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

    def sync_documents(self, user_id="user_default"):
        """
        Indexes new documents in the data folder into persistent vector store without duplicate re-embeddings.
        """
        docs = load_documents(self.data_folder, user_id=user_id)
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
