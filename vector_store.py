import os
import json
import faiss
import numpy as np
from embeddings import get_embedding, get_embeddings_batch

INDEX_FILE = os.path.join("data", "index.faiss")
META_FILE = os.path.join("data", "vector_meta.json")

class PersistentVectorStore:
    def __init__(self, index_file=INDEX_FILE, meta_file=META_FILE):
        self.index_file = index_file
        self.meta_file = meta_file
        self.metadata = []
        self.index = None
        self.dimension = 384
        self.load()

    def load(self):
        """Loads FAISS index and metadata from disk if available."""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        
        if os.path.exists(self.index_file) and os.path.exists(self.meta_file):
            try:
                self.index = faiss.read_index(self.index_file)
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                self.dimension = self.index.d
                return
            except Exception as e:
                print(f"Error loading vector store from disk: {e}")
                
        # Initialize new FAISS L2 Flat Index
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []

    def save(self):
        """Persists FAISS index and metadata to disk."""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, self.index_file)
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def add_chunks(self, chunk_objects):
        """
        Incrementally adds new chunk objects to FAISS index and metadata store.
        Deduplicates chunks by chunk_id.
        """
        if not chunk_objects:
            return
            
        existing_ids = set(m.get("chunk_id") for m in self.metadata)
        new_chunks = [c for c in chunk_objects if c.get("chunk_id") not in existing_ids]
        
        if not new_chunks:
            return
            
        texts = [c["text"] for c in new_chunks]
        embeddings = get_embeddings_batch(texts)
        embeddings_np = np.array(embeddings).astype("float32")
        
        self.index.add(embeddings_np)
        
        for c in new_chunks:
            self.metadata.append(c)
            
        self.save()

    def search(self, query_text, k=5, user_id=None):
        """
        Searches FAISS index for top-K matching chunks, filtered by user_id if specified.
        """
        if self.index is None or self.index.ntotal == 0:
            return [], []
            
        query_vec = get_embedding(query_text)
        query_np = np.array([query_vec]).astype("float32")
        
        # Retrieve more candidates if user_id filtering is required
        search_k = min(k * 4 if user_id else k, self.index.ntotal)
        distances, indices = self.index.search(query_np, search_k)
        
        res_distances = []
        res_chunks = []
        
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            
            # User level filtering: allow if user matches or if meta user is public default
            if user_id and meta.get("user_id") not in (user_id, "user_default"):
                continue
                
            res_distances.append(float(dist))
            res_chunks.append(meta)
            
            if len(res_chunks) >= k:
                break
                
        return res_distances, res_chunks

    def clear(self):
        """Clears all vectors and metadata."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        if os.path.exists(self.meta_file):
            os.remove(self.meta_file)

if __name__ == "__main__":
    store = PersistentVectorStore()
    print(f"Loaded store with {store.index.ntotal} vectors.")
