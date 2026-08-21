import os

def load_documents(data_folder):
    documents = []
    
    for filename in os.listdir(data_folder):
        if filename.endswith(".txt"):
            file_path = os.path.join(data_folder, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
                documents.append({
                    "filename": filename,
                    "content": text
                })
                
    return documents

# Test our loader
if __name__ == "__main__":
    docs = load_documents("data")
    print(f"Loaded {len(docs)} document(s).")
    print("--- Content of first document ---")
    print(docs[0]["content"])
