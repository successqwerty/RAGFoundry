from sentence_transformers import SentenceTransformer
from ingestion import load_documents
from chunking import chunk_text

# Load embedding model locally (384-dimensional vectors)
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text):
    """Embeds a single string (e.g. user question)."""
    return model.encode(text)

def get_embeddings_batch(texts):
    """Embeds a list of strings/chunks (e.g. document chunks)."""
    return model.encode(texts)

if __name__ == "__main__":
    # 1. Load document
    docs = load_documents("data")
    full_text = docs[0]["content"]
    
    # 2. Split document into chunks
    chunks = chunk_text(full_text, chunk_size=200, overlap=40)
    print(f"Total Chunks created: {len(chunks)}")
    
    # 3. Convert ALL chunks into vector embeddings!
    vectors = get_embeddings_batch(chunks)
    
    print(f"\nVectors matrix shape: {vectors.shape}")
    print(f"-> Generated {vectors.shape[0]} vectors.")
    print(f"-> Each vector has {vectors.shape[1]} numbers/dimensions.")
    
    print("\n--- Vector for Chunk 1 (First 5 values) ---")
    print(vectors[0][:5])
