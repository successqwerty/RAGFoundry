import os
import streamlit as st
from rag_pipeline import RAGPipeline

# Page Configuration
st.set_page_config(page_title="RAGFoundry", page_icon="🏗️", layout="wide")

st.title("🏗️ RAGFoundry — Document Question Answering System")
st.markdown("Ask natural language questions about your uploaded documents and get grounded AI answers with source citations.")

# Sidebar: File Uploader & Controls
with st.sidebar:
    st.header("⚙️ Document Management")
    uploaded_files = st.file_uploader("Upload .txt or .pdf files", type=["txt", "pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        os.makedirs("data", exist_ok=True)
        for file in uploaded_files:
            file_path = os.path.join("data", file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        st.success(f"Saved {len(uploaded_files)} file(s) to data/")
        # Clear cached pipeline to reload new documents
        if "pipeline" in st.session_state:
            del st.session_state["pipeline"]

    st.markdown("---")
    if st.button("🔄 Re-Index Documents", use_container_width=True):
        if "pipeline" in st.session_state:
            del st.session_state["pipeline"]
        st.rerun()

    k_value = st.slider("Number of Chunks to Retrieve (K):", min_value=1, max_value=5, value=2)

# Initialize RAG Pipeline in Streamlit Session State (cached so it loads once)
if "pipeline" not in st.session_state:
    with st.spinner("Initializing RAG Engine & Indexing Documents..."):
        st.session_state["pipeline"] = RAGPipeline("data")

pipeline = st.session_state["pipeline"]

# User Question Input
user_question = st.text_input("💬 Ask a question about your documents:", placeholder="e.g. What is the vacation policy?")

if user_question:
    with st.spinner("Searching vectors & generating answer..."):
        try:
            result = pipeline.ask(user_question, k=k_value)
            
            # Display LLM Answer
            st.subheader("💡 Answer:")
            st.info(result["answer"])
            
            # Display Sources
            st.subheader("📄 Sources Cited:")
            for src in result["sources"]:
                st.markdown(f"* `📄 {src}`")
                
            # Display Retrieved Chunks Details in an Accordion
            with st.expander("🔍 View Raw Retrieved Chunks & FAISS Scores"):
                for rank, chunk in enumerate(result["retrieved_chunks"]):
                    st.markdown(f"**Rank {rank+1}** | **Distance Score**: `{chunk['distance_score']:.4f}` | **File**: `{chunk['filename']}`")
                    st.code(chunk["text"], language="text")
                    st.markdown("---")
                    
        except Exception as e:
            st.error(f"Error generating answer: {e}")
