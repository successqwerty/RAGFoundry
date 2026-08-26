from retrieval import RetrievalEngine
from generation import generate_answer

class RAGPipeline:
    def __init__(self, data_folder="data"):
        print("Initializing RAGFoundry Pipeline...")
        self.retrieval_engine = RetrievalEngine(data_folder)
        print("Pipeline Ready!\n")

    def ask(self, question, k=3):
        """
        End-to-end RAG workflow with Source Citations.
        """
        # Step 1: Retrieve relevant chunks with metadata
        retrieved_chunks = self.retrieval_engine.retrieve(question, k=k)
        
        # Step 2: Generate answer using retrieved chunks as context
        llm_answer = generate_answer(question, retrieved_chunks)
        
        # Step 3: Extract unique source filenames for citations
        sources = sorted(list(set(chunk["filename"] for chunk in retrieved_chunks)))
        
        return {
            "question": question,
            "answer": llm_answer,
            "sources": sources,
            "retrieved_chunks": retrieved_chunks
        }

if __name__ == "__main__":
    rag = RAGPipeline("data")
    
    # user_query = "What happens if I stay late at the office after 5 PM?"
    # user_query = "Can I bring my pet dog to the office?"
    user_query = "What is the annual learning budget for employees?"


    result = rag.ask(user_query, k=2)
    
    print("=" * 60)
    print("USER QUESTION:", result["question"])
    print("=" * 60)
    
    print("\n--- LLM GENERATED ANSWER ---")
    print(result["answer"])
    
    print("\n--- SOURCES CITED ---")
    for src in result["sources"]:
        print(f" {src}")

