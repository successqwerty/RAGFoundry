# RAGFoundry

RAGFoundry is an AI-powered document intelligence and **Retrieval-Augmented Generation (RAG)** web application. It enables users to upload private documents, index them into dense vector stores, retrieve context-relevant information, and generate grounded answers using either local offline models (via Ollama) or cloud models (via Google Gemini BYOK).

### What It Does

RAGFoundry transforms static documents into an interactive, cited knowledge base through an end-to-end automated pipeline:

```
Document Upload → Document Parsing → Chunking → Embeddings → FAISS Vector Search → Relevant Context Retrieval → LLM Generation → Streaming Answer + Sources
```

---

## ✨ Features

- **Multi-Format Document Upload**: Ingest and parse a wide range of file types including PDF, Word (`.docx`), plain text, Markdown, spreadsheets (`.csv`, `.xlsx`), presentations (`.pptx`), HTML/XML, and structured files (`.json`, `.yaml`).
- **Dense Vector Search with FAISS**: Fast vector similarity search powered by FAISS (`IndexFlatL2`) over 384-dimensional embedding vectors.
- **Local Sentence-Transformer Embeddings**: Generates embeddings on-device using HuggingFace's `all-MiniLM-L6-v2` with zero external API dependencies for vectorization.
- **Dual AI Engine Options**:
  - **Local Offline LLM**: Run private inference through **Ollama** (e.g., `llama3.2`) with zero external data transmission.
  - **Cloud LLM (Gemini)**: Fast cloud inference through **Google Gemini** models (defaulting to `gemini-3.6-flash`, with fallback resolution to `gemini-2.5-flash` / `gemini-1.5-flash` or custom configured models).
- **Bring Your Own Key (BYOK)**: Users can provide their Gemini API key through the UI. The key is stored in browser `localStorage` and is not persisted in the application's SQLite database.
- **Real-Time Token Streaming**: Server-Sent Events (SSE) stream tokens progressively as the language model generates them.
- **Persistent Conversation History**: Multi-turn conversation sessions backed by SQLite (`rag_foundry.db`), grouped chronologically (`TODAY`, `YESTERDAY`, `PREVIOUS 7 DAYS`, `OLDER`).
- **Grounded Source Citations**: Assistant cards display supporting source document names, page numbers, and vector retrieval snippets.
- **Zero-Document Validation Guard**: If zero documents are currently indexed, the system immediately returns *"Please upload a document first."* without invoking retrieval or calling LLMs.
- **Unified Single-Port Deployment**: FastAPI serves both the REST API and the frontend Single-Page Application (SPA) through a single unified web service.
- **Responsive Theme Engine**: Dark and light modes with contrast-verified color palettes, smooth transitions, and hidden native scrollbars.

---

## 🧠 What is RAG?

**Retrieval-Augmented Generation (RAG)** is an AI architecture that enhances large language models by grounding their responses in external, authoritative documents rather than relying solely on training data. This helps ground model responses in retrieved document context and can reduce unsupported answers.

In RAGFoundry, the process works as follows:

1. **Loads documents**: Ingests files uploaded by the user via extensible format parsers.
2. **Splits them into chunks**: Segments full text into overlapping boundary-aware windows to preserve context.
3. **Converts chunks into embeddings**: Transforms textual chunks into mathematical vectors capturing semantic meaning.
4. **Stores/searches embeddings using FAISS**: Indexes dense vectors for Euclidean distance similarity lookup.
5. **Retrieves relevant chunks for a user query**: Embeds the user question and queries FAISS for the top-$k$ nearest context passages.
6. **Sends retrieved context to the selected LLM**: Constructs a prompt containing the user query and the retrieved document context.
7. **Streams the generated answer back to the user**: Progressive token delivery via Server-Sent Events (SSE).
8. **Displays supporting sources/evidence**: Highlights the document filename, page number, and snippets used to produce the answer.

---

## 🏗️ Architecture

