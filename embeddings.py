import functools
from sentence_transformers import SentenceTransformer

# Singleton cached transformer model
_model_instance = None

def get_embedding_model():
    global _model_instance
    if _model_instance is None:
        _model_instance = SentenceTransformer("all-MiniLM-L6-v2")
    return _model_instance

def get_embedding(text):
    """Embeds a single string (e.g. user question)."""
    model = get_embedding_model()
    return model.encode(text)

def get_embeddings_batch(texts):
    """Embeds a list of strings/chunks (e.g. document chunks)."""
    if not texts:
        return []
    model = get_embedding_model()
    return model.encode(texts)

if __name__ == "__main__":
    vec = get_embedding("Test question")
    print(f"Embedding dimensions: {len(vec)}")
