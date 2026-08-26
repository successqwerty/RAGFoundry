from retrieval import RetrievalEngine
from generation import generate_answer

class RAGPipeline:
    def __init__(self, data_folder="data"):
        print("Initializing RAGFoundry Pipeline...")
        # 1. Build the retrieval engine (ingest, chunk, embed, index)
        self.retrieval_engine = RetrievalEngine(data_folder)
        print("Pipeline Ready!\n")

    def ask(self, question, k=3):
        """
        End-to-end RAG workflow: Question -> Retrieve -> Generate Answer.
        """
        # Step 1: Retrieve relevant chunks
        retrieved_chunks = self.retrieval_engine.retrieve(question, k=k)
        
        # Step 2: Generate answer using retrieved chunks as context
        llm_answer = generate_answer(question, retrieved_chunks)
        
        return {
            "question": question,
            "retrieved_chunks": retrieved_chunks,
            "answer": llm_answer
        }

if __name__ == "__main__":
    # Initialize the complete pipeline
    rag = RAGPipeline("data")
    
    # Test Question
    user_query = "What is the internet reimbursement for remote workers?"
    
    # Execute full RAG pipeline
    result = rag.ask(user_query, k=2)
    
    # Print Intermediate Values Visually
    print("=" * 60)
    print("STAGE 1: USER QUESTION")
    print("=" * 60)
    print(result["question"])
    
    print("\n" + "=" * 60)
    print("STAGE 2: RETRIEVED CHUNKS FROM FAISS")
    print("=" * 60)
    for rank, chunk in enumerate(result["retrieved_chunks"]):
        print(f"\n[Rank {rank+1}] Distance: {chunk['distance_score']:.4f} | Source: {chunk['filename']}")
        print(f"Snippet: {repr(chunk['text'])}")
        
    print("\n" + "=" * 60)
    print("STAGE 3: FINAL LLM GENERATED ANSWER")
    print("=" * 60)
    print(result["answer"])
