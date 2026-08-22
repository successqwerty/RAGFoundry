# 🏗️ RAGFoundry — Document Question Answering System

RAGFoundry is a lightweight, framework-free **Retrieval-Augmented Generation (RAG)** system built from scratch in Python. It allows users to ask natural language questions about custom documents (such as enterprise HR handbooks) and receive accurate, grounded answers with source citations.

---

## 💡 What is RAG?

Standard LLMs cannot read private company documents and can hallucinate when asked about internal policies. RAG solves this by acting like an **Open-Book Exam**:
1. **Document Processing**: Extracts document text, breaks it into smaller chunks, and converts it into mathematical vector embeddings.
2. **Retrieval**: When a user asks a question, the system converts the query into a vector, searches for the most semantically relevant text chunks, and feeds them to the LLM as context.
3. **Generation**: The LLM generates a precise answer grounded strictly in the retrieved source text.

---

## 🚀 How This Project Was Built

### 1. Dependency & Environment Setup
We established the project dependencies in `requirements.txt` using lean, dedicated open-source libraries instead of heavy abstractions:
* **`pypdf`**: Extracts raw text from PDF documents.
* **`sentence-transformers`**: Generates text embeddings locally using Hugging Face models.
* **`faiss-cpu`**: Facebook AI Similarity Search engine for fast vector indexing and retrieval.

### 2. Document Data Preparation
We created a dedicated `data/` directory to hold raw source files and populated it with `sample.txt` — a comprehensive Enterprise HR Handbook covering:
* Work Hours & Overtime Policy
* Paid Time Off (PTO), Sick Leave & Parental Leave
* Hybrid & Remote Work Allowances
* Health Insurance & Wellness Stipends
* Professional Development & Learning Budgets
* Travel & Expense Reimbursements

### 3. Document Ingestion Module (`ingestion.py`)
We built a custom ingestion engine that scans the `data/` folder, safely reads files into Python memory, and structures them into clean dictionaries containing:
* **`content`**: The raw text string of the document.
* **`filename`**: Source metadata preserved for auditability and citations.

### 4. Text Chunking Module (`chunking.py`)
Because full documents are too large for precise vector search and exceed LLM context windows, we built a sliding-window text chunker. It splits large documents into smaller text snippets with configurable parameters:
* **`chunk_size`**: Limits the character size of each snippet to preserve semantic focus.
* **`overlap`**: Steps the sliding window backward so consecutive chunks share overlapping text, ensuring key context is never lost across sentence boundaries.

### 5. Text Embedding Module (`embeddings.py`)
We implemented local vector embedding generation using the open-source `all-MiniLM-L6-v2` model from `sentence-transformers`:
* **`get_embedding(text)`**: Converts a single string (e.g., a user query) into a 384-dimensional vector.
* **`get_embeddings_batch(texts)`**: Converts a list of text chunks into a 2D matrix of shape `(N, 384)`.
* **Semantic Vector Space**: Maps semantic meanings into numerical coordinates so mathematical distance represents semantic similarity.

### 6. Vector Store & Search Module (`vector_store.py`)
We integrated Meta's FAISS library to index and query vector embeddings in memory:
* **`create_faiss_index(embeddings)`**: Initializes an `IndexFlatL2` vector index, formats vector data to `float32`, and indexes document embeddings.
* **`search_faiss_index(index, query_vector, k=3)`**: Performs Euclidean L2 distance similarity search to find top-$K$ matching chunks for a user question.

### 7. Retrieval Engine Module (`retrieval.py`)
We built a unified `RetrievalEngine` class that ties together ingestion, chunking, batch embeddings, and FAISS indexing into an end-to-end retrieval interface:
* **Metadata Tracking**: Maps each text chunk to its source document filename for citations.
* **`retrieve(query, k=3)`**: Embeds user query, queries FAISS index, and returns structured dictionaries containing `chunk_index`, `text`, `filename`, and `distance_score`.
### 8. Repository Protection (`.gitignore`)
We configured `.gitignore` to prevent temporary Python caches (`__pycache__`), virtual environment folders, and vector index files from being tracked in version control.

---

## 📁 Current Project Structure


RAG FOUNDRY/
├── data/
│   └── sample.txt       # Enterprise HR Handbook document
├── .gitignore           # Git ignore rules for cache & vector files
├── requirements.txt     # Dependency list (pypdf, sentence-transformers, faiss-cpu)
├── ingestion.py         # Document loader and metadata extractor
├── chunking.py          # Sliding-window text chunker
├── embeddings.py        # Vector embedding generator (all-MiniLM-L6-v2)
├── vector_store.py      # FAISS vector index & similarity search engine
├── retrieval.py         # End-to-end retrieval engine with metadata tracking
└── README.md            # Complete project documentation
