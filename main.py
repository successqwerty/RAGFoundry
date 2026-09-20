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
    stream: Optional[bool] = Field(default=True, description="Enable real-time token streaming via SSE")

class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    retrieved_chunks: List[Dict[str, Any]]
    elapsed_sec: float
    precision: Optional[float] = 0.0
    accuracy: Optional[float] = 0.0
    precision_pct: Optional[str] = "0.0%"
    accuracy_pct: Optional[str] = "0.0%"
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

from fastapi.responses import FileResponse, StreamingResponse
import json

@app.get("/", include_in_schema=False)
def root_redirect():
    return FileResponse("frontend/index.html")

@app.post("/ask", tags=["RAG"])
def ask_question(payload: AskRequest):
    """
    Main RAG Endpoint supporting real-time token streaming via Server-Sent Events (SSE)
    as well as traditional JSON responses when stream=False.
    """
    if not payload.question or not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question field cannot be empty."
        )

    q_text = payload.question.strip()

    # If non-streaming is explicitly requested: run synchronous pipeline
    if payload.stream is False:
        # Guard: Validate indexed documents count BEFORE retrieval or LLM execution
        if not pipeline.has_documents(user_id=payload.user_id):
            return AskResponse(
                question=q_text,
                answer="Please upload a document first. Upload a PDF, DOCX, or TXT file to start asking questions.",
                sources=[],
                retrieved_chunks=[],
                elapsed_sec=0.0,
                precision=0.0,
                accuracy=0.0,
                precision_pct="0.0%",
                accuracy_pct="0.0%",
                conversation_id=payload.conversation_id
            )
        
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
            chunks=result.get("retrieved_chunks", []),
            precision=result.get("precision", 0.0),
            accuracy=result.get("accuracy", 0.0),
            precision_pct=result.get("precision_pct", "0.0%"),
            accuracy_pct=result.get("accuracy_pct", "0.0%"),
            elapsed_sec=result.get("elapsed_sec", 0.0)
        )

        return AskResponse(
            question=result["question"],
            answer=result["answer"],
            sources=result.get("sources", []),
            retrieved_chunks=result.get("retrieved_chunks", []),
            elapsed_sec=result.get("elapsed_sec", 0.0),
            precision=result.get("precision", 0.0),
            accuracy=result.get("accuracy", 0.0),
            precision_pct=result.get("precision_pct", "0.0%"),
            accuracy_pct=result.get("accuracy_pct", "0.0%"),
            conversation_id=conv_id
        )

    # STREAMING MODE (Default: payload.stream is True)
    def event_stream_generator():
        # Guard: Validate indexed documents count BEFORE retrieval or LLM execution
        if not pipeline.has_documents(user_id=payload.user_id):
            no_doc_msg = "Please upload a document first. Upload a PDF, DOCX, or TXT file to start asking questions."
            yield f"data: {json.dumps({'type': 'no_documents', 'message': no_doc_msg})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'delta': no_doc_msg})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'elapsed_sec': 0.0, 'precision': 0.0, 'accuracy': 0.0, 'precision_pct': '0.0%', 'accuracy_pct': '0.0%', 'conversation_id': payload.conversation_id})}\n\n"
            return

        # 1. Resolve or Create Conversation
        conv_id = payload.conversation_id
        conv_title = None
        if conv_id:
            existing = db_manager.get_conversation(conv_id)
            if not existing:
                conv_title = db_manager.generate_conversation_title(q_text)
                conv_id = db_manager.create_conversation(user_id=payload.user_id, title=conv_title)
        else:
            conv_title = db_manager.generate_conversation_title(q_text)
            conv_id = db_manager.create_conversation(user_id=payload.user_id, title=conv_title)

        # 2. Save NEW user message to database once
        db_manager.save_message(conv_id, "user", q_text)

        # Emit conversation metadata early
        yield f"data: {json.dumps({'type': 'conversation_meta', 'conversation_id': conv_id, 'title': conv_title})}\n\n"

        accumulated_tokens = []
        retrieved_sources = []
        retrieved_chunks = []

        try:
            for event in pipeline.ask_stream(
                question=q_text,
                k=payload.k,
                provider=payload.provider,
                model_name=payload.model_name,
                user_id=payload.user_id,
                api_key=payload.api_key
            ):
                if event["type"] == "sources":
                    retrieved_sources = event.get("sources", [])
                    retrieved_chunks = event.get("chunks", [])
                elif event["type"] == "token":
                    accumulated_tokens.append(event.get("delta", ""))
                elif event["type"] == "complete":
                    event["conversation_id"] = conv_id
                    
                    # 3. Save assistant answer to the SAME conversation in database ONCE
                    from generation import clean_plain_text
                    final_raw = "".join(accumulated_tokens)
                    clean_ans = clean_plain_text(final_raw)
                    
                    db_manager.save_message(
                        conv_id,
                        "assistant",
                        clean_ans,
                        sources=retrieved_sources,
                        chunks=retrieved_chunks,
                        precision=event.get("precision", 0.0),
                        accuracy=event.get("accuracy", 0.0),
                        precision_pct=event.get("precision_pct", "0.0%"),
                        accuracy_pct=event.get("accuracy_pct", "0.0%"),
                        elapsed_sec=event.get("elapsed_sec", 0.0)
                    )

                yield f"data: {json.dumps(event)}\n\n"

        except Exception as err:
            err_msg = f"Error during generation: {str(err)}"
            yield f"data: {json.dumps({'type': 'error', 'message': err_msg})}\n\n"

    return StreamingResponse(
        event_stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/documents", tags=["Workspace"])
def get_workspace_documents():
    """Returns list of indexed documents in the data folder."""
    docs = []
    if os.path.exists(data_folder):
        for f in sorted(os.listdir(data_folder)):
            if f.lower().endswith(('.pdf', '.docx', '.txt', '.md', '.csv', '.xlsx', '.pptx', '.html')) and not f.startswith('.') and f != "vector_meta.json":
                file_path = os.path.join(data_folder, f)
                if os.path.isfile(file_path):
                    size_kb = round(os.path.getsize(file_path) / 1024.0, 1)
                    docs.append({
                        "filename": f,
                        "size_kb": size_kb,
                        "status": "Indexed"
                    })
    # If no documents exist, ensure vector store and cache are fully cleared
    if len(docs) == 0:
        pipeline.retrieval_engine.store.clear()
        clear_suggestions_cache()
    return {"documents": docs, "count": len(docs)}

@app.delete("/documents", tags=["Workspace"])
def clear_all_workspace_documents():
    """Deletes all indexed documents from workspace and clears vector index."""
    if os.path.exists(data_folder):
        for existing_file in os.listdir(data_folder):
            file_p = os.path.join(data_folder, existing_file)
            if os.path.isfile(file_p) and not existing_file.endswith(('.faiss', '.json', '.db')):
                try:
                    os.remove(file_p)
                except Exception:
                    pass
    pipeline.rebuild_index()
    clear_suggestions_cache()
    return {"status": "success", "message": "All documents cleared."}

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
    app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend_ui")
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend_root")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
