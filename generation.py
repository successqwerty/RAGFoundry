import os
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

SYSTEM_INSTRUCTION = (
    "You are a document question-answering assistant. "
    "Answer the user's question strictly using ONLY the provided document context snippets below. "
    "Do not invent facts that are not supported by the context. "
    "If the answer cannot be found in the uploaded documents, clearly say: "
    "'I could not find this information in the uploaded documents.' "
    "Do not fabricate citations or sources."
)

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
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(temperature=0.0)
        )
        return response.text.strip()
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

def generate_answer_stream_gemini(question, context_chunks, api_key=None, model_name="gemini-2.0-flash"):
    """
    Gemini Cloud streaming generator. Yields string deltas.
    """
    formatted_context = format_context(context_chunks)
    user_prompt = f"CONTEXT:\n{formatted_context}\n\nUSER QUESTION: {question}"

    try:
        load_dotenv(override=True)
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            yield "Gemini API Key is missing. Please provide a valid Gemini API Key in the sidebar or .env file."
            return
        client = genai.Client(api_key=key)
        response = client.models.generate_content_stream(
            model=model_name or "gemini-2.0-flash",
            contents=[SYSTEM_INSTRUCTION, user_prompt],
            config=genai.types.GenerateContentConfig(temperature=0.2)
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"Unable to generate answer via Gemini Cloud: {e}"

def generate_answer_stream(question, context_chunks, api_key=None, provider="gemini", model_name="gemini-2.0-flash"):
    """
    Unified streaming response generator for Ollama and Gemini.
    """
    if provider.lower() == "ollama":
        return generate_answer_stream_ollama(question, context_chunks, model_name=model_name or OLLAMA_MODEL)
    else:
        return generate_answer_stream_gemini(question, context_chunks, api_key=api_key, model_name=model_name)

def generate_answer(question, context_chunks, api_key=None, provider="gemini", model_name="gemini-2.0-flash"):
    """Synchronous fallback answer generator."""
    tokens = list(generate_answer_stream(question, context_chunks, api_key=api_key, provider=provider, model_name=model_name))
    return "".join(tokens)
