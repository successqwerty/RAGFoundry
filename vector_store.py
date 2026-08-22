import faiss
import numpy as np
from ingestion import load_documents
from chunking import chunk_text
from embeddings import get_embedding, get_embeddings_batch

def create_faiss_index(embeddings):
    """
    Creates a FAISS index and stores vectors inside it.
    """
    # Get vector dimensions (e.g. 384)
    dimension = embeddings.shape[1]
    
    # Create an L2 Euclidean Distance index
    index = faiss.IndexFlatL2(dimension)
    
    # Convert embeddings to float32 numpy array (FAISS requires float32)
    embeddings_np = np.array(embeddings).astype('float32')
    
    # Add vectors to index
    index.add(embeddings_np)
    
    return index

def search_faiss_index(index, query_vector, k=3):
    """
    Searches the FAISS index for the top-k closest vectors to query_vector.
    """
    # Ensure query vector is 2D float32 numpy array
    query_np = np.array([query_vector]).astype('float32')
    
    # Perform similarity search (returns distances and indices of top-k matches)
    distances, indices = index.search(query_np, k)
    
    return distances[0], indices[0]

if __name__ == "__main__":
    # 1. Load and chunk handbook
    docs = load_documents("data")
    full_text = docs[0]["content"]
    chunks = chunk_text(full_text, chunk_size=250, overlap=50)
    
    # 2. Embed all chunks
    chunk_embeddings = get_embeddings_batch(chunks)
    
    # 3. Store in FAISS Index
    index = create_faiss_index(chunk_embeddings)
    print(f"Stored {index.ntotal} vectors in FAISS index.")
    
    # 4. User Question
    user_query = "How many paid vacation days do employees get?"
    print(f"\nUser Question: '{user_query}'")
    
    # 5. Embed Question & Search FAISS
    query_vec = get_embedding(user_query)
    distances, top_indices = search_faiss_index(index, query_vec, k=3)
    
    # 6. Display Retrieved Chunks
    print("\n--- TOP RETRIEVED CHUNKS ---")
    for rank, (dist, idx) in enumerate(zip(distances, top_indices)):
        print(f"\n[Rank {rank+1}] Chunk Index #{idx} (Distance Score: {dist:.4f}):")
        print(repr(chunks[idx]))
