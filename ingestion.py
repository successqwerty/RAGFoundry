import os
import hashlib
from pypdf import PdfReader

def get_file_hash(file_path):
    """Calculates SHA256 hash of a file for content-based deduplication."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()

def load_documents(data_folder, user_id="user_default"):
    """
    Production Document Loader:
    - Extracts page-by-page text from PDFs with exact 1-indexed page numbers.
    - Extracts .txt document content.
    - Attaches comprehensive metadata (filename, page_number, file_hash, doc_id, user_id).
    """
    documents = []
    if not os.path.exists(data_folder):
        return documents
        
    for filename in sorted(os.listdir(data_folder)):
        file_path = os.path.join(data_folder, filename)
        if not os.path.isfile(file_path) or filename.endswith(".db") or filename.startswith("."):
            continue
            
        file_hash = get_file_hash(file_path)
        doc_id = f"doc_{file_hash[:12]}"
        size_kb = round(os.path.getsize(file_path) / 1024, 1)
        
        # 1. Handle .txt files
        if filename.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    text = file.read()
                    if text.strip():
                        documents.append({
                            "doc_id": doc_id,
                            "filename": filename,
                            "file_path": file_path,
                            "file_hash": file_hash,
                            "size_kb": size_kb,
                            "user_id": user_id,
                            "pages": [{"page_number": 1, "text": text}]
                        })
            except Exception as e:
                print(f"Error reading TXT {filename}: {e}")
                
        # 2. Handle .pdf files
        elif filename.endswith(".pdf"):
            try:
                reader = PdfReader(file_path)
                pages_data = []
                for i, page in enumerate(reader.pages):
                    extracted = page.extract_text()
                    if extracted and extracted.strip():
                        pages_data.append({
                            "page_number": i + 1,
                            "text": extracted.strip()
                        })
                        
                if pages_data:
                    documents.append({
                        "doc_id": doc_id,
                        "filename": filename,
                        "file_path": file_path,
                        "file_hash": file_hash,
                        "size_kb": size_kb,
                        "user_id": user_id,
                        "pages": pages_data
                    })
            except Exception as e:
                print(f"Error reading PDF {filename}: {e}")
                
    return documents

if __name__ == "__main__":
    docs = load_documents("data")
    print(f"Loaded {len(docs)} document(s).")
    if docs:
        print(f"First doc: {docs[0]['filename']} ({len(docs[0]['pages'])} page(s))")
