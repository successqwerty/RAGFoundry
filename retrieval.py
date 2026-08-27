from ingestion import load_documents
from chunking import chunk_text
from embeddings import get_embedding, get_embeddings_batch
from vector_store import create_faiss_index, search_faiss_index
from generation import rewrite_query
from sentence_transformers import CrossEncoder

# Load lightweight, fast Cross-Encoder Reranker
try:
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
except Exception:
    reranker = None

class RetrievalEngine:
    def __init__(self, data_folder="data"):
        self.docs = load_documents(data_folder)
        
        self.chunks = []
        self.metadata = []
        
        for doc in self.docs:
            doc_chunks = chunk_text(doc["content"], chunk_size=500, overlap=80)
            for chunk in doc_chunks:
                self.chunks.append(chunk)
                self.metadata.append({"filename": doc["filename"]})
                
        self.embeddings = get_embeddings_batch(self.chunks)
        self.index = create_faiss_index(self.embeddings)

    def retrieve(self, query, k=10, use_query_rewriting=True, provider="gemini", model_name=None):
        """
        Production Two-Stage Retrieval:
        1. Bi-Encoder FAISS Vector Search: Retrieves Top K=10 candidates.
        2. Cross-Encoder Reranking: Deep attention re-scoring that moves the exact target chunk to RANK 1!
        """
        search_query = query
        if use_query_rewriting:
            search_query = rewrite_query(query, provider=provider, model_name=model_name)
            print(f"\n[Query Rewriter] Original Query: '{query}'")
            print(f"[Query Rewriter] Optimized Search Vector Query: '{search_query}'")
            
        query_vec = get_embedding(search_query)
        distances, indices = search_faiss_index(self.index, query_vec, k=min(k, len(self.chunks)))
        
        candidates = []
        seen_indices = set()
        
        for dist, idx in zip(distances, indices):
            if idx in seen_indices:
                continue
            seen_indices.add(idx)
            
            full_text = self.chunks[idx]
            if idx + 1 < len(self.chunks) and self.metadata[idx]["filename"] == self.metadata[idx+1]["filename"]:
                full_text += "\n" + self.chunks[idx+1]
                
            candidates.append({
                "chunk_index": int(idx),
                "text": full_text,
                "filename": self.metadata[idx]["filename"],
                "distance_score": float(dist)
            })
            
        # Two-Stage Reranking using Cross-Encoder
        if reranker and candidates:
            pairs = [[query, c["text"]] for c in candidates]
            scores = reranker.predict(pairs)
            for i, score in enumerate(scores):
                candidates[i]["rerank_score"] = float(score)
            # Sort by Reranker Relevance Score (highest relevance first!)
            candidates = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
            
        return candidates

if __name__ == "__main__":
    engine = RetrievalEngine("data")
    results = engine.retrieve("what is the first project done by gayathri", k=2)
    for r in results:
        print(f"\nSnippet: {repr(r['text'][:120])}")
