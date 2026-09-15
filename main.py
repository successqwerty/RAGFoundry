import os
import shutil
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import existing RAG Pipeline & DB Manager
from rag_pipeline import RAGPipeline
import db_manager
from suggested_questions import generate_suggested_questions, clear_suggestions_cache

load_dotenv(override=True)

# Initialize Database
db_manager.init_db()

# 1. Initialize FastAPI Application
app = FastAPI(
    title="RAGFoundry API",
    description="FastAPI Backend for RAGFoundry SaaS Dashboard",
    version="2.0.0"
)

# 2. Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Instantiate Master RAG Pipeline
data_folder = os.environ.get("DATA_FOLDER", "data")
pipeline = RAGPipeline(data_folder=data_folder)

# Auto-sync on startup
try:
    pipeline.sync()
    print("[RAGFoundry API] Successfully synced RAGPipeline vector store on startup.")
except Exception as e:
    print(f"[RAGFoundry API Warning] Could not sync vector store on startup: {e}")

# 4. Pydantic Models
class AskRequest(BaseModel):
    question: str = Field(..., example="What is Human Resource Management?")
    conversation_id: Optional[str] = Field(default=None, description="Existing conversation ID to append message to")
    k: Optional[int] = Field(default=5, ge=1, le=20)
    provider: Optional[str] = Field(default="gemini")
    model_name: Optional[str] = Field(default="gemini-3.6-flash")
    user_id: Optional[str] = Field(default="user_default")
    api_key: Optional[str] = Field(default=None, description="Optional custom user Gemini API key (BYOK)")

class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    retrieved_chunks: List[Dict[str, Any]]
    elapsed_sec: float
    conversation_id: Optional[str] = None

class SuggestedQuestionsRequest(BaseModel):
    provider: Optional[str] = Field(default="gemini")
    model_name: Optional[str] = Field(default="gemini-3.6-flash")
    api_key: Optional[str] = Field(default=None)
    force_refresh: Optional[bool] = Field(default=False)

class HealthResponse(BaseModel):
    status: str
    message: str
    documents_folder: str