```
                       ┌───────────────────────────────┐
                       │    RAGFoundry Web Frontend    │
                       │    (HTML5 / Vanilla CSS / JS) │
                       └───────────────┬───────────────┘
                                       │ HTTP / SSE Stream
                                       ▼
                       ┌───────────────────────────────┐
                       │     FastAPI Backend Server    │
                       │           (main.py)           │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │          RAG Pipeline         │
                       │       (rag_pipeline.py)       │
                       └───────┬───────────────┬───────┘
                               │               │
            ┌──────────────────▼──┐         ┌──▼──────────────────┐
            │ Document Ingestion  │         │  Persistent Storage │
            │ (loader_factory.py) │         │   (db_manager.py)   │
            │    (chunking.py)    │         │      (SQLite)       │
            └──────────┬──────────┘         └─────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ Vector Embeddings   │
            │   (embeddings.py)   │
            │  (all-MiniLM-L6-v2) │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  FAISS Vector Store │
            │  (vector_store.py)  │
            │   (retrieval.py)    │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │   LLM Generation    │
            │   (generation.py)   │
            ├──────────┬──────────┤
            │  Ollama  │  Gemini  │
            │ (Local)  │  (BYOK)  │
            └──────────┴──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  Streaming Response │
            │ (Server-Sent Events)│
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  Frontend Display   │
            │  (Answer + Sources) │
            └─────────────────────┘
```

### Component Roles & Technical Distinctions

| Concept | What It Does in RAGFoundry | Technical Distinction |
|---|---|---|
| **Embeddings** | Converts text chunks into 384-dimensional dense floating-point arrays using `all-MiniLM-L6-v2`. | Translates natural language into geometric vectors where semantic similarity correlates with spatial distance. |
| **FAISS** | Facebook AI Similarity Search engine managing in-memory and disk-persisted vector indexes (`IndexFlatL2`). | The specialized vector index structure that executes fast nearest-neighbor distance calculations. |
| **Retrieval** | Embeds the incoming query, searches the FAISS index for top-$k$ nearest neighbors, and formats context snippets. | Bridges the vector database with the LLM prompt by selecting the most relevant document chunks. |
| **LLM Generation** | Prompts Ollama or Google Gemini with retrieved snippets and system instructions to synthesize plain-text answers. | The language model that reads context and user questions to produce a coherent, cited answer. |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Web Server & REST API** | FastAPI, Uvicorn | High-performance async REST backend and Server-Sent Events streaming |
| **Frontend Client** | HTML5, Vanilla CSS, JavaScript, Tailwind CSS (CDN) | Single-Page Application (SPA) with responsive theming |
| **Vector Database** | Meta FAISS (`faiss-cpu`) | Hardware-optimized vector similarity index |
| **Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`) | Local 384-dimensional dense semantic embedding generation |
| **Numerical Math** | NumPy | Array transformations and embedding matrix manipulations |
| **Database** | SQLite (`sqlite3`) | Persistent storage for multi-turn conversation threads and messages |
| **Local LLM** | Ollama | On-premise offline inference engine (e.g., `llama3.2`) |
| **Cloud LLM** | Google Gemini (`google-genai`) | Cloud inference supporting user-provided API keys (BYOK) |
| **Document Loaders** | PyPDF, python-docx, python-pptx, Pandas, OpenPyXL, BeautifulSoup4, PyYAML, Pillow | Multi-format parsing for PDF, Word, PowerPoint, Excel, CSV, HTML, YAML, and image metadata |
| **Configuration** | python-dotenv | Local environment variable management |
| **HTTP Client & Testing** | HTTPX, unittest | Integration testing for async endpoints and SSE streams |
| **Legacy Interface** | Streamlit (`app.py`) | Alternative development UI |

---

## 📁 Project Structure

```text
RAGFoundry/
├── data/
│   └── .gitkeep               # Directory anchor (runtime documents & DB are excluded from Git)
├── frontend/
│   ├── index.html             # Single-Page Application interface, modals, and views
│   ├── styles.css             # Theme tokens, dark mode styles, and custom scrollbar rules
│   └── app.js                 # Client-side state handling, theme switching, and API calls
├── chunking.py                # Boundary-aware text splitter creating overlapping chunk windows
├── db_manager.py              # SQLite persistence for multi-turn conversations and messages
├── embeddings.py              # Local Sentence-Transformers embedding generator (all-MiniLM-L6-v2)
├── generation.py              # Streaming LLM response generators for Ollama and Gemini BYOK
├── ingestion.py               # Ingestion orchestrator for data folder documents
├── loader_factory.py          # Extensible document loader factory for PDF, DOCX, XLSX, PPTX, etc.
├── main.py                    # FastAPI application serving both REST API endpoints and frontend
├── rag_pipeline.py            # Master RAG pipeline connecting loaders, vector store, and generator
├── retrieval.py               # Semantic retrieval engine querying FAISS for relevant context
├── suggested_questions.py     # Document-aware suggested question generator
├── vector_store.py            # FAISS index wrapper handling serialization and similarity search
├── app.py                     # Optional development/legacy Streamlit dashboard
├── test_api.py                # Integration tests for FastAPI endpoints
├── test_metrics.py            # Unit tests for precision, accuracy, and retrieval latency metrics
├── test_rag_pipeline.py       # Unit tests for RAG pipeline indexing and retrieval
├── test_streaming.py          # Unit tests for Server-Sent Events (SSE) token streaming
├── test_zero_docs.py          # Unit tests for zero-document protection and validation guards
├── requirements.txt           # Python dependency specifications
├── .env.example               # Template for environment configuration
├── .gitignore                 # Exclusion rules for secrets, virtual envs, and runtime data
└── README.md                  # Project documentation
```

---

## 🚀 Local Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd RAGFoundry
```

