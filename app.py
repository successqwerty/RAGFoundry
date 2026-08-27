import os
import streamlit as st
from rag_pipeline import RAGPipeline

# 1. Page Setup
st.set_page_config(
    page_title="RAGFoundry — Local AI Document Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom Professional Light Pastel CSS
custom_css = """
<style>
/* Font Imports */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Hide Default Streamlit Elements */
header[data-testid="stHeader"] { visibility: hidden; height: 0px; }
footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
#MainMenu { visibility: hidden; }

/* Global Styling */
html, body, .stApp {
    background-color: #F8F7FC !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: #374151 !important;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #F1EFFA !important;
    border-right: 1px solid #E7E5EF !important;
    width: 280px !important;
}
section[data-testid="stSidebar"] > div {
    padding: 1.5rem 1rem !important;
}

/* Main Container Width & Centering */
.main .block-container {
    max-width: 900px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    margin: 0 auto !important;
}

/* Typography Hierarchy */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    color: #374151 !important;
    font-weight: 600 !important;
}

/* Custom Cards */
.rf-card {
    background-color: #FFFFFF;
    border: 1px solid #E7E5EF;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
    box-shadow: 0 2px 10px rgba(55, 65, 81, 0.03);
}

.rf-user-card {
    background-color: #EDE9F7;
    border: 1px solid #E7E5EF;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 16px;
    color: #374151;
}

.rf-ai-card {
    background-color: #FFFFFF;
    border: 1px solid #E7E5EF;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(55, 65, 81, 0.04);
}

.rf-doc-card {
    background-color: #FFFFFF;
    border: 1px solid #E7E5EF;
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Badges */
.rf-badge-mint {
    background-color: #DDF3E8;
    color: #4F8A6B;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 12px;
    display: inline-block;
}

.rf-badge-lavender {
    background-color: #EDE9F7;
    color: #8B7CC8;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 12px;
    display: inline-block;
}

.rf-badge-blue {
    background-color: #DCEAF7;
    color: #374151;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 12px;
    display: inline-block;
}

/* Custom Buttons */
.stButton > button {
    background-color: #8B7CC8 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    transition: background-color 0.2s ease !important;
}
.stButton > button:hover {
    background-color: #7668B5 !important;
    color: #FFFFFF !important;
}

/* Sidebar Secondary Button */
.rf-secondary-btn button {
    background-color: #FFFFFF !important;
    color: #374151 !important;
    border: 1px solid #E7E5EF !important;
    border-radius: 10px !important;
}
.rf-secondary-btn button:hover {
    background-color: #EDE9F7 !important;
}

/* Input Fields */
.stTextInput > div > div > input {
    background-color: #FFFFFF !important;
    border: 1px solid #E7E5EF !important;
    border-radius: 12px !important;
    color: #374151 !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #8B7CC8 !important;
    box-shadow: 0 0 0 2px rgba(139, 124, 200, 0.2) !important;
}

/* Streamlit Expander Styling */
.st-emotion-cache-16ids9p, div[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E7E5EF !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}
div[data-testid="stExpander"] summary {
    color: #7B8190 !important;
    font-weight: 500 !important;
}

/* Section Header Labels */
.rf-sidebar-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: #7B8190;
    text-transform: uppercase;
    margin-top: 16px;
    margin-bottom: 8px;
}

/* Status Panel */
.rf-status-panel {
    background-color: #DDF3E8;
    color: #4F8A6B;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 12px;
    font-weight: 500;
    margin-top: 20px;
}

/* Suggestion Cards */
.rf-suggestion-card {
    background-color: #FFFFFF;
    border: 1px solid #E7E5EF;
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 13px;
    color: #374151;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}
.rf-suggestion-card:hover {
    border-color: #8B7CC8;
    background-color: #F8F7FC;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 3. Helper Function to Get Documents Info
def get_documents_info(data_folder="data"):
    if not os.path.exists(data_folder):
        return []
    files = os.listdir(data_folder)
    doc_list = []
    for f in files:
        file_path = os.path.join(data_folder, f)
        if os.path.isfile(file_path):
            size_kb = round(os.path.getsize(file_path) / 1024, 1)
            doc_list.append({"name": f, "size_kb": size_kb})
    return doc_list

documents_in_data = get_documents_info("data")
doc_count = len(documents_in_data)

# 4. SIDEBAR RENDERING
with st.sidebar:
    # Header Branding
    st.markdown("""
        <div style='margin-bottom: 20px;'>
            <div style='font-size: 20px; font-weight: 700; color: #374151; display: flex; align-items: center; gap: 8px;'>
                <span style='color: #8B7CC8;'>✦</span> RAGFoundry
            </div>
            <div style='font-size: 12px; color: #7B8190; margin-top: 2px;'>Local AI Document Intelligence</div>
        </div>
    """, unsafe_allow_html=True)

    # MODEL Section
    st.markdown('<div class="rf-sidebar-label">MODEL</div>', unsafe_allow_html=True)
    provider_choice = st.selectbox(
        "Model Engine",
        ["Ollama (100% Offline Local)", "Gemini (Cloud)"],
        label_visibility="collapsed"
    )
    
    if provider_choice == "Ollama (100% Offline Local)":
        selected_provider = "ollama"
        selected_model = st.text_input("Model Name", value="llama3.2", help="e.g. llama3.2, mistral")
        st.markdown('<div style="font-size:12px; color:#4F8A6B; margin-top:4px;">● Local AI Ready</div>', unsafe_allow_html=True)
    else:
        selected_provider = "gemini"
        selected_model = "gemini-2.0-flash"
        user_api_key = st.text_input("Gemini API Key (Optional)", type="password", help="Overrides default API Key")
        if user_api_key:
            os.environ["GEMINI_API_KEY"] = user_api_key.strip()
            st.markdown('<div style="font-size:12px; color:#4F8A6B; margin-top:4px;">✓ Custom Key Applied</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:12px; color:#8B7CC8; margin-top:4px;">● Gemini Cloud Active</div>', unsafe_allow_html=True)

    st.markdown("<hr style='border:none; border-top:1px solid #E7E5EF; margin:16px 0;'>", unsafe_allow_html=True)

    # WORKSPACE Section
    st.markdown(f'<div class="rf-sidebar-label">WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 10px;">Documents &nbsp;·&nbsp; {doc_count:02d}</div>', unsafe_allow_html=True)

    # Document List
    if doc_count > 0:
        for doc in documents_in_data:
            st.markdown(f"""
                <div class="rf-doc-card">
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 170px;">
                        <span style="color: #8B7CC8;">📄</span> 
                        <span style="font-size: 13px; font-weight: 500; color: #374151;">{doc['name']}</span>
                    </div>
                    <span class="rf-badge-mint">Indexed</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size: 12px; color: #7B8190; margin-bottom: 10px;">No documents uploaded yet.</div>', unsafe_allow_html=True)

    # Document Upload Controls
    clear_existing = st.checkbox("Clear old documents on upload", value=True)
    uploaded_files = st.file_uploader("Upload .txt or .pdf files", type=["txt", "pdf"], accept_multiple_files=True, label_visibility="collapsed")
    
    if uploaded_files:
        os.makedirs("data", exist_ok=True)
        if clear_existing:
            for existing_file in os.listdir("data"):
                file_path_to_remove = os.path.join("data", existing_file)
                if os.path.isfile(file_path_to_remove):
                    os.remove(file_path_to_remove)

        for file in uploaded_files:
            file_path = os.path.join("data", file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        st.markdown(f'<div class="rf-badge-mint" style="margin-top:6px;">✓ Saved {len(uploaded_files)} file(s)</div>', unsafe_allow_html=True)
        if "pipeline" in st.session_state:
            del st.session_state["pipeline"]
        st.rerun()

    # Re-Index Button
    st.markdown('<div class="rf-secondary-btn" style="margin-top: 12px;">', unsafe_allow_html=True)
    if st.button("🔄 Re-Index Documents", use_container_width=True):
        if "pipeline" in st.session_state:
            del st.session_state["pipeline"]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Bottom System Status Card
    if doc_count > 0:
        st.markdown(f"""
            <div class="rf-status-panel">
                ● System ready<br>
                <span style="font-size: 11px; font-weight: 400; opacity: 0.85;">{doc_count} document(s) indexed & searchable</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="rf-status-panel" style="background-color:#FCE8D8; color:#374151;">
                ● No documents indexed<br>
                <span style="font-size: 11px; font-weight: 400; opacity: 0.85;">Upload a PDF or TXT file above</span>
            </div>
        """, unsafe_allow_html=True)


# 5. INITIALIZE RAG PIPELINE (Cached in Session State)
if "pipeline" not in st.session_state:
    with st.spinner("Initializing RAG Engine & Indexing Documents..."):
        st.session_state["pipeline"] = RAGPipeline("data")

pipeline = st.session_state["pipeline"]


# 6. MAIN WORKSPACE CONTENT

# Top Header Layout
col_header_left, col_header_right = st.columns([3, 1])

with col_header_left:
    st.markdown('<span class="rf-badge-lavender">LOCAL AI</span>', unsafe_allow_html=True)
    st.markdown('<h1 style="font-size: 30px; margin-top: 6px; margin-bottom: 4px;">Document Q&A</h1>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 14px; color: #7B8190; margin-bottom: 24px;">Ask questions about your uploaded documents and get grounded answers with citations.</div>', unsafe_allow_html=True)

with col_header_right:
    st.markdown(f"""
        <div style="text-align: right; margin-top: 10px;">
            <span class="rf-badge-mint">● Local AI</span>
            <div style="font-size: 12px; color: #7B8190; margin-top: 4px;">{selected_provider.title()} · {selected_model}</div>
        </div>
    """, unsafe_allow_html=True)


# Session state for suggestion clicks or previous question
if "current_question" not in st.session_state:
    st.session_state["current_question"] = ""

# Function to handle suggestion click
def set_question(q_text):
    st.session_state["current_question"] = q_text


# 7. EMPTY STATE (when no question submitted yet)
if "last_result" not in st.session_state:
    st.markdown("""
        <div style="text-align: center; padding: 40px 20px; background-color: #FFFFFF; border: 1px solid #E7E5EF; border-radius: 16px; margin-bottom: 24px;">
            <div style="font-size: 32px; color: #8B7CC8; margin-bottom: 12px;">✦</div>
            <h2 style="font-size: 20px; font-weight: 600; color: #374151; margin-bottom: 6px;">Ask your documents anything</h2>
            <p style="font-size: 14px; color: #7B8190; max-width: 480px; margin: 0 auto 24px auto;">
                Upload a document in the sidebar and start asking questions using your local AI model.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="font-size: 12px; font-weight: 700; color: #7B8190; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 12px;">SUGGESTED QUESTIONS</div>', unsafe_allow_html=True)
    
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        if st.button("💡 What are the main projects?", key="sug1", use_container_width=True):
            st.session_state["current_question"] = "What are the main projects?"
            st.rerun()
    with s_col2:
        if st.button("📝 Summarize this document", key="sug2", use_container_width=True):
            st.session_state["current_question"] = "Summarize this document"
            st.rerun()
    with s_col3:
        if st.button("⚡ What skills are mentioned?", key="sug3", use_container_width=True):
            st.session_state["current_question"] = "What skills are mentioned?"
            st.rerun()


# 8. QUESTION INPUT FORM
user_query_input = st.text_input(
    "Ask anything about your documents...",
    value=st.session_state.get("current_question", ""),
    placeholder="Ask anything about your documents...",
    label_visibility="collapsed",
    key="qa_input"
)

# Submit Trigger
if user_query_input and (user_query_input != st.session_state.get("last_asked_query", "")):
    st.session_state["last_asked_query"] = user_query_input
    
    with st.spinner("Searching documents & generating grounded answer..."):
        try:
            # Production dynamic retrieval (K=10 with parent section expansion & CrossEncoder reranking)
            result = pipeline.ask(user_query_input, k=10, provider=selected_provider, model_name=selected_model)
            st.session_state["last_result"] = result
        except Exception as e:
            st.session_state["last_error"] = str(e)


# 9. DISPLAY ERROR STATE IF ANY
if "last_error" in st.session_state:
    st.markdown(f"""
        <div style="background-color: #FCE8D8; border: 1px solid #E7E5EF; border-radius: 12px; padding: 18px 22px; margin-top: 16px;">
            <div style="font-size: 15px; font-weight: 600; color: #374151; margin-bottom: 4px;">Something went wrong</div>
            <div style="font-size: 13px; color: #7B8190;">We couldn't generate an answer. Please check your local AI service and try again.</div>
            <details style="margin-top: 8px; font-size: 12px; color: #374151;">
                <summary>Show technical details</summary>
                <code style="display:block; margin-top:4px; padding:6px; background:#FFFFFF;">{st.session_state["last_error"]}</code>
            </details>
        </div>
    """, unsafe_allow_html=True)
    del st.session_state["last_error"]


# 10. DISPLAY CONVERSATION & AI ANSWER
if "last_result" in st.session_state:
    res = st.session_state["last_result"]
    
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # User Question Card
    st.markdown(f"""
        <div class="rf-user-card">
            <div style="font-size: 11px; font-weight: 700; color: #8B7CC8; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px;">You</div>
            <div style="font-size: 15px; font-weight: 500; color: #374151;">{res['question']}</div>
        </div>
    """, unsafe_allow_html=True)

    # AI Answer Card
    st.markdown(f"""
        <div class="rf-ai-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div style="font-size: 14px; font-weight: 600; color: #374151; display: flex; align-items: center; gap: 6px;">
                    <span style="color: #8B7CC8;">✦</span> RAGFoundry
                </div>
                <span class="rf-badge-blue">Grounded Response</span>
            </div>
            <div style="font-size: 15px; line-height: 1.65; color: #374151;">
                {res['answer']}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # SOURCES SECTION
    st.markdown('<h3 style="font-size: 16px; font-weight: 600; margin-top: 24px; margin-bottom: 12px;">Sources</h3>', unsafe_allow_html=True)
    
    src_cols = st.columns(min(len(res["sources"]), 3) or 1)
    for idx, src in enumerate(res["sources"]):
        col_target = src_cols[idx % len(src_cols)]
        with col_target:
            st.markdown(f"""
                <div class="rf-card" style="padding: 12px 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 13px; font-weight: 600; color: #374151;">📄 {src}</span>
                        <span class="rf-badge-blue">Relevant source</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # COLLAPSIBLE RETRIEVED CONTEXT SECTION
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    with st.expander("▸ Retrieved context (FAISS & Two-Stage Reranker Scores)"):
        st.markdown('<div style="font-size: 12px; color: #7B8190; margin-bottom: 12px;">The following text chunks were retrieved by FAISS and re-scored by the Cross-Encoder model:</div>', unsafe_allow_html=True)
        
        for rank, chunk in enumerate(res["retrieved_chunks"]):
            rerank_score = chunk.get("rerank_score", None)
            score_display = f"Rerank Score: `{rerank_score:.4f}`" if rerank_score is not None else f"Distance: `{chunk['distance_score']:.4f}`"
            
            st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E7E5EF; border-radius: 10px; padding: 14px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span class="rf-badge-lavender">Rank {rank+1}</span>
                        <span style="font-size: 12px; color: #7B8190;">{score_display} &nbsp;·&nbsp; 📄 {chunk['filename']}</span>
                    </div>
                    <div style="font-size: 13px; font-family: monospace; background-color: #F8F7FC; padding: 10px; border-radius: 6px; color: #374151; white-space: pre-wrap;">
{chunk['text']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
