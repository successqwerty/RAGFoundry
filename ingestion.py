import os
from pypdf import PdfReader

def load_documents(data_folder):
    documents = []
    
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        
        # 1. Handle .txt files
        if filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
                documents.append({
                    "filename": filename,
                    "content": text
                })
                
        # 2. Handle .pdf files
        elif filename.endswith(".pdf"):
            try:
                reader = PdfReader(file_path)
                pdf_text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        pdf_text += extracted + "\n"
                
                documents.append({
                    "filename": filename,
                    "content": pdf_text
                })
            except Exception as e:
                print(f"Error reading PDF {filename}: {e}")
                
    return documents

# Test our loader
if __name__ == "__main__":
    docs = load_documents("data")
    print(f"Loaded {len(docs)} document(s).")
    print("--- Content of first document ---")
    print(docs[0]["content"])