### 2. Create a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the provided template to create your local `.env` file:

```bash
cp .env.example .env
```

The application provides sensible defaults:

```ini
# Optional: Server-wide Gemini API key (users can also provide this in the UI)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Local Ollama runtime settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Document storage folder
DATA_FOLDER=data
```

> **Note on API Keys**: You do not need to hardcode a Gemini API key in `.env`. Users can paste their personal Gemini API key directly into the left sidebar of the web application. Keys are stored in browser `localStorage` and never saved in the SQLite database. Real API keys must never be committed to Git.

---

## ▶️ Running the Application

Start the unified FastAPI application using Uvicorn:

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000
```

Once started, open your browser and navigate to:

```text
http://localhost:8000
```

FastAPI automatically serves the complete frontend application at `/` and handles all API requests through relative paths on port `8000`.

*(Optional Development Mode: Running the frontend separately via `python -m http.server 3000 --directory frontend` is supported for isolated frontend development, but running Uvicorn directly is the primary unified method).*

---

## 📄 Supported Document Formats

The extensible parser in `loader_factory.py` supports the following formats:

| Format | Extensions | Engine / Library | Extraction Strategy |
|---|---|---|---|
| **Portable Document Format** | `.pdf` | `pypdf` | Page-by-page text extraction with page metadata |
| **Word Documents** | `.docx`, `.doc` | `python-docx` | Paragraph-level extraction joined into full document body (with text fallback for legacy `.doc`) |
| **Plain Text & Code** | `.txt`, `.md`, `.markdown`, `.py`, `.js`, `.css`, `.rtf`, `.log`, `.ini`, `.cfg` | Python standard library | Direct UTF-8 stream ingestion with fallback error-ignoring decoding |
| **Spreadsheets** | `.csv`, `.tsv`, `.xlsx`, `.xls` | `pandas`, `openpyxl` | Tabular row serialization for CSV/TSV and per-sheet extraction for Excel workbooks |
| **Presentations** | `.pptx`, `.ppt` | `python-pptx` | Slide-by-slide shape and text frame extraction |
| **HTML / XML** | `.html`, `.htm`, `.xml` | `beautifulsoup4` | Tag stripping and clean inner text extraction |
| **Structured Data** | `.json`, `.yaml`, `.yml` | `json`, `PyYAML` | Pretty-printed structured serialization |
| **Images** | `.png`, `.jpg`, `.jpeg`, `.webp`, `.tiff`, `.bmp` | `Pillow` | Supported for image metadata ingestion (format, dimensions, mode); OCR-based text extraction is not currently implemented |

---

## 🔌 API Endpoints

All endpoints are hosted by FastAPI in `main.py`:

| Method | Endpoint | Description | Request Parameters / Body | Response Summary |
|---|---|---|---|---|
| `GET` | `/` | Serves the frontend single-page web app | None | `frontend/index.html` |
| `GET` | `/health` | System health and data directory status | None | `{"status": "ok", "documents_folder": "..."}` |
| `GET` | `/documents` | Lists all currently indexed workspace documents; clears index if empty | None | `{"documents": [...], "count": N}` |
| `POST` | `/upload` | Uploads a document and triggers FAISS indexing | Multipart: `file` (UploadFile), `clear_old` (bool form) | `{"status": "success", "filename": "..."}` |
| `DELETE` | `/documents` | Clears all documents from workspace and resets vector store | None | `{"status": "success", "message": "..."}` |
| `DELETE` | `/documents/{filename}` | Deletes a single document and rebuilds FAISS index | Path: `filename` (str) | `{"status": "success", "message": "..."}` |
| `POST` | `/ask` | Primary RAG endpoint (SSE streaming by default) | JSON body: `question`, `stream`, `k`, `provider`, `model_name`, `user_id`, `api_key`, `conversation_id` | Server-Sent Events stream (`text/event-stream`) or JSON `AskResponse` |
| `GET` | `/history` | Retrieves saved chat threads grouped by date categories | Query: `user_id` (default `"user_default"`) | `{"history": {"TODAY": [...], "YESTERDAY": [...], ...}}` |
| `GET` | `/history/{conv_id}` | Retrieves full message turn history for a specific conversation | Path: `conv_id` (str) | Conversation dictionary with messages |
| `DELETE` | `/history/{conv_id}` | Deletes a conversation by ID | Path: `conv_id` (str) | `{"status": "success", "message": "..."}` |
| `GET` | `/conversations` | Lists all saved conversations with titles and previews | Query: `user_id` (default `"user_default"`) | Array of conversation summary objects |
| `GET` | `/conversations/{conv_id}` | Pure SQLite read of saved conversation without invoking RAG or LLM | Path: `conv_id` (str) | Full saved conversation object |
| `DELETE` | `/conversations/{conv_id}` | Deletes a saved conversation and associated messages | Path: `conv_id` (str) | `{"status": "success", "message": "..."}` |
| `GET` | `/ai-engine` | Returns active AI engine provider and status | None | `{"provider": "...", "model_name": "...", "ollama_available": bool, "gemini_configured": bool}` |
| `POST` | `/reindex` | Forces complete vector re-indexing from disk | Query: `user_id` (default `"user_default"`) | `{"status": "success", "message": "..."}` |
| `GET` | `/suggested-questions` | Generates document-grounded query ideas (GET) | Query: `provider`, `model_name`, `api_key`, `force_refresh` | `{"questions": [...], "cached": bool}` |
| `POST` | `/suggested-questions` | Generates document-grounded query ideas (POST) | JSON body: `provider`, `model_name`, `api_key`, `force_refresh` | `{"questions": [...], "cached": bool}` |

### Streaming Protocol (Server-Sent Events)

When calling `POST /ask` with `stream=true` (the default), the server yields chunks with `text/event-stream` encoding:

1. `{"type": "no_documents", "message": "Please upload a document first..."}` (emitted if zero documents are indexed)
2. `{"type": "conversation_meta", "conversation_id": "...", "title": "..."}` (emitted at start of generation)
3. `{"type": "sources", "sources": ["doc.pdf · Page 1"], "chunks": [...]}` (emitted once context is retrieved)
4. `{"type": "token", "delta": "word "}` (emitted progressively as tokens are generated)
5. `{"type": "complete", "elapsed_sec": 1.12, "precision": ..., "accuracy": ..., "conversation_id": "..."}` (emitted upon generation finish)
6. `{"type": "error", "message": "..."}` (emitted if an exception occurs during generation)

---

## 💬 Conversation History

RAGFoundry implements multi-turn conversational threads using SQLite (`db_manager.py`):

- **Turn Persistence**: Each conversation can hold multiple user-question and assistant-response pairs under a unique `conversation_id`.
- **Pure Read Loading**: Clicking an existing chat in the History sidebar fetches the stored messages directly from SQLite. It does **not** re-run embeddings, FAISS search, or LLM generation.
- **Continuing Conversations**: Follow-up questions in an existing thread pass the active `conversation_id`, preserving conversation continuity.
- **Stored Citations**: Retrieved sources, context chunks, and execution timing are saved alongside each assistant message in SQLite.

---

## 🤖 LLM Providers

### 1. Ollama (Local Development)
- Runs offline on local hardware via the official Python client.
- Default model: `llama3.2` (configurable via `OLLAMA_MODEL` environment variable or API payload).
- Suitable for private on-device testing with zero cloud data transmission.

### 2. Google Gemini (Cloud BYOK)
- Cloud inference using the Google GenAI SDK.
- Configurable models: defaults to `gemini-3.6-flash`, with fallback resolution to `gemini-2.5-flash` / `gemini-1.5-flash`, or custom models specified in client requests.
- **Bring Your Own Key (BYOK)**: Users paste their Gemini API key into the sidebar. Keys are kept in browser `localStorage` and sent in request payloads. Keys are not persisted in the SQLite database.

---

## 🔎 Retrieval Pipeline

```
User Query
    │
    ▼
