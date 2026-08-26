import os
from google import genai
from dotenv import load_dotenv 

def generate_answer(question, context_chunks, api_key=None):
    """
    Constructs a RAG prompt and uses Gemini to generate a grounded answer.
    """
    # 1. Combine retrieved chunks into a single formatted context string
    formatted_context = ""
    for i, chunk in enumerate(context_chunks):
        formatted_context += f"\n--- Context Snippet {i+1} (Source: {chunk['filename']}) ---\n"
        formatted_context += f"{chunk['text']}\n"

    # 2. Build the System Instruction & Prompt
    system_instruction = (
        "You are an accurate HR Policy Assistant. "
        "Answer the user's question strictly using ONLY the provided context snippets below. "
        "Do NOT use outside knowledge or make up policies. "
        "If the answer is not contained in the provided context, state clearly: "
        "'I do not have enough information in the provided documents to answer your question.'"
    )
    
    user_prompt = f"CONTEXT:\n{formatted_context}\n\nUSER QUESTION: {question}"

    load_dotenv(override=True)
    # 3. Initialize Gemini Client
    api_key_to_use = api_key or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key_to_use)
    
    # 4. Generate Content
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=user_prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2  # Low temperature for factual, low-creativity answers
        )
    )
    
    return response.text

if __name__ == "__main__":
    # Test generation with dummy context
    dummy_chunks = [
        {
            "filename": "sample.txt",
            "text": "2.1 Vacation Allowance: Full-time employees receive 18 paid vacation days per calendar year."
        }
    ]
    
    test_question = "How many vacation days do I get?"
    
    print(f"Question: '{test_question}'")
    print("\nGenerating response with Gemini...")
    
    try:
        answer = generate_answer(test_question, dummy_chunks)
        print("\n--- LLM GENERATED ANSWER ---")
        print(answer)
    except Exception as e:
        print(f"\nAPI Call Note: {e}")
        print("(Ensure GEMINI_API_KEY environment variable is set or passed to generate_answer)")
