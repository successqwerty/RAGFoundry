import os
import streamlit as st
from rag_pipeline import RAGPipeline

# 1. Page Configuration
st.set_page_config(
    page_title="RAGFoundry — Local AI Document Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom Professional Light Pastel & Workspace CSS
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Hide Default Header & Footer Chrome */
header[data-testid="stHeader"] { visibility: hidden; height: 0px; }
footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
#MainMenu { visibility: hidden; }

/* Ensure Sidebar Collapse Toggle is ALWAYS Visible & Styled */
[data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"] {
    display: flex !important;
    visibility: visible !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E7E5EF !important;
    border-radius: 10px !important;
    color: #8B7CC8 !important;
    box-shadow: 0 2px 8px rgba(55, 65, 81, 0.08) !important;
    position: fixed !important;
    top: 14px !important;
    left: 14px !important;
    z-index: 999999 !important;
    width: 38px !important;
    height: 38px !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="collapsedControl"]:hover, [data-testid="stSidebarCollapseButton"]:hover {
    background-color: #EDE9F7 !important;
    color: #7668B5 !important;
}

/* Global Application Styling */
html, body, .stApp {
    background-color: #F8F7FC !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: #374151 !important;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #F1EFFA !important;
    border-right: 1px solid #E7E5EF !important;
    width: 270px !important;
}
section[data-testid="stSidebar"] > div {
    padding: 1.5rem 1rem !important;
}

/* Main Container Alignment & Max Width */
.main .block-container {
    max-width: 1050px !important;
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

/* Large AI Query Composer Styling */
.stTextArea textarea {
    background-color: #FFFFFF !important;
    border: 1px solid #E7E5EF !important;
    border-radius: 16px !important;
    color: #374151 !important;
    padding: 16px !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 4px 14px rgba(55, 65, 81, 0.03) !important;
    resize: none !important;
}
.stTextArea textarea:focus {
    border-color: #8B7CC8 !important;
    box-shadow: 0 0 0 3px rgba(139, 124, 200, 0.15) !important;
}

/* Custom Cards */
.rf-card {
    background-color: #FFFFFF;
    border: 1px solid #E7E5EF;
    border-radius: 14px;
    padding: 20px 24px;
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
    padding: 8px 12px;
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

/* Primary Lavender Button */
.stButton > button {
    background-color: #8B7CC8 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 8px 18px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    transition: background-color 0.2s ease !important;
}
.stButton > button:hover {
    background-color: #7668B5 !important;
    color: #FFFFFF !important;
}

/* Secondary White Button */
.rf-secondary-btn button {
    background-color: #FFFFFF !important;
    color: #374151 !important;
    border: 1px solid #E7E5EF !important;
    border-radius: 10px !important;
}
.rf-secondary-btn button:hover {
    background-color: #EDE9F7 !important;
}

/* Suggested Query White Cards */
.rf-sug-btn button {
    background-color: #FFFFFF !important;
    color: #374151 !important;
    border: 1px solid #E7E5EF !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    text-align: left !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02) !important;
}
.rf-sug-btn button:hover {
    border-color: #8B7CC8 !important;
    background-color: #EDE9F7 !important;
    color: #374151 !important;
}

/* Streamlit Expander Styling */
div[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E7E5EF !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}
div[data-testid="stExpander"] summary {
    color: #7B8190 !important;
    font-weight: 500 !important;
}

/* Sidebar Section Headers */
.rf-sidebar-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: #7B8190;
    text-transform: uppercase;
    margin-top: 18px;
    margin-bottom: 8px;
}

/* Sidebar System Status */
.rf-status-panel {
    background-color: #DDF3E8;
    color: #4F8A6B;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 12px;
    font-weight: 500;
    margin-top: 24px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 3. Helper Function to List Documents
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

# 4. SIDEBAR RENDERING (WORKSPACE & MODEL)
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

    # WORKSPACE SECTION
    st.markdown('<div class="rf-sidebar-label">WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 10px;">Documents &nbsp;·&nbsp; {doc_count}</div>', unsafe_allow_html=True)

    if doc_count > 0:
        for doc in documents_in_data:
            st.markdown(f"""
                <div class="rf-doc-card">
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 160px;">
                        <span style="color: #8B7CC8;">📄</span> 
                        <span style="font-size: 13px; font-weight: 500; color: #374151;">{doc['name']}</span>
                    </div>
                    <span class="rf-badge-mint">✓ Indexed</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size: 12px; color: #7B8190; margin-bottom: 10px;">No documents uploaded yet.</div>', unsafe_allow_html=True)

    # Upload Controls
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
    st.markdown('<div class="rf-secondary-btn" style="margin-top: 10px;">', unsafe_allow_html=True)
    if st.button("🔄 Re-Index Documents", use_container_width=True):
        if "pipeline" in st.session_state:
            del st.session_state["pipeline"]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr style='border:none; border-top:1px solid #E7E5EF; margin:16px 0;'>", unsafe_allow_html=True)

    # AI ENGINE / MODEL SECTION
    st.markdown('<div class="rf-sidebar-label">AI ENGINE</div>', unsafe_allow_html=True)
    provider_choice = st.selectbox(
        "Select Provider",
        ["Ollama (100% Offline Local)", "Gemini (Cloud)"],
        label_visibility="collapsed"
    )
    
    if provider_choice == "Ollama (100% Offline Local)":
        selected_provider = "ollama"
        selected_model = st.text_input("Model Name", value="llama3.2", help="e.g. llama3.2, mistral")
        st.markdown('<div style="font-size:12px; color:#4F8A6B; margin-top:4px;">● Local AI Active</div>', unsafe_allow_html=True)
    else:
        selected_provider = "gemini"
        selected_model = "gemini-2.0-flash"
        user_api_key = st.text_input("Gemini API Key (Optional)", type="password", help="Overrides default API Key")
        if user_api_key:
            os.environ["GEMINI_API_KEY"] = user_api_key.strip()
            st.markdown('<div style="font-size:12px; color:#4F8A6B; margin-top:4px;">✓ Custom Key Applied</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:12px; color:#8B7CC8; margin-top:4px;">● Gemini Cloud Active</div>', unsafe_allow_html=True)

    # SYSTEM STATUS CARD AT BOTTOM
    if doc_count > 0:
        st.markdown(f"""
            <div class="rf-status-panel">
                ● System ready<br>
                <span style="font-size: 11px; font-weight: 400; opacity: 0.85;">{doc_count} document(s) indexed</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="rf-status-panel" style="background-color:#FCE8D8; color:#374151;">
                ● No documents indexed<br>
                <span style="font-size: 11px; font-weight: 400; opacity: 0.85;">Upload a PDF or TXT above</span>
            </div>
        """, unsafe_allow_html=True)


# 5. INITIALIZE PIPELINE (Session State Cached)
if "pipeline" not in st.session_state:
    with st.spinner("Initializing RAG Engine & Indexing Documents..."):
        st.session_state["pipeline"] = RAGPipeline("data")

pipeline = st.session_state["pipeline"]


# 6. MAIN WORKSPACE CONTENT

# Top Header Layout
col_head_left, col_head_right = st.columns([3, 1])

with col_head_left:
    st.markdown('<span class="rf-badge-lavender">DOCUMENT INTELLIGENCE</span>', unsafe_allow_html=True)
    st.markdown('<h1 style="font-size: 32px; margin-top: 6px; margin-bottom: 4px;">Ask your documents anything</h1>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 14px; color: #7B8190; margin-bottom: 20px;">Search, reason, and answer using your private document knowledge base.</div>', unsafe_allow_html=True)

with col_head_right:
    st.markdown(f"""
        <div style="text-align: right; margin-top: 6px;">
            <span class="rf-badge-mint">● Knowledge base · {doc_count} doc(s)</span>
            <div style="font-size: 12px; color: #7B8190; margin-top: 4px;">{selected_provider.title()} · {selected_model}</div>
        </div>
    """, unsafe_allow_html=True)


# Session state for suggestion selection
if "input_question" not in st.session_state:
    st.session_state["input_question"] = ""

# 7. LARGE AI QUERY COMPOSER
with st.form(key="query_composer_form", clear_on_submit=False):
    user_query = st.text_area(
        "Ask anything about your documents...",
        value=st.session_state.get("input_question", ""),
        height=95,
        placeholder="Ask anything about your documents (e.g. What is the second project listed in the resume?)...",
        label_visibility="collapsed"
    )
    
    col_comp_left, col_comp_right = st.columns([3, 1])
    with col_comp_left:
        st.markdown(f"""
            <div style="font-size: 12px; color: #7B8190; margin-top: 8px;">
                <span style="color: #8B7CC8;">📄</span> {doc_count} Document(s) Indexed &nbsp;·&nbsp; 
                <span style="color: #4F8A6B;">●</span> {selected_provider.title()} ({selected_model})
            </div>
        """, unsafe_allow_html=True)
    with col_comp_right:
        submit_button = st.form_submit_button("Send Query ➔", use_container_width=True)


# 8. SUGGESTED QUERY CARDS (Shown before asking a question)
if "last_result" not in st.session_state:
    st.markdown('<div style="font-size: 11px; font-weight: 700; color: #7B8190; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 20px; margin-bottom: 12px;">SUGGESTED QUERIES</div>', unsafe_allow_html=True)
    
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        st.markdown('<div class="rf-sug-btn">', unsafe_allow_html=True)
        if st.button("✦ What are the main projects?", key="sug_p1", use_container_width=True):
            st.session_state["input_question"] = "What are the main projects?"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with s_col2:
        st.markdown('<div class="rf-sug-btn">', unsafe_allow_html=True)
        if st.button("≡ Summarize this document", key="sug_p2", use_container_width=True):
            st.session_state["input_question"] = "Summarize this document"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with s_col3:
        st.markdown('<div class="rf-sug-btn">', unsafe_allow_html=True)
        if st.button("◇ What skills are mentioned?", key="sug_p3", use_container_width=True):
            st.session_state["input_question"] = "What skills are mentioned?"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# 9. PROCESS QUERY SUBMISSION
if submit_button and user_query.strip():
    st.session_state["input_question"] = user_query.strip()
    with st.spinner("✦ Searching knowledge base & generating grounded answer..."):
        try:
            # Production dynamic retrieval (K=10 with parent section expansion & CrossEncoder reranking)
            result = pipeline.ask(user_query.strip(), k=10, provider=selected_provider, model_name=selected_model)
            st.session_state["last_result"] = result
            if "last_error" in st.session_state:
                del st.session_state["last_error"]
        except Exception as e:
            st.session_state["last_error"] = str(e)


# 10. ERROR DISPLAY STATE
if "last_error" in st.session_state:
    st.markdown(f"""
        <div style="background-color: #FCE8D8; border: 1px solid #E7E5EF; border-radius: 12px; padding: 18px 22px; margin-top: 20px;">
            <div style="font-size: 15px; font-weight: 600; color: #374151; margin-bottom: 4px;">Unable to generate answer</div>
            <div style="font-size: 13px; color: #7B8190;">Check that your selected AI service ({selected_provider.title()}) is active and try again.</div>
            <details style="margin-top: 8px; font-size: 12px; color: #374151;">
                <summary>Show technical details</summary>
                <code style="display:block; margin-top:4px; padding:8px; background:#FFFFFF; border-radius:6px;">{st.session_state["last_error"]}</code>
            </details>
        </div>
    """, unsafe_allow_html=True)


# 11. CONVERSATION, GROUNDED ANSWER & EVIDENCE WORKSPACE
if "last_result" in st.session_state:
    res = st.session_state["last_result"]
    
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)

    # User Question Card
    st.markdown(f"""
        <div class="rf-user-card">
            <div style="font-size: 11px; font-weight: 700; color: #8B7CC8; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px;">You</div>
            <div style="font-size: 15px; font-weight: 500; color: #374151;">{res['question']}</div>
        </div>
    """, unsafe_allow_html=True)

    # AI Grounded Answer Card
    st.markdown(f"""
        <div class="rf-ai-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div style="font-size: 14px; font-weight: 600; color: #374151; display: flex; align-items: center; gap: 6px;">
                    <span style="color: #8B7CC8;">✦</span> RAGFoundry
                </div>
                <span class="rf-badge-mint">✓ Grounded in your documents</span>
            </div>
            <div style="font-size: 15px; line-height: 1.65; color: #374151;">
                {res['answer']}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # EVIDENCE SECTION
    st.markdown('<h3 style="font-size: 16px; font-weight: 600; margin-top: 24px; margin-bottom: 12px;">Evidence</h3>', unsafe_allow_html=True)
    
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

    # COLLAPSIBLE RETRIEVED CONTEXT (FAISS & CROSS-ENCODER RERANKER)
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    with st.expander(f"▸ Retrieved context · {len(res['retrieved_chunks'])} chunks (FAISS & Two-Stage Reranker Scores)"):
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