Query Processing (Optional Query Rewriting)
    │
    ▼
Dense Vector Embedding (all-MiniLM-L6-v2)
    │
    ▼
FAISS Similarity Search (L2 Distance over IndexFlatL2)
    │
    ▼
Top-K Relevant Chunks Extracted
    │
    ▼
Context Construction (Formatted with Document & Page Numbers)
    │
    ▼
LLM Generation (Ollama or Gemini)
    │
    ▼
Grounded Answer + Citations
```

### Why Vector Similarity?

Keyword search often fails when users ask questions using different vocabulary than the document (e.g., asking *"compensation"* when the document says *"salary"*). Vector embeddings convert words and phrases into coordinates in a high-dimensional semantic space. FAISS calculates the geometric distance between the query vector and chunk vectors to retrieve contextually relevant information regardless of exact keyword matches.

---

## 🔐 Security & Git Practices

- **No Secrets in Source Control**: `.env` and local environment files are explicitly excluded in `.gitignore`. Real API keys must never be committed.
- **No Private Data in Git**: Uploaded documents in `data/`, local vector indexes (`index.faiss`, `vector_meta.json`), and SQLite databases (`rag_foundry.db`) are ignored by Git.
- **Clean Clones**: The repository maintains a `.gitkeep` inside `data/` so the directory structure exists immediately upon cloning without checking in sensitive personal files.
- **Client Storage**: User BYOK keys are held in browser `localStorage` and are not written to SQLite database tables. Browser `localStorage` is client-side storage, not a secure server vault.
- **Scope**: The application does not currently provide authentication, passwords, or multi-tenant database isolation.

---

## 🌐 Deployment

RAGFoundry is packaged so that FastAPI serves both the backend API and the frontend UI as a single unified web application.

```
User Browser
    │
    ▼
