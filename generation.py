import os
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)

def rewrite_query(original_question, api_key=None, provider="gemini", model_name=None):
    """
    Uses Gemini or Ollama to rewrite conversational user questions into search-optimized queries.
    """
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
                model=model_name or "llama3.2",
                messages=[{"role": "user", "content": prompt}]
            )
            return res['message']['content'].strip()
        except Exception:
            return original_question

    load_dotenv(override=True)
    client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(temperature=0.0)
        )
        return response.text.strip()
    except Exception:
        return original_question

def generate_answer_ollama(question, context_chunks, model_name="llama3.2"):
    """
    100% Offline LLM Answer Generation using local Ollama.
    """
    try:
        import ollama
    except ImportError:
        return "Error: 'ollama' package is not installed. Run 'pip install ollama'."

    formatted_context = ""
    for i, chunk in enumerate(context_chunks):
        formatted_context += f"\n--- Context Snippet {i+1} (Source: {chunk['filename']}) ---\n"
        formatted_context += f"{chunk['text']}\n"

    system_instruction = (
        "You are an accurate Universal Document Assistant. "
        "Answer the user's question strictly using ONLY the provided context snippets below. "
        "Pay careful attention to document section headings (e.g. PROJECTS vs EXPERIENCE vs CERTIFICATIONS). "
        "Do NOT confuse internships or certifications with projects if a dedicated PROJECTS section exists. "
        "If the answer is not contained in the provided context, state clearly: "
        "'I do not have enough information in the provided documents to answer your question.'"
    )
    
    user_prompt = f"CONTEXT:\n{formatted_context}\n\nUSER QUESTION: {question}"

    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            options={"temperature": 0.2}
        )
        return response['message']['content']
    except Exception as e:
        return f"Ollama Local Model Error: {e}\n(Make sure Ollama app is running locally with 'ollama run {model_name}')"

def generate_answer(question, context_chunks, api_key=None, provider="gemini", model_name="gemini-2.0-flash"):
    """
    Constructs a RAG prompt and generates an answer using Gemini (Cloud) or Ollama (Local).
    """
    if provider.lower() == "ollama":
        return generate_answer_ollama(question, context_chunks, model_name=model_name or "llama3.2")

    # Default Gemini Cloud Provider
    formatted_context = ""
    for i, chunk in enumerate(context_chunks):
        formatted_context += f"\n--- Context Snippet {i+1} (Source: {chunk['filename']}) ---\n"
        formatted_context += f"{chunk['text']}\n"

    system_instruction = (
        "You are an accurate Universal Document Assistant. "
        "Answer the user's question strictly using ONLY the provided context snippets below. "
        "Pay careful attention to document section headings (e.g. PROJECTS vs EXPERIENCE vs CERTIFICATIONS). "
        "Do NOT confuse internships or certifications with projects if a dedicated PROJECTS section exists. "
        "If the answer is not contained in the provided context, state clearly: "
        "'I do not have enough information in the provided documents to answer your question.'"
    )
    
    user_prompt = f"CONTEXT:\n{formatted_context}\n\nUSER QUESTION: {question}"

    load_dotenv(override=True)
    api_key_to_use = api_key or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key_to_use)
    
    response = client.models.generate_content(
        model=model_name or "gemini-2.0-flash",
        contents=user_prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2
        )
    )
    
    return response.text

if __name__ == "__main__":
    test_q = "what is the first project done by gayathri"
    rewritten = rewrite_query(test_q)
    print(f"Original: '{test_q}'")
    print(f"Rewritten: '{rewritten}'")
