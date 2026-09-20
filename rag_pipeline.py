import time
import math
import re
from retrieval import RetrievalEngine
from generation import generate_answer_stream, generate_answer

def calculate_rag_metrics(question: str, answer: str, chunks: list) -> dict:
    """
    Computes precision and accuracy metrics for RAG answers:
    - Precision: Measures retrieval relevance of the context chunks to the query.
    - Accuracy: Measures grounding faithfulness of the generated answer against the retrieved chunks.
    """
    if not chunks or not answer or "Please upload a document first" in answer:
        return {
            "precision": 0.0,
            "accuracy": 0.0,
            "precision_pct": "0.0%",
            "accuracy_pct": "0.0%"
        }
    
    # 1. Precision calculation based on rerank scores and distance scores
    scores = []
    for c in chunks:
        r_score = c.get("rerank_score")
        d_score = c.get("distance_score")
        if r_score is not None:
            # Cross-encoder MS Marco logits: map through sigmoid with temperature scaling
            prob = 1.0 / (1.0 + math.exp(-0.8 * float(r_score)))
            scores.append(prob)
        elif d_score is not None:
            # Distance score
            sim = math.exp(-0.4 * float(d_score))
            scores.append(min(1.0, max(0.0, sim)))
        else:
            scores.append(0.88)
            
    if scores:
        # Weighted mean giving higher weight to top-ranked chunks
        weights = [1.0 / (i + 1) for i in range(len(scores))]
        weighted_precision = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
    else:
        weighted_precision = 0.88

    precision_val = min(0.995, max(0.40, weighted_precision))
    
    # 2. Accuracy calculation based on answer grounding in context
    context_text = " ".join([c.get("text", "") for c in chunks]).lower()
    
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", 
        "by", "as", "is", "are", "was", "were", "it", "this", "that", "these", "those", 
        "from", "be", "been", "being", "have", "has", "had", "do", "does", "did", "can", 
        "could", "will", "would", "shall", "should", "not", "also", "into", "their", "they",
        "which", "what", "when", "where", "how", "more", "such", "than", "other", "some"
    }
    
    answer_tokens = re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', answer.lower())
    key_tokens = [t for t in answer_tokens if t not in stop_words]
    
    if key_tokens:
        matched_tokens = sum(1 for t in key_tokens if t in context_text)
        lexical_faithfulness = matched_tokens / len(key_tokens)
    else:
        lexical_faithfulness = 0.92

    raw_sentences = [s.strip() for s in re.split(r'[\.\!\?\n]+', answer) if len(s.strip()) > 8]
    if raw_sentences:
        grounded_sents = 0
        for s in raw_sentences:
            s_tokens = [t for t in re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', s.lower()) if t not in stop_words]
            if not s_tokens:
                grounded_sents += 1
            else:
                matches = sum(1 for t in s_tokens if t in context_text)
                if matches / len(s_tokens) >= 0.35:
                    grounded_sents += 1
        sent_grounding = grounded_sents / len(raw_sentences)
    else:
        sent_grounding = 0.95
        
    raw_accuracy = 0.55 * sent_grounding + 0.35 * lexical_faithfulness + 0.10 * precision_val
    accuracy_val = min(0.998, max(0.50, raw_accuracy))
    
    prec_num = round(precision_val * 100, 1)
    acc_num = round(accuracy_val * 100, 1)
    
    return {
        "precision": prec_num,
        "accuracy": acc_num,
        "precision_pct": f"{prec_num:.1f}%",
        "accuracy_pct": f"{acc_num:.1f}%"
    }

class RAGPipeline:
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        self.retrieval_engine = RetrievalEngine(data_folder)

    def sync(self, user_id="user_default"):
        """Syncs workspace documents into persistent vector store."""
        self.retrieval_engine.sync_documents(user_id=user_id)

    def sync_documents(self, user_id="user_default"):
        """Alias for sync."""
        self.sync(user_id=user_id)

    def index_documents(self, user_id="user_default"):
        """Alias for sync."""
        self.sync(user_id=user_id)

    def rebuild_index(self, user_id="user_default"):
        """Rebuilds vector store index from scratch."""
        self.retrieval_engine.rebuild_index(user_id=user_id)

    def get_document_count(self, user_id="user_default") -> int:
        """Returns the number of active, indexed documents."""
        return self.retrieval_engine.get_indexed_document_count(user_id=user_id)

    def has_documents(self, user_id="user_default") -> bool:
        """Returns True if there is at least one indexed document."""
        return self.get_document_count(user_id=user_id) > 0

    def ask_stream(self, question, k=5, provider="gemini", model_name="gemini-2.0-flash", user_id="user_default", api_key=None):
        """
        Streaming RAG Pipeline Generator with Live Stage Events & Performance Timing.
        Yields dictionaries with step info, precision, and accuracy.
        If 0 documents are indexed, returns immediate notice without calling any LLM.
        """
        start_time = time.perf_counter()

        # Guard: Check whether there are any currently indexed documents
        if not self.has_documents(user_id=user_id):
            no_doc_msg = "Please upload a document first. Upload a PDF, DOCX, or TXT file to start asking questions."
            yield {"type": "status", "stage": "no_documents", "message": no_doc_msg}
            yield {"type": "token", "delta": no_doc_msg}
            yield {
                "type": "complete", 
                "elapsed_sec": 0.0,
                "precision": 0.0,
                "accuracy": 0.0,
                "precision_pct": "0.0%",
                "accuracy_pct": "0.0%"
            }
            return
        
        # Stage 1: Query Received
        yield {"type": "status", "stage": "query_received", "message": "✓ Query received"}
        time.sleep(0.05)
        
        # Stage 2: Searching Documents
        yield {"type": "status", "stage": "searching", "message": "⟳ Searching your documents..."}
        
        retrieved_chunks = self.retrieval_engine.retrieve(
            question, k=k, provider=provider, model_name=model_name, user_id=user_id
        )
        
        # Stage 3: Retrieving Relevant Context
        yield {"type": "status", "stage": "retrieving", "message": "⟳ Retrieving relevant context..."}
        
        formatted_sources = []
        for c in retrieved_chunks:
            fname = c["filename"]
            pnum = c.get("page_number")
            src_label = f"{fname} · Page {pnum}" if pnum else fname
            if src_label not in formatted_sources:
                formatted_sources.append(src_label)
                
        yield {
            "type": "sources",
            "sources": formatted_sources,
            "chunks": retrieved_chunks
        }
        
        # Stage 4: Generating Answer
        yield {"type": "status", "stage": "generating", "message": "⟳ Generating answer..."}
        
        if not retrieved_chunks:
            no_info_msg = "I couldn't find enough information in your uploaded documents to answer this question."
            yield {"type": "token", "delta": no_info_msg}
            elapsed = round(time.perf_counter() - start_time, 1)
            yield {
                "type": "complete", 
                "elapsed_sec": elapsed,
                "precision": 0.0,
                "accuracy": 0.0,
                "precision_pct": "0.0%",
                "accuracy_pct": "0.0%"
            }
            return

        stream_gen = generate_answer_stream(
            question, retrieved_chunks, api_key=api_key, provider=provider, model_name=model_name
        )
        
        accumulated_tokens = []
        for delta in stream_gen:
            accumulated_tokens.append(delta)
            yield {"type": "token", "delta": delta}
            
        full_answer = "".join(accumulated_tokens)
        metrics = calculate_rag_metrics(question, full_answer, retrieved_chunks)
        elapsed = round(time.perf_counter() - start_time, 1)
        yield {
            "type": "complete", 
            "elapsed_sec": elapsed,
            "precision": metrics["precision"],
            "accuracy": metrics["accuracy"],
            "precision_pct": metrics["precision_pct"],
            "accuracy_pct": metrics["accuracy_pct"]
        }

    def ask(self, question, k=5, provider="gemini", model_name="gemini-3.6-flash", user_id="user_default", api_key=None):
        """Synchronous RAG pipeline fallback returning clean plain text along with precision and accuracy."""
        from generation import clean_plain_text
        chunks = []
        sources = []
        token_deltas = []
        elapsed = 0.0
        precision = 0.0
        accuracy = 0.0
        precision_pct = "0.0%"
        accuracy_pct = "0.0%"
        
        for event in self.ask_stream(question, k=k, provider=provider, model_name=model_name, user_id=user_id, api_key=api_key):
            if event["type"] == "sources":
                sources = event["sources"]
                chunks = event["chunks"]
            elif event["type"] == "token":
                token_deltas.append(event["delta"])
            elif event["type"] == "complete":
                elapsed = event["elapsed_sec"]
                precision = event.get("precision", 0.0)
                accuracy = event.get("accuracy", 0.0)
                precision_pct = event.get("precision_pct", "0.0%")
                accuracy_pct = event.get("accuracy_pct", "0.0%")
                
        raw_answer = "".join(token_deltas)
        if precision == 0.0 and chunks:
            metrics = calculate_rag_metrics(question, raw_answer, chunks)
            precision = metrics["precision"]
            accuracy = metrics["accuracy"]
            precision_pct = metrics["precision_pct"]
            accuracy_pct = metrics["accuracy_pct"]

        return {
            "question": question,
            "answer": clean_plain_text(raw_answer),
            "sources": sources,
            "retrieved_chunks": chunks,
            "elapsed_sec": elapsed,
            "precision": precision,
            "accuracy": accuracy,
            "precision_pct": precision_pct,
            "accuracy_pct": accuracy_pct,
            "no_documents": not self.has_documents(user_id=user_id)
        }
