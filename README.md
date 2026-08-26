# 🏗️ RAGFoundry — Document Question Answering System

RAGFoundry is a lightweight, framework-free **Retrieval-Augmented Generation (RAG)** system built from scratch in Python. It allows users to ask natural language questions about custom documents (such as enterprise HR handbooks or technical resumes) and receive accurate, grounded answers with source citations.

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
* **`google-genai`**: Official Google Gemini SDK for LLM generation (`gemini-3.6-flash`).
* **`python-dotenv`**: Manages secure API keys via a local `.env` file.
* **`streamlit`**: Interactive web application framework for browser deployment.

### 2. Document Data Preparation & Multi-Format Parsing
We created a dedicated `data/` directory supporting multi-format document loading (`.txt` and `.pdf`):
* `sample.txt`: Enterprise HR Policy Handbook.
* `pypdf`: Full page-by-page PDF text extraction.

### 3. Document Ingestion Module (`ingestion.py`)
We built a custom ingestion engine that scans the `data/` folder, safely reads `.txt` and `.pdf` files into Python memory, and structures them into clean dictionaries containing content and source metadata (`filename`).

### 4. Smart Boundary-Aware Text Chunking (`chunking.py`)
To prevent slicing words in half or breaking sentences mid-thought, we implemented a smart boundary-aware chunker that respects line breaks and word boundaries (`chunk_size=500`, `overlap=80`).

### 5. Text Embedding Module (`embeddings.py`)
We implemented local vector embedding generation using the open-source `all-MiniLM-L6-v2` model from `sentence-transformers`:
* **`get_embedding(text)`**: Converts a single string (e.g., a user query) into a 384-dimensional vector.
* **`get_embeddings_batch(texts)`**: Converts a list of text chunks into a 2D matrix of shape `(N, 384)`.

### 6. Vector Store & Search Module (`vector_store.py`)
We integrated Meta's FAISS library to index and query vector embeddings in memory using Euclidean L2 distance similarity search.

### 7. Retrieval Engine Module (`retrieval.py`)
We built a unified `RetrievalEngine` class that ties together ingestion, chunking, batch embeddings, FAISS indexing, and source metadata tracking.

### 8. LLM Generation Module (`generation.py`)
We built a grounded answer generator using Google's `gemini-3.6-flash` with strict system instructions to prevent hallucinations.

### 9. Advanced RAG Feature: AI Query Rewriting (`rewrite_query()`)
To handle noisy or casual human questions, we integrated an AI Query Rewriter that transforms conversational user prompts into concise, domain-optimized vector search queries before searching FAISS.

### 10. Master RAG Pipeline & Source Citations (`rag_pipeline.py`)
We connected query rewriting, retrieval, generation, and source metadata into an end-to-end `RAGPipeline` class that outputs grounded answers with verified source document citations (`📄 filename`).

### 11. Interactive Web Application (`app.py`)
We wrapped our pipeline into an interactive Streamlit browser UI featuring drag-and-drop document uploaders, dynamic $K$-retrieval sliders, re-indexing controls, answer cards, and expandable raw vector chunk inspectors.

---

## 📁 Current Project Structure

```text
RAG FOUNDRY/
├── data/                # Document storage directory (.txt & .pdf)
├── .env                 # API Key environment file (ignored by Git)
├── .gitignore           # Git ignore rules for cache, .env & vector files
├── requirements.txt     # Dependency list
├── ingestion.py         # Multi-format document loader (.txt & .pdf)
├── chunking.py          # Boundary-aware text chunker
├── embeddings.py        # Vector embedding generator (all-MiniLM-L6-v2)
├── vector_store.py      # FAISS vector index & similarity search engine
├── retrieval.py         # End-to-end retrieval engine with AI Query Rewriting
├── generation.py        # Query rewriter and Gemini response generator
├── rag_pipeline.py      # Master end-to-end RAG pipeline
├── app.py               # Interactive Streamlit web application
└── README.md            # Complete project documentation
