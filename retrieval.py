from ingestion import load_documents
from chunking import chunk_text
from embeddings import get_embedding, get_embeddings_batch
from vector_store import create_faiss_index, search_faiss_index
from generation import rewrite_query

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

    def retrieve(self, query, k=3, use_query_rewriting=True):
        """
        Retrieves top-k chunks, automatically applying Query Rewriting.
        """
        search_query = query
        if use_query_rewriting:
            search_query = rewrite_query(query)
            print(f"\n[Query Rewriter] Original Query: '{query}'")
            print(f"[Query Rewriter] Optimized Search Vector Query: '{search_query}'")
            
        query_vec = get_embedding(search_query)
        distances, indices = search_faiss_index(self.index, query_vec, k=k)
        
        results = []
        for dist, idx in zip(distances, indices):
            results.append({
                "chunk_index": int(idx),
                "text": self.chunks[idx],
                "filename": self.metadata[idx]["filename"],
                "distance_score": float(dist)
            })
            
        return results

if __name__ == "__main__":
    engine = RetrievalEngine("data")
    results = engine.retrieve("what is the first project done by gayathri", k=2)
    for r in results:
        print(f"\nSnippet: {repr(r['text'][:120])}")
