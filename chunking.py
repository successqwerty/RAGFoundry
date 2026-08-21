from ingestion import load_documents

def chunk_text(text, chunk_size=150, overlap=30):
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # Move the sliding window forward by (chunk_size - overlap)
        start += (chunk_size - overlap)
        
    return chunks

if __name__ == "__main__":
    docs = load_documents("data")
    sample_text = docs[0]["content"]
    
    print(f"--- Original Text Length: {len(sample_text)} characters ---")
    
    chunks = chunk_text(sample_text, chunk_size=150, overlap=30)
    
    print(f"\n--- Generated {len(chunks)} Chunks ---")
    for i, c in enumerate(chunks):
        print(f"\n[CHUNK {i+1}] (Length: {len(c)} chars):")
        print(repr(c))