# 5. API Endpoints

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Returns backend API status."""
    return HealthResponse(
        status="ok",
        message="RAGFoundry Backend API is online and ready.",
        documents_folder=os.path.abspath(pipeline.data_folder)
    )

from fastapi.responses import FileResponse

@app.get("/", include_in_schema=False)
def root_redirect():
    return FileResponse("frontend/index.html")

@app.post("/ask", response_model=AskResponse, tags=["RAG"])
def ask_question(payload: AskRequest):
    """
    Main RAG Endpoint for Multi-Turn Conversations.
    Appends new question & answer to existing conversation if conversation_id is supplied,
    or creates a new conversation if omitted.
    Only runs RAG / LLM for the NEW user question.
    """
    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question field cannot be empty."
        )

    try:
        q_text = payload.question.strip()
        
        # 1. Resolve or Create Conversation
        conv_id = payload.conversation_id
        if conv_id:
            existing = db_manager.get_conversation(conv_id)
            if not existing:
                conv_title = db_manager.generate_conversation_title(q_text)
                conv_id = db_manager.create_conversation(user_id=payload.user_id, title=conv_title)
        else:
            conv_title = db_manager.generate_conversation_title(q_text)
            conv_id = db_manager.create_conversation(user_id=payload.user_id, title=conv_title)

        # 2. Save NEW user message to database
        db_manager.save_message(conv_id, "user", q_text)

        # 3. Call RAG pipeline ONLY for the new question
        result = pipeline.ask(
            question=q_text,
            k=payload.k,
            provider=payload.provider,
            model_name=payload.model_name,
            user_id=payload.user_id,
            api_key=payload.api_key
        )

        # 4. Save assistant answer to the SAME conversation in database
        db_manager.save_message(
            conv_id, 
            "assistant", 
            result["answer"],
            sources=result.get("sources", []),
            chunks=result.get("retrieved_chunks", [])
        )

        return AskResponse(
            question=result["question"],
            answer=result["answer"],
            sources=result.get("sources", []),
            retrieved_chunks=result.get("retrieved_chunks", []),
            elapsed_sec=result.get("elapsed_sec", 0.0),
            conversation_id=conv_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing RAG pipeline: {str(e)}"
        )

@app.get("/documents", tags=["Workspace"])
def get_workspace_documents():
    """Returns list of indexed documents in the data folder."""
    docs = []
    if os.path.exists(data_folder):
        for f in os.listdir(data_folder):
            if f.lower().endswith(('.pdf', '.docx', '.txt')) and not f.startswith('.') and f != "vector_meta.json":
                file_path = os.path.join(data_folder, f)
                size_kb = round(os.path.getsize(file_path) / 1024.0, 1)
                docs.append({
                    "filename": f,
                    "size_kb": size_kb,
                    "status": "Indexed"
                })
    return {"documents": docs, "count": len(docs)}

@app.post("/upload", tags=["Workspace"])
async def upload_documents(
    file: UploadFile = File(...), 
    clear_old: bool = Form(False)
):
    """Uploads document to data folder and triggers vector index update."""
    try:
        os.makedirs(data_folder, exist_ok=True)

        if clear_old:
            for existing_file in os.listdir(data_folder):
                file_p = os.path.join(data_folder, existing_file)
                if os.path.isfile(file_p) and not existing_file.endswith(('.faiss', '.json', '.db')):
                    os.remove(file_p)

        target_path = os.path.join(data_folder, file.filename)
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Re-index pipeline
        pipeline.rebuild_index()
        clear_suggestions_cache()

        return {
            "status": "success",
            "message": f"Successfully uploaded and indexed '{file.filename}'.",
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@app.delete("/documents/{filename}", tags=["Workspace"])
def delete_workspace_document(filename: str):
    """Deletes an indexed document from workspace, rebuilds index, and invalidates suggestions."""
    file_path = os.path.join(data_folder, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found.")

    try:
        os.remove(file_path)
        pipeline.rebuild_index()
        clear_suggestions_cache()
        return {
            "status": "success",
            "message": f"Document '{filename}' deleted and vector index rebuilt."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@app.get("/suggested-questions", tags=["RAG"])
def get_suggested_questions(
    provider: Optional[str] = "gemini",
    model_name: Optional[str] = "gemini-3.6-flash",
    api_key: Optional[str] = None,
    force_refresh: Optional[bool] = False
):
    """
    Generates dynamic, document-aware suggested questions based ONLY on
    currently indexed documents in the Knowledge Base.
    """
    return generate_suggested_questions(
        vector_store=pipeline.retrieval_engine.store,
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        force_refresh=force_refresh
    )

@app.post("/suggested-questions", tags=["RAG"])
def post_suggested_questions(payload: SuggestedQuestionsRequest):
    """POST variant for dynamic document-aware suggested questions."""
    return generate_suggested_questions(
        vector_store=pipeline.retrieval_engine.store,
        provider=payload.provider,
        model_name=payload.model_name,
        api_key=payload.api_key,
        force_refresh=payload.force_refresh
    )

@app.get("/history", tags=["History"])
def get_chat_history(user_id: str = "user_default"):
    """Returns conversations grouped by TODAY, YESTERDAY, PREVIOUS 7 DAYS, OLDER."""
    grouped = db_manager.get_user_conversations_grouped(user_id=user_id)
    return {"history": grouped}

@app.get("/history/{conv_id}", tags=["History"])
def get_conversation_details(conv_id: str):
    """Returns full messages for a specific conversation."""
    conv = db_manager.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv

@app.delete("/history/{conv_id}", tags=["History"])
def delete_chat_conversation(conv_id: str):
    """Deletes a conversation by ID."""
    success = db_manager.delete_conversation(conv_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found or could not be deleted.")
    return {"status": "success", "message": "Conversation deleted."}

@app.get("/conversations", tags=["Conversations"])
def get_all_conversations(user_id: str = "user_default"):
    """
    Returns list of all saved conversations with summaries.
    Conceptual ChatGPT-style conversation list endpoint.
    """
    conversations = db_manager.get_all_conversations(user_id=user_id)
    return conversations

@app.get("/conversations/{conv_id}", tags=["Conversations"])
def get_single_conversation(conv_id: str):
    """
    Returns the COMPLETE saved conversation without triggering RAG, FAISS, or LLM.
    Pure database read.
    """
    conv = db_manager.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv

@app.delete("/conversations/{conv_id}", tags=["Conversations"])
def delete_single_conversation(conv_id: str):
    """Deletes a conversation and all associated messages."""
    success = db_manager.delete_conversation(conv_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found or could not be deleted.")
    return {"status": "success", "message": f"Conversation {conv_id} deleted."}

@app.get("/ai-engine", tags=["System"])
def get_ai_engine_info():
    """Returns current AI engine provider and status."""
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    return {
        "provider": "ollama" if not gemini_key else "gemini",
        "model_name": ollama_model if not gemini_key else "gemini-3.6-flash",
        "ollama_available": True,
        "gemini_configured": bool(gemini_key)
    }

@app.post("/reindex", tags=["RAG"])
def reindex_documents(user_id: str = "user_default"):
    """Forces a complete re-indexing of documents."""
    try:
        pipeline.rebuild_index(user_id=user_id)
        clear_suggestions_cache()
        return {"status": "success", "message": "Vector store index successfully rebuilt."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Re-indexing failed: {str(e)}"
        )

# Mount static frontend
if os.path.exists("frontend"):
    app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
