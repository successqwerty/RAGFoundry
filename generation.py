import os
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)

import re

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

SYSTEM_INSTRUCTION = (
    "You are a document question-answering assistant. "
    "Answer the user's question strictly using ONLY the provided document context snippets below. "
    "Do not invent facts that are not supported by the context. "
    "If the answer cannot be found in the uploaded documents, clearly say: "
    "'I could not find this information in the uploaded documents.' "
    "Do not fabricate citations or sources.\n\n"
    "CRITICAL FORMATTING INSTRUCTIONS:\n"
    "Return the answer as clean plain text only.\n"
    "Do not use Markdown.\n"
    "Do not use Markdown headings.\n"
    "Do not use #, ##, or ###.\n"
    "Do not use bold markers such as **.\n"
    "Do not use italic markers such as *.\n"
    "Do not use Markdown bullet syntax.\n"
    "Do not use horizontal rules such as ---.\n"
    "Use simple numbered sections where appropriate.\n"
    "Use normal paragraphs.\n"
    "Use line breaks between sections.\n"
    "Return readable human-friendly plain text."
)

def clean_plain_text(text: str) -> str:
    """Conservative sanitization fallback to strip any residual Markdown markers."""
    if not text:
        return ""
    # Strip markdown headings like ###, ##, # at start of lines
    cleaned = re.sub(r'^[ \t]*#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Strip bold and italic markdown markers (**text** -> text, *text* -> text)
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
    cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
    # Strip leading markdown bullet asterisks or dashes (* item -> item)
    cleaned = re.sub(r'^[ \t]*\*\s+', '', cleaned, flags=re.MULTILINE)
    # Strip horizontal rules like ---, ***, ___ on their own line
    cleaned = re.sub(r'^[ \t]*[-*_]{3,}[ \t]*$', '', cleaned, flags=re.MULTILINE)
    # Clean up redundant empty lines caused by stripped rules
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def rewrite_query(original_question, api_key=None, provider="gemini", model_name=None):
    """Uses Gemini or Ollama to rewrite user questions into search-optimized queries."""
    prompt = (
        "You are an AI search optimizer. "
        "Rewrite the following user question into a clear, natural search query "
        "designed to find document section headings and keywords in a vector database. "
        "Do NOT use search operators like '+' or Quotes. Output ONLY plain natural words, nothing else.\n\n"
        f"User Question: {original_question}"
    )
    
    if provider.lower() == "ollama":
        try:
            import ollama
            res = ollama.chat(
                model=model_name or OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            return res['message']['content'].strip()
        except Exception:
            return original_question

    try:
        load_dotenv(override=True)
        client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(temperature=0.0)
        )
        return response.text.strip()
    except Exception:
        try:
            import ollama
            res = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            return res['message']['content'].strip()
        except Exception:
            return original_question

def format_context(context_chunks):
    """Formats context chunks with page numbers and source filenames."""
    formatted_context = ""
    for i, chunk in enumerate(context_chunks):
        page_info = f" (Page {chunk['page_number']})" if chunk.get('page_number') else ""
        formatted_context += f"\n--- Context Snippet {i+1} [Source: {chunk['filename']}{page_info}] ---\n"
        formatted_context += f"{chunk['text']}\n"
    return formatted_context

def generate_answer_stream_ollama(question, context_chunks, model_name="llama3.2"):
    """
    100% Offline LLM Answer Generation using local Ollama streaming tokens.
    Yields string deltas. Handles Ollama connection errors gracefully.
    """
    try:
        import ollama
    except ImportError:
        yield "AI model package 'ollama' is not installed. Please install it using 'pip install ollama'."
        return

    formatted_context = format_context(context_chunks)
    user_prompt = f"CONTEXT:\n{formatted_context}\n\nUSER QUESTION: {question}"

    try:
        stream = ollama.chat(
            model=model_name or OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_prompt}
            ],
            options={"temperature": 0.2},
            stream=True
        )
        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
    except Exception as e:
        err_msg = str(e)
        if "connection" in err_msg.lower() or "refused" in err_msg.lower() or "not found" in err_msg.lower():
            yield "AI model is currently unavailable. Please make sure Ollama is running and try again."
        else:
            yield f"Unable to generate answer: {err_msg}"

def generate_answer_stream_gemini(question, context_chunks, api_key=None, model_name="gemini-3.6-flash"):
    """
    Gemini Cloud streaming generator with automatic Ollama fallback on quota exhaustion (429).
    """
    formatted_context = format_context(context_chunks)
    user_prompt = f"CONTEXT:\n{formatted_context}\n\nUSER QUESTION: {question}"

    load_dotenv(override=True)
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        # If no key, fall back to local Ollama directly
        for chunk in generate_answer_stream_ollama(question, context_chunks, model_name=OLLAMA_MODEL):
            yield chunk
        return

    candidate_models = ["gemini-3.6-flash", model_name, "gemini-2.5-flash", "gemini-1.5-flash"]
    models_to_try = []
    for m in candidate_models:
        if m and m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    for m in models_to_try:
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content_stream(
                model=m,
                contents=[SYSTEM_INSTRUCTION, user_prompt],
                config=genai.types.GenerateContentConfig(temperature=0.2)
            )
            yielded_any = False
            for chunk in response:
                if chunk.text:
                    yielded_any = True
                    yield chunk.text
            if yielded_any:
                return
        except Exception as e:
            last_error = e
            err_str = str(e)
            if "404" in err_str or "NOT_FOUND" in err_str or "not found" in err_str.lower():
                continue
            elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                # Automatic seamless fallback to local Ollama!
                try:
                    for chunk in generate_answer_stream_ollama(question, context_chunks, model_name=OLLAMA_MODEL):
                        yield chunk
                    return
                except Exception:
                    yield f"Gemini Cloud quota reached (429). Please switch to Ollama in the sidebar."
                    return
            else:
                yield f"Unable to generate answer via Gemini Cloud: {e}"
                return

    # If all candidate models failed, fall back to Ollama
    try:
        for chunk in generate_answer_stream_ollama(question, context_chunks, model_name=OLLAMA_MODEL):
            yield chunk
    except Exception:
        yield f"Unable to generate answer: {last_error}"


def generate_answer_stream(question, context_chunks, api_key=None, provider="gemini", model_name="gemini-3.6-flash"):
    """
    Unified streaming response generator for Ollama and Gemini.
    """
    if provider.lower() == "ollama":
        return generate_answer_stream_ollama(question, context_chunks, model_name=model_name or OLLAMA_MODEL)
    else:
        return generate_answer_stream_gemini(question, context_chunks, api_key=api_key, model_name=model_name or "gemini-3.6-flash")

def generate_answer(question, context_chunks, api_key=None, provider="gemini", model_name="gemini-3.6-flash"):
    """Synchronous fallback answer generator with plain text sanitization."""
    tokens = list(generate_answer_stream(question, context_chunks, api_key=api_key, provider=provider, model_name=model_name))
    raw_answer = "".join(tokens)
    return clean_plain_text(raw_answer)
