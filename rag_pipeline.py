import time
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
        Streaming RAG Pipeline Generator with Live Stage Events & Performance Timing.
        Yields dictionaries with step info:
        - {"type": "status", "stage": "query_received", "message": "✓ Query received"}
        - {"type": "status", "stage": "searching", "message": "⟳ Searching your documents..."}
        - {"type": "status", "stage": "retrieving", "message": "⟳ Retrieving relevant context..."}
        - {"type": "sources", "sources": [...], "chunks": [...]}
        - {"type": "status", "stage": "generating", "message": "⟳ Generating answer..."}
        - {"type": "token", "delta": "..."}
        - {"type": "complete", "elapsed_sec": 2.4}
        """
        start_time = time.perf_counter()
        
        # Stage 1: Query Received
        yield {"type": "status", "stage": "query_received", "message": "✓ Query received"}
        time.sleep(0.05)
        
        # Stage 2: Searching Documents
        yield {"type": "status", "stage": "searching", "message": "⟳ Searching your documents..."}
        
        retrieved_chunks = self.retrieval_engine.retrieve(
            question, k=k, provider=provider, model_name=model_name, user_id=user_id
        )
        
        # Stage 3: Retrieving Relevant Context
        yield {"type": "status", "stage": "retrieving", "message": "⟳ Retrieving relevant context..."}
        
        formatted_sources = []
        for c in retrieved_chunks:
            fname = c["filename"]
            pnum = c.get("page_number")
            src_label = f"{fname} · Page {pnum}" if pnum else fname
            if src_label not in formatted_sources:
                formatted_sources.append(src_label)
                
        yield {
            "type": "sources",
            "sources": formatted_sources,
            "chunks": retrieved_chunks
        }
        
        # Stage 4: Generating Answer
        yield {"type": "status", "stage": "generating", "message": "⟳ Generating answer..."}
        
        if not retrieved_chunks:
            yield {"type": "token", "delta": "I couldn't find enough information in your uploaded documents to answer this question."}
            elapsed = round(time.perf_counter() - start_time, 1)
            yield {"type": "complete", "elapsed_sec": elapsed}
            return

        stream_gen = generate_answer_stream(
            question, retrieved_chunks, api_key=api_key, provider=provider, model_name=model_name
        )
        
        for delta in stream_gen:
            yield {"type": "token", "delta": delta}
            
        elapsed = round(time.perf_counter() - start_time, 1)
        yield {"type": "complete", "elapsed_sec": elapsed}

    def ask(self, question, k=5, provider="gemini", model_name="gemini-2.0-flash", user_id="user_default", api_key=None):
        """Synchronous RAG pipeline fallback."""
        chunks = []
        sources = []
        token_deltas = []
        elapsed = 0.0
        
        for event in self.ask_stream(question, k=k, provider=provider, model_name=model_name, user_id=user_id, api_key=api_key):
            if event["type"] == "sources":
                sources = event["sources"]
                chunks = event["chunks"]
            elif event["type"] == "token":
                token_deltas.append(event["delta"])
            elif event["type"] == "complete":
                elapsed = event["elapsed_sec"]
                
        return {
            "question": question,
            "answer": "".join(token_deltas),
            "sources": sources,
            "retrieved_chunks": chunks,
            "elapsed_sec": elapsed
        }
