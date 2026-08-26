from ingestion import load_documents

def chunk_text(text, chunk_size=500, overlap=50):
    """
    Smart boundary-aware chunker that respects sentence/line breaks and NEVER cuts words in half.
    """
    lines = text.split("\n")
    chunks = []
    current_chunk = ""
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        # Check if adding this line exceeds chunk_size
        if len(current_chunk) + len(line_str) + 1 <= chunk_size:
            current_chunk += ("\n" + line_str) if current_chunk else line_str
        else:
            if current_chunk:
                chunks.append(current_chunk)
                
            # If a single line is longer than chunk_size, split by spaces safely
            if len(line_str) > chunk_size:
                words = line_str.split(" ")
                current_chunk = ""
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= chunk_size:
                        current_chunk += (" " + word) if current_chunk else word
                    else:
                        chunks.append(current_chunk)
                        current_chunk = word
            else:
                current_chunk = line_str
                
    if current_chunk:
        chunks.append(current_chunk)
        
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