Public RAGFoundry URL (e.g. Cloud VM / Container)
    │
    ▼
FastAPI Application (Port 8000)
    ├── Static Frontend (frontend/index.html)
    ├── RAG Pipeline (rag_pipeline.py)
    ├── FAISS Vector Store (data/index.faiss)
    └── LLM Provider
          ├── Google Gemini (Recommended for cloud deployments via BYOK)
          └── Ollama (Local host development)
```

### Cloud Deployment Notes

- When deploying to cloud environments (e.g., VPS, Docker, AWS, GCP, Render), **Google Gemini with BYOK** provides immediate remote access without server GPU requirements.
- A cloud-hosted backend cannot automatically access an Ollama instance running on a user's private local machine. For cloud deployments, Gemini BYOK is the primary option for remote users, while Ollama is intended for local self-hosted development.
- For multi-tenant production scaling, future architecture updates can incorporate user authentication, S3-compatible cloud object storage, and remote vector databases.

---

## 🧪 Testing

The repository contains automated unit and integration tests:

| Test File | What It Verifies |
|---|---|
| [`test_api.py`](test_api.py) | Verifies FastAPI endpoints (`/health`, 400 Bad Request on empty question, and `/ask` flow) using `TestClient`. |
| [`test_streaming.py`](test_streaming.py) | Verifies Server-Sent Events (SSE) streaming output and chunk generation. |
| [`test_zero_docs.py`](test_zero_docs.py) | Verifies the zero-document validation guard returns *"Please upload a document first."* without calling LLMs. |
| [`test_metrics.py`](test_metrics.py) | Verifies retrieval precision, accuracy calculations, and latency tracking. |
| [`test_rag_pipeline.py`](test_rag_pipeline.py) | Verifies document loading, vector store syncing, and retrieval pipeline flow. |

Run tests using Python's standard unittest runner:

```bash
python -m unittest discover -s . -p "test_*.py"
```

---

## 🔮 Future Improvements

The following architectural enhancements are planned for future versions:

- **Authentication & User Accounts**: Multi-user registration, role-based access control, and session tokens.
- **Per-User Document Isolation**: Scoped knowledge bases ensuring users only query their own private documents.
- **Cloud Object Storage**: Offloading uploaded files to AWS S3, Google Cloud Storage, or Cloudflare R2.
- **Persistent Cloud Vector Store**: Integration with managed vector databases such as Qdrant, Pinecone, or pgvector.
- **Automated RAG Evaluation**: Integration with Ragas or TruLens for automated faithfulness and context recall scoring.
- **Agentic Workflows**: Multi-step reasoning with tools, calculators, and web search fallback.

---

## 📌 Important Project Notes

- Runtime files, uploaded documents, vector index files, databases, and `.env` files are intentionally excluded from Git.
- Always create your local environment using `.env.example` as a template before running the application locally.
- In production, always enforce HTTPS when handling user-provided API keys.
