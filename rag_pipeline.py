from retrieval import RetrievalEngine
from generation import generate_answer_stream, generate_answer

class RAGPipeline:
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        self.retrieval_engine = RetrievalEngine(data_folder)

    def sync(self, user_id="user_default"):
        """Syncs workspace documents into persistent vector store."""
        self.retrieval_engine.sync_documents(user_id=user_id)

    def sync_documents(self, user_id="user_default"):
        """Alias for sync."""
        self.sync(user_id=user_id)

    def index_documents(self, user_id="user_default"):
        """Alias for sync."""
        self.sync(user_id=user_id)

    def rebuild_index(self, user_id="user_default"):
        """Rebuilds vector store index from scratch."""
        self.retrieval_engine.rebuild_index(user_id=user_id)

    def ask_stream(self, question, k=5, provider="gemini", model_name="gemini-2.0-flash", user_id="user_default", api_key=None):
        """
        Streaming RAG Pipeline Generator.
        Yields dictionaries with step info:
        - {"type": "status", "message": "..."}
        - {"type": "sources", "sources": [...], "chunks": [...]}
        - {"type": "token", "delta": "..."}
        """
        yield {"type": "status", "message": "Searching knowledge base & retrieving relevant context..."}
        
        retrieved_chunks = self.retrieval_engine.retrieve(
            question, k=k, provider=provider, model_name=model_name, user_id=user_id
        )
        
        formatted_sources = []
        for c in retrieved_chunks:
            fname = c["filename"]
            pnum = c.get("page_number")
            src_label = f"{fname} (Page {pnum})" if pnum else fname
            if src_label not in formatted_sources:
                formatted_sources.append(src_label)
                
        yield {
            "type": "sources",
            "sources": formatted_sources,
            "chunks": retrieved_chunks
        }
        
        yield {"type": "status", "message": "Generating answer grounded in documents..."}
        
        if not retrieved_chunks:
            yield {"type": "token", "delta": "I could not find this information in the uploaded documents."}
            return

        stream_gen = generate_answer_stream(
            question, retrieved_chunks, api_key=api_key, provider=provider, model_name=model_name
        )
        
        for delta in stream_gen:
            yield {"type": "token", "delta": delta}

    def ask(self, question, k=5, provider="gemini", model_name="gemini-2.0-flash", user_id="user_default", api_key=None):
        """Synchronous RAG pipeline fallback."""
        chunks = []
        sources = []
        token_deltas = []
        
        for event in self.ask_stream(question, k=k, provider=provider, model_name=model_name, user_id=user_id, api_key=api_key):
            if event["type"] == "sources":
                sources = event["sources"]
                chunks = event["chunks"]
            elif event["type"] == "token":
                token_deltas.append(event["delta"])
                
        return {
            "question": question,
            "answer": "".join(token_deltas),
            "sources": sources,
            "retrieved_chunks": chunks
        }
