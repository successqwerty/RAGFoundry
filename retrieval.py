from ingestion import load_documents
from chunking import chunk_document
from vector_store import PersistentVectorStore
from generation import rewrite_query
from sentence_transformers import CrossEncoder

_reranker_instance = None

def get_reranker():
    global _reranker_instance
    if _reranker_instance is None:
        try:
            _reranker_instance = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", local_files_only=True)
        except Exception:
            try:
                _reranker_instance = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            except Exception as e:
                print(f"Warning: Reranker failed to initialize: {e}")
                _reranker_instance = None
    return _reranker_instance

class RetrievalEngine:
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        self.store = PersistentVectorStore()
        self.sync_documents()

    def get_indexed_document_count(self, user_id="user_default") -> int:
        """Returns the number of currently active, supported documents on disk."""
        import os
        if not os.path.exists(self.data_folder):
            if len(self.store.metadata) > 0 or (self.store.index and self.store.index.ntotal > 0):
                self.store.clear()
            return 0
        valid_exts = ('.pdf', '.docx', '.doc', '.txt', '.md', '.csv', '.xlsx', '.pptx', '.html')
        doc_files = [
            f for f in os.listdir(self.data_folder)
            if f.lower().endswith(valid_exts) and not f.startswith('.') and f != "vector_meta.json" and os.path.isfile(os.path.join(self.data_folder, f))
        ]
        if not doc_files:
            # If no document files exist on disk, clear any stale index/metadata immediately
            if len(self.store.metadata) > 0 or (self.store.index and self.store.index.ntotal > 0):
                self.store.clear()
            return 0
        return len(doc_files)

    def has_indexed_documents(self, user_id="user_default") -> bool:
        return self.get_indexed_document_count(user_id=user_id) > 0

    def sync_documents(self, user_id="user_default"):
        """
        Synchronizes vector store with current documents in data_folder:
        1. Identifies active files on disk.
        2. If active files is empty, clears store completely (prevents stale vectors).
        3. If files were removed or changed, rebuilds store so stale chunks are pruned.
        4. Indexes any new documents.
        """
        docs = load_documents(self.data_folder, user_id=user_id)
        if not docs:
            self.store.clear()
            return

        current_hashes = {d["file_hash"] for d in docs}
        current_filenames = {d["filename"] for d in docs}

        stored_hashes = {m.get("file_hash") for m in self.store.metadata if m.get("file_hash")}
        stored_filenames = {m.get("filename") for m in self.store.metadata if m.get("filename")}

        # If any stored file is no longer in data_folder or hash changed, rebuild clean
        if (stored_filenames - current_filenames) or (stored_hashes - current_hashes):
            self.store.clear()
            for doc in docs:
                all_chunks = chunk_document(doc, chunk_size=500, overlap=80)
                self.store.add_chunks(all_chunks)
            return

        for doc in docs:
            all_chunks = chunk_document(doc, chunk_size=500, overlap=80)
            self.store.add_chunks(all_chunks)

    def sync(self, user_id="user_default"):
        """Alias for sync_documents."""
        self.sync_documents(user_id=user_id)

    def rebuild_index(self, user_id="user_default"):
        """Clears existing store and re-indexes all workspace documents from scratch."""
        self.store.clear()
        self.sync_documents(user_id=user_id)

    def retrieve(self, query, k=5, use_query_rewriting=True, provider="gemini", model_name=None, user_id=None):
        """
        Two-Stage Production Retrieval:
        1. Bi-Encoder FAISS Search: Retrieves top candidates.
        2. Cross-Encoder Reranking: Deep attention relevance rescoring.
        """
        # Guard: If no documents are currently indexed, return empty immediately.
        # DO NOT call rewrite_query (which calls Gemini/Ollama).
        if not self.has_indexed_documents(user_id=user_id or "user_default"):
            return []

        search_query = query
        if use_query_rewriting:
            search_query = rewrite_query(query, provider=provider, model_name=model_name)
            
        distances, candidate_chunks = self.store.search(search_query, k=k*2, user_id=user_id)
        
        if not candidate_chunks:
            return []
            
        for i, c in enumerate(candidate_chunks):
            c["distance_score"] = float(distances[i])
            
        reranker = get_reranker()
        if reranker and candidate_chunks:
            try:
                pairs = [[query, c["text"]] for c in candidate_chunks]
                scores = reranker.predict(pairs)
                for i, score in enumerate(scores):
                    candidate_chunks[i]["rerank_score"] = float(score)
                candidate_chunks = sorted(candidate_chunks, key=lambda x: x["rerank_score"], reverse=True)
            except Exception as e:
                print(f"Reranking error: {e}")
                
        return candidate_chunks[:k]

if __name__ == "__main__":
    engine = RetrievalEngine("data")
    res = engine.retrieve("test query", k=3)
    print(f"Retrieved {len(res)} chunk(s).")
