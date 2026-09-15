import os
import json
import re
import hashlib
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(override=True)

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
_SUGGESTIONS_CACHE: Dict[str, List[str]] = {}

SUGGESTION_SYSTEM_PROMPT = (
    "You are generating suggested questions for a document intelligence application.\n\n"
    "Generate exactly 4 questions that a user could ask about the provided documents.\n\n"
    "STRICT RULES:\n"
    "- Use ONLY the provided document content.\n"
    "- Do not use outside knowledge.\n"
    "- Do not assume facts that are not present in the documents.\n"
    "- Every question must be answerable using the provided documents.\n"
    "- Questions must be diverse and useful.\n"
    "- Do not mention documents or topics that are not provided.\n"
    "- Do not generate generic questions unrelated to the documents.\n"
    "- Do not use Markdown.\n"
    "- Return only a JSON array of 4 question strings."
)

def compute_document_set_fingerprint(chunks: List[Dict[str, Any]], provider: str, model_name: str) -> str:
    """Computes a unique cache key based on indexed chunks and provider/model."""
    items = []
    for c in chunks:
        doc_id = c.get("doc_id") or c.get("filename") or ""
        chunk_id = c.get("chunk_id") or ""
        file_hash = c.get("file_hash") or ""
        items.append(f"{doc_id}:{chunk_id}:{file_hash}")
    items.sort()
    raw = f"{provider}_{model_name}_" + "|".join(items)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def extract_representative_content(chunks: List[Dict[str, Any]]) -> str:
    """
    Extracts representative sample chunks across all indexed documents.
    Ensures multiple documents are all proportionally represented.
    """
    if not chunks:
        return ""

    docs_map: Dict[str, List[Dict[str, Any]]] = {}
    for c in chunks:
        fname = c.get("filename") or "Untitled Document"
        docs_map.setdefault(fname, []).append(c)

    sections = []
    max_chars_per_doc = max(1000, 6000 // max(len(docs_map), 1))

    for fname, doc_chunks in docs_map.items():
        doc_text_parts = []
        n = len(doc_chunks)
        if n <= 3:
            selected_indices = list(range(n))
        else:
            # First 2 chunks, middle chunk, and last chunk
            selected_indices = sorted(list(set([0, 1, n // 2, n - 1])))

        current_chars = 0
        for idx in selected_indices:
            txt = doc_chunks[idx].get("text", "").strip()
            if not txt:
                continue
            if current_chars + len(txt) > max_chars_per_doc:
                remaining = max(0, max_chars_per_doc - current_chars)
                if remaining > 100:
                    doc_text_parts.append(txt[:remaining] + "...")
                break
            doc_text_parts.append(txt)
            current_chars += len(txt)

        doc_summary = "\n".join(doc_text_parts)
        sections.append(f"--- DOCUMENT: {fname} ---\n{doc_summary}")

    return "\n\n".join(sections)

def parse_questions_json(raw_text: str) -> List[str]:
    """Parses JSON array of question strings from raw LLM output with multiple fallbacks."""
    if not raw_text:
        return []

    # Clean markdown fences
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # Attempt 1: direct json loads
    try:
        data = json.loads(text)
        if isinstance(data, list):
            cleaned = [str(q).strip().strip('"').strip("'") for q in data if str(q).strip()]
            if len(cleaned) >= 4:
                return cleaned[:4]
            if len(cleaned) > 0:
                return cleaned
    except Exception:
        pass

    # Attempt 2: regex extract JSON array [ ... ]
    match = re.search(r"\[\s*(.*?)\s*\]", text, re.DOTALL)
    if match:
        try:
            bracket_content = f"[{match.group(1)}]"
            data = json.loads(bracket_content)
            if isinstance(data, list):
                cleaned = [str(q).strip().strip('"').strip("'") for q in data if str(q).strip()]
                if len(cleaned) >= 4:
                    return cleaned[:4]
                if len(cleaned) > 0:
                    return cleaned
        except Exception:
            pass

    # Attempt 3: Line-by-line fallback for numbered or bulleted questions ending in ?
    lines = text.split("\n")
    candidates = []
    for line in lines:
        l = line.strip()
        l = re.sub(r"^\d+[\.\)]\s*", "", l)  # Remove "1. " or "1) "
        l = re.sub(r"^[-*•]\s*", "", l)       # Remove "- " or "* "
        l = l.strip('"').strip("'").strip()
        if l and l.endswith("?"):
            candidates.append(l)

    if len(candidates) >= 4:
        return candidates[:4]
    return candidates

def generate_suggested_questions(
    vector_store,
    provider: str = "gemini",
    model_name: str = "gemini-3.6-flash",
    api_key: Optional[str] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Generates dynamic, document-aware suggested questions strictly grounded
    in currently indexed documents.
    """
    chunks = getattr(vector_store, "metadata", []) or []
    
    # Check if there are valid chunks with text
    valid_chunks = [c for c in chunks if c.get("text", "").strip()]
    
    if not valid_chunks:
        return {
            "questions": [],
            "status": "no_documents",
            "message": "Upload a document to get suggested questions.",
            "document_count": 0,
            "documents": []
        }

    filenames = sorted(list(set(c.get("filename", "Document") for c in valid_chunks if c.get("filename"))))
    fingerprint = compute_document_set_fingerprint(valid_chunks, provider, model_name)

    # Check Cache
    if not force_refresh and fingerprint in _SUGGESTIONS_CACHE:
        return {
            "questions": _SUGGESTIONS_CACHE[fingerprint],
            "status": "success",
            "cached": True,
            "document_count": len(filenames),
            "documents": filenames
        }

    representative_context = extract_representative_content(valid_chunks)
    user_prompt = (
        f"DOCUMENTS CONTENT:\n{representative_context}\n\n"
        "Generate exactly 4 diverse, useful, and answerable questions that a user could ask about these documents. "
        "Return ONLY a JSON array of 4 question strings."
    )

    provider_lower = (provider or "gemini").lower()
    raw_response = ""

    if provider_lower == "ollama":
        try:
            import ollama
            res = ollama.chat(
                model=model_name or OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": SUGGESTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                options={"temperature": 0.3}
            )
            raw_response = res.get("message", {}).get("content", "")
        except Exception as e:
            err_msg = str(e)
            if "connection" in err_msg.lower() or "refused" in err_msg.lower():
                return {
                    "questions": [],
                    "status": "error",
                    "error": "Ollama local model is not running. Please start Ollama.",
                    "document_count": len(filenames),
                    "documents": filenames
                }
            return {
                "questions": [],
                "status": "error",
                "error": f"Failed to generate questions with Ollama: {err_msg}",
                "document_count": len(filenames),
                "documents": filenames
            }
    else:
        # Gemini Cloud
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            # Fall back to Ollama if no Gemini key
            try:
                import ollama
                res = ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=[
                        {"role": "system", "content": SUGGESTION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    options={"temperature": 0.3}
                )
                raw_response = res.get("message", {}).get("content", "")
            except Exception as e:
                return {
                    "questions": [],
                    "status": "error",
                    "error": "Gemini API key is not configured and Ollama is unavailable.",
                    "document_count": len(filenames),
                    "documents": filenames
                }
        else:
            try:
                from google import genai
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name or "gemini-3.6-flash",
                    contents=[SUGGESTION_SYSTEM_PROMPT, user_prompt],
                    config=genai.types.GenerateContentConfig(temperature=0.3)
                )
                raw_response = response.text or ""
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    # Seamless fallback to local Ollama if available
                    try:
                        import ollama
                        res = ollama.chat(
                            model=OLLAMA_MODEL,
                            messages=[
                                {"role": "system", "content": SUGGESTION_SYSTEM_PROMPT},
                                {"role": "user", "content": user_prompt}
                            ],
                            options={"temperature": 0.3}
                        )
                        raw_response = res.get("message", {}).get("content", "")
                    except Exception:
                        return {
                            "questions": [],
                            "status": "error",
                            "error": "Gemini Cloud quota reached (429). Please switch to Ollama in the sidebar.",
                            "document_count": len(filenames),
                            "documents": filenames
                        }
                else:
                    return {
                        "questions": [],
                        "status": "error",
                        "error": f"Failed to generate questions with Gemini: {err_str}",
                        "document_count": len(filenames),
                        "documents": filenames
                    }

    questions = parse_questions_json(raw_response)
    if questions and len(questions) >= 4:
        questions = questions[:4]
        _SUGGESTIONS_CACHE[fingerprint] = questions
        return {
            "questions": questions,
            "status": "success",
            "cached": False,
            "document_count": len(filenames),
            "documents": filenames
        }
    elif questions:
        _SUGGESTIONS_CACHE[fingerprint] = questions
        return {
            "questions": questions,
            "status": "success",
            "cached": False,
            "document_count": len(filenames),
            "documents": filenames
        }
    else:
        return {
            "questions": [],
            "status": "error",
            "error": "Could not parse questions from AI response.",
            "document_count": len(filenames),
            "documents": filenames
        }

def clear_suggestions_cache():
    """Clears cached suggestions (e.g. after document upload, delete, or re-index)."""
    global _SUGGESTIONS_CACHE
    _SUGGESTIONS_CACHE.clear()
