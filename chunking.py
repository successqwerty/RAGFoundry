def chunk_text(text, chunk_size=500, overlap=80):
    """
    Smart boundary-aware chunker that respects sentence/line breaks and NEVER cuts words in half.
    Returns list of chunk text strings.
    """
    lines = text.split("\n")
    chunks = []
    current_chunk = ""
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        if len(current_chunk) + len(line_str) + 1 <= chunk_size:
            current_chunk += ("\n" + line_str) if current_chunk else line_str
        else:
            if current_chunk:
                chunks.append(current_chunk)
                
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

def chunk_document(doc, chunk_size=500, overlap=80):
    """
    Chunks a loaded document structure, attaching page numbers and metadata to every chunk object.
    """
    chunk_objects = []
    chunk_counter = 0
    
    for page in doc.get("pages", []):
        page_num = page["page_number"]
        page_text = page["text"]
        
        raw_chunks = chunk_text(page_text, chunk_size=chunk_size, overlap=overlap)
        
        for raw_c in raw_chunks:
            if not raw_c.strip():
                continue
            chunk_counter += 1
            chunk_id = f"{doc['doc_id']}_c{chunk_counter}"
            chunk_objects.append({
                "chunk_id": chunk_id,
                "doc_id": doc["doc_id"],
                "filename": doc["filename"],
                "file_hash": doc["file_hash"],
                "user_id": doc.get("user_id", "user_default"),
                "page_number": page_num,
                "chunk_index": chunk_counter,
                "text": raw_c
            })
            
    return chunk_objects

if __name__ == "__main__":
    from ingestion import load_documents
    docs = load_documents("data")
    if docs:
        c_objs = chunk_document(docs[0], chunk_size=300, overlap=50)
        print(f"Generated {len(c_objs)} chunk object(s) with page numbers.")
        print("First chunk sample:", c_objs[0])
