# 🏗️ RAGFoundry — Enterprise Document Intelligence & Conversational RAG

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![FAISS](https://img.shields.io/badge/Vector_DB-FAISS-00599C.svg)](https://github.com/facebookresearch/faiss)
[![Gemini](https://img.shields.io/badge/LLM-Google_Gemini-4285F4.svg)](https://ai.google.dev/)
[![Ollama](https://img.shields.io/badge/Local_LLM-Ollama-black.svg)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)

**RAGFoundry** is a modern, high-performance **Retrieval-Augmented Generation (RAG)** platform designed to transform private business documents into interactive, cited knowledge bases. It features a ChatGPT-style conversational architecture, dual AI engine execution (100% offline local models via Ollama or ultra-fast cloud inference via Google Gemini), persistent multi-turn SQLite conversation history, and a sleek, responsive Single-Page Application (SPA).

---

## 📸 Architecture & Overview

```
                      ┌───────────────────────────────┐
                      │    RAGFoundry Web Frontend    │
                      │  (Vanilla HTML5 / CSS / JS)   │
                      └───────────────┬───────────────┘
                                      │ REST API / JSON
                                      ▼
                      ┌───────────────────────────────┐
                      │    FastAPI Backend Server     │
                      │          (main.py)            │
                      └───────┬───────────────┬───────┘
                              │               │
            ┌─────────────────▼──┐         ┌──▼─────────────────┐
            │   RAG Pipeline     │         │ Persistent Storage │
            │ (rag_pipeline.py)  │         │  (db_manager.py)   │
            └─────────┬──────────┘         └──────────┬─────────┘
                      │                               │
         ┌────────────┼────────────┐           ┌──────┴──────┐
         ▼            ▼            ▼           ▼             ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────────┐
   │ Ingestion│ │Embeddings│ │  FAISS   │ │ SQLite  │ │Vector Meta  │
   │& Parsing │ │MiniLM-L6 │ │Vector DB │ │  Chats  │ │ & Doc Store │
   └──────────┘ └──────────┘ └──────────┘ └─────────┘ └─────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
   ┌──────────┐              ┌──────────┐
   │  Ollama  │              │  Gemini  │
   │ (Local)  │              │ (Cloud)  │
   └──────────┘              └──────────┘
```

---

## ✨ Key Features

### 1. Dual AI Engine Architecture
* **🦙 100% Offline Local Model (Ollama)**: Zero data leakage, unlimited tokens, and no external API quotas using local models like `llama3.2`.
* **⚡ Google Gemini Cloud AI**: Real-time cloud intelligence with `gemini-2.5-flash` / `gemini-1.5-flash`.
* **🔑 Bring Your Own Key (BYOK)**: Secure client-side API key management stored in browser `localStorage` and passed directly in session headers without server persistence.

### 2. True Multi-Turn Persistent Conversations
* Modeled after modern ChatGPT architectures:
  $$\text{Conversation} \longrightarrow (\text{User Question} \longleftrightarrow \text{Grounded Answer}) \times N$$
* **Pure Read History**: Reopening saved chats from History loads existing messages instantly from SQLite without costly re-generation or re-retrieval.
* **Date Grouping**: Automatic chronological grouping (`TODAY`, `YESTERDAY`, `PREVIOUS 7 DAYS`, `OLDER`).
* **Custom Modals**: Native-like modal dialogs for chat deletion and alerts with dimmed backdrops and smooth animations.

### 3. Multi-Format Document Ingestion & Chunking
* **Extensible Loader Factory (`loader_factory.py`)**: Seamless parsing of `.pdf`, `.docx`, `.txt`, `.md`, `.csv`, `.json`, and more.
* **Boundary-Aware Chunking (`chunking.py`)**: Slices text into overlapping windows (`chunk_size=500`, `overlap=80`) without truncating words or sentence structures.
* **Dense Vector Embeddings (`embeddings.py`)**: Local 384-dimensional dense vectors generated via `sentence-transformers/all-MiniLM-L6-v2`.
* **FAISS Vector Index (`vector_store.py`)**: Hardware-accelerated Euclidean (L2) semantic similarity search.

### 4. Grounded Citations & Evidence Drawers
* Every assistant response is strictly anchored in retrieved vector chunks.
* Interactive **Evidence & Sources** dropdown reveals exact document filenames, chunks, and latency benchmarks (`⚡ 1.25s`).

### 5. Pixel-Close Responsive UI & Theming
* **Sleek Dark Mode & Light Mode**: Complete contrast-verified design tokens with seamless toggling and zero flash of unstyled content.
* **Hidden Visual Scrollbars**: Scoped CSS hides right-edge scrollbars on the Left Sidebar and History page while keeping 100% active mouse wheel, touch, and trackpad scrolling.
* **Centered Ask Composition**: Clean empty state with zero hardcoded clutter that transitions smoothly to chat stream upon submission.

---

## 📁 Repository Structure

```text
RAG FOUNDRY/
├── data/                       # Ingested documents, vector store & SQLite DB
│   ├── rag_foundry.db          # Persistent SQLite conversation database
│   ├── vector_meta.json        # Chunk metadata and file provenance mappings
│   └── ...                     # Uploaded documents (.pdf, .docx, .txt)
├── frontend/                   # Client Single-Page Application (SPA)
│   ├── index.html              # Main application markup & UI layout
│   ├── styles.css              # Custom styling, dark mode tokens & scrollbar rules
│   └── app.js                  # Frontend utilities and event handlers
├── chunking.py                 # Boundary-aware text chunker
├── db_manager.py               # SQLite schema & conversation persistence engine
├── embeddings.py               # Sentence-Transformers vector embedding module
├── generation.py               # Dual-engine generation (Gemini & Ollama)
├── ingestion.py                # Legacy text/pdf ingestion handler
├── loader_factory.py           # Multi-format document loader factory (PDF, DOCX, TXT)
├── main.py                     # FastAPI REST API application server
├── rag_pipeline.py             # Master RAG pipeline orchestrator
├── requirements.txt            # Python package dependencies
├── retrieval.py                # Semantic retrieval engine with FAISS
├── suggested_questions.py      # Dynamic document-aware suggested questions generator
├── test_api.py                 # Automated unit tests for FastAPI endpoints
├── vector_store.py             # Meta FAISS vector similarity search index
└── README.md                   # Comprehensive project documentation
```

---

## 🚀 Quick Start & Installation

### 1. Clone Repository & Setup Virtual Environment

```bash
# Clone repository
git clone https://github.com/successqwerty/RAGFoundry.git
cd RAGFoundry

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables (`.env`)

Create a `.env` file in the root directory (optional if using client-side BYOK or Ollama):

```env
# Optional server-wide Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Default Ollama Host
OLLAMA_HOST=http://localhost:11434
```

### 3. Launch Ollama (Optional for Local Mode)

If running offline with local models:

```bash
# Pull and start llama3.2
ollama pull llama3.2
ollama run llama3.2
```

### 4. Start the Application

Open two terminal windows:

#### Terminal 1 — Backend API (FastAPI):
```bash
uvicorn main:app --reload --port 8000
```
*API documentation available at `http://localhost:8000/docs`.*

#### Terminal 2 — Frontend Server:
```bash
python -m http.server 3000 --directory frontend
```
*Open your browser and navigate to `http://localhost:3000`.*

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ask` | Submit multi-turn query, run vector retrieval, generate grounded answer |
| `POST` | `/upload` | Upload `.pdf`, `.docx`, or `.txt` file for chunking and FAISS indexing |
| `GET` | `/documents` | List all indexed documents in knowledge base with chunk statistics |
| `DELETE` | `/documents/{filename}` | Delete document and re-sync FAISS index |
| `GET` | `/history` | Retrieve saved conversations grouped by date (`TODAY`, `OLDER`, etc.) |
| `GET` | `/conversations/{id}` | Pure SQLite read of full message history for a conversation |
| `DELETE` | `/conversations/{id}` | Delete a saved conversation and its message history |
| `GET` | `/health` | System health check and model connectivity status |

---

## 🛡️ Privacy & Security

- **Client-Side Keys**: Custom Gemini API keys are held strictly in the browser's `localStorage` and transmitted via HTTPS headers per request.
- **Local Fallback**: Switching to Ollama routes 100% of embeddings and generations on-premise without cloud calls.
- **Data Isolation**: Source documents and vector indices remain on your local disk in the `data/` directory.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
