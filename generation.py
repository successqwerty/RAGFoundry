import os
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)

def rewrite_query(original_question, api_key=None):
    """
    Uses Gemini to rewrite conversational user questions into search-optimized queries.
    """
    load_dotenv(override=True)
    client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
    
    prompt = (
        "You are an AI search optimizer. "
        "Rewrite the following user question into a concise, search-optimized query string "
        "designed to match document section headers and keywords in a vector database. "
        "Output ONLY the rewritten search string, nothing else.\n\n"
        f"User Question: {original_question}"
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=genai.types.GenerateContentConfig(temperature=0.0)
        )
        return response.text.strip()
    except Exception:
        return original_question

def generate_answer(question, context_chunks, api_key=None):
    """
    Constructs a RAG prompt and uses Gemini to generate a grounded answer.
    """
    formatted_context = ""
    for i, chunk in enumerate(context_chunks):
        formatted_context += f"\n--- Context Snippet {i+1} (Source: {chunk['filename']}) ---\n"
        formatted_context += f"{chunk['text']}\n"

    system_instruction = (
        "You are an accurate HR Policy Assistant. "
        "Answer the user's question strictly using ONLY the provided context snippets below. "
        "Do NOT use outside knowledge or make up policies. "
        "If the answer is not contained in the provided context, state clearly: "
        "'I do not have enough information in the provided documents to answer your question.'"
    )
    
    user_prompt = f"CONTEXT:\n{formatted_context}\n\nUSER QUESTION: {question}"

    load_dotenv(override=True)
    api_key_to_use = api_key or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key_to_use)
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
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
