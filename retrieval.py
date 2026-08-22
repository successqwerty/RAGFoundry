from ingestion import load_documents
from chunking import chunk_text
from embeddings import get_embedding, get_embeddings_batch
from vector_store import create_faiss_index, search_faiss_index

class RetrievalEngine:
    def __init__(self, data_folder="data"):
        # 1. Load documents
        self.docs = load_documents(data_folder)
        
        # 2. Chunk text and preserve metadata for each chunk
        self.chunks = []
        self.metadata = []
        
        for doc in self.docs:
            doc_chunks = chunk_text(doc["content"], chunk_size=250, overlap=50)
            for chunk in doc_chunks:
                self.chunks.append(chunk)
                self.metadata.append({"filename": doc["filename"]})
                
        # 3. Generate embeddings for all chunks
        self.embeddings = get_embeddings_batch(self.chunks)
        
        # 4. Build FAISS index
        self.index = create_faiss_index(self.embeddings)

    def retrieve(self, query, k=3):
        """
        Retrieves the top-k most relevant text chunks for a query.
        """
        # Embed the user question
        query_vec = get_embedding(query)
        
        # Search FAISS index
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
    
    test_queries = [
        "How many vacation days do I get?",
        "What is the daily meal stipend when traveling?",
        "What is the company stock option equity policy?",
        "How much money do I get?"
    ]
    
    for q in test_queries:
        print(f"\n=======================================================")
        print(f"QUERY: '{q}'")
        print(f"=======================================================")
        results = engine.retrieve(q, k=2)
        for rank, res in enumerate(results):
            print(f"\n  [Rank {rank+1}] Distance: {res['distance_score']:.4f} | File: {res['filename']}")
            print(f"  Snippet: {repr(res['text'][:120])}...")
