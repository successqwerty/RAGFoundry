import os
import streamlit as st
from rag_pipeline import RAGPipeline

# 1. State Initialization
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

theme = st.session_state["theme"]

# 2. Page Configuration
st.set_page_config(
    page_title="RAGFoundry — Local AI Document Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3. Dynamic Theme Tokens & CSS Injection
if theme == "light":
    bg_main = "#F8F7FC"
    bg_sidebar = "#F1EFFA"
    bg_surface = "#FFFFFF"
    bg_elevated = "#FCFBFF"
    primary_color = "#8B7CC8"
    primary_hover = "#7668B5"
    soft_lavender = "#EDE9F7"
    powder_blue = "#DCEAF7"
    bg_mint = "#DDF3E8"
    text_mint = "#4F8A6B"
    bg_peach = "#FCE8D8"
    text_main = "#374151"
    text_sec = "#7B8190"
    text_muted = "#9AA1AF"
    border_color = "#E7E5EF"
    code_bg = "#F8F7FC"
else: # dark
    bg_main = "#0F1117"
    bg_sidebar = "#0B0D12"
    bg_surface = "#171A23"
    bg_elevated = "#1C202B"
    primary_color = "#A78BFA"
    primary_hover = "#8B7CF6"
    soft_lavender = "#242033"
    powder_blue = "#93C5FD"
    bg_mint = "#142A21"
    text_mint = "#86E3B3"
    bg_peach = "#30201C"
    text_main = "#F3F4F6"
    text_sec = "#A7ADBB"
    text_muted = "#737B8C"
    border_color = "#292E3A"
    code_bg = "#11141C"

custom_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Hide Default Header & Footer Chrome */
header[data-testid="stHeader"] {{ visibility: hidden; height: 0px; }}
footer {{ visibility: hidden; }}
[data-testid="stDecoration"] {{ display: none; }}
#MainMenu {{ visibility: hidden; }}

/* Persistent Sidebar Open/Close Toggle Control */
[data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"] {{
    display: flex !important;
    visibility: visible !important;
    background-color: {bg_surface} !important;
    border: 1px solid {border_color} !important;
    border-radius: 10px !important;
    color: {primary_color} !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12) !important;
    position: fixed !important;
    top: 14px !important;
    left: 14px !important;
    z-index: 999999 !important;
    width: 38px !important;
    height: 38px !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
}}
[data-testid="collapsedControl"]:hover, [data-testid="stSidebarCollapseButton"]:hover {{
    background-color: {soft_lavender} !important;
    color: {primary_color} !important;
}}

/* Global Theme Colors */
html, body, .stApp {{
    background-color: {bg_main} !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: {text_main} !important;
}}

/* Sidebar Styling */
section[data-testid="stSidebar"] {{
    background-color: {bg_sidebar} !important;
    border-right: 1px solid {border_color} !important;
    width: 270px !important;
}}
section[data-testid="stSidebar"] > div {{
    padding: 1.5rem 1rem !important;
}}

/* Main Container Width */
.main .block-container {{
    max-width: 1050px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    margin: 0 auto !important;
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Inter', sans-serif !important;
    color: {text_main} !important;
    font-weight: 600 !important;
}}

/* Large AI Query Composer Styling */
.stTextArea textarea {{
    background-color: {bg_surface} !important;
    border: 1px solid {border_color} !important;
    border-radius: 16px !important;
    color: {text_main} !important;
    padding: 16px !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
    resize: none !important;
}}
.stTextArea textarea:focus {{
    border-color: {primary_color} !important;
    box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.2) !important;
}}

/* Custom Workspace Cards */
.rf-card {{
    background-color: {bg_surface};
    border: 1px solid {border_color};
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}}

.rf-user-card {{
    background-color: {soft_lavender};
    border: 1px solid {border_color};
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 16px;
    color: {text_main};
}}

.rf-ai-card {{
    background-color: {bg_surface};
    border: 1px solid {border_color};
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}}

.rf-doc-card {{
    background-color: {bg_surface};
    border: 1px solid {border_color};
    border-radius: 10px;
    padding: 8px 12px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

/* Badges */
.rf-badge-mint {{
    background-color: {bg_mint};
    color: {text_mint};
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 12px;
    display: inline-block;
}}

.rf-badge-lavender {{
    background-color: {soft_lavender};
    color: {primary_color};
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 12px;
    display: inline-block;
}}

.rf-badge-blue {{
    background-color: {powder_blue};
    color: {text_main};
    font-size: 11px;
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 12px;
    display: inline-block;
}}

/* Primary Buttons */
.stButton > button {{
    background-color: {primary_color} !important;
    color: {bg_main} !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 8px 18px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: background-color 0.2s ease !important;
}}
.stButton > button:hover {{
    background-color: {primary_hover} !important;
    color: {bg_main} !important;
}}

/* Secondary Buttons */
.rf-secondary-btn button {{
    background-color: {bg_surface} !important;
    color: {text_main} !important;
    border: 1px solid {border_color} !important;
    border-radius: 10px !important;
}}
.rf-secondary-btn button:hover {{
    background-color: {soft_lavender} !important;
}}

/* Suggested Queries White Cards */
.rf-sug-btn button {{
    background-color: {bg_surface} !important;
    color: {text_main} !important;
    border: 1px solid {border_color} !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    text-align: left !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.03) !important;
}}
.rf-sug-btn button:hover {{
    border-color: {primary_color} !important;
    background-color: {soft_lavender} !important;
    color: {text_main} !important;
}}

/* Streamlit Expander Styling */
div[data-testid="stExpander"] {{
    background-color: {bg_surface} !important;
    border: 1px solid {border_color} !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}}
div[data-testid="stExpander"] summary {{
    color: {text_sec} !important;
    font-weight: 500 !important;
}}

/* Sidebar Labels */
.rf-sidebar-label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: {text_sec};
    text-transform: uppercase;
    margin-top: 18px;
    margin-bottom: 8px;
}}

/* System Status Panel */
.rf-status-panel {{
    background-color: {bg_mint};
    color: {text_mint};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 12px;
    font-weight: 500;
    margin-top: 24px;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 4. Helper Function to Get Documents List
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

# 5. SIDEBAR RENDERING (WORKSPACE & MODEL)
with st.sidebar:
    # Branding
    st.markdown(f"""
        <div style='margin-bottom: 20px;'>
            <div style='font-size: 20px; font-weight: 700; color: {text_main}; display: flex; align-items: center; gap: 8px;'>
                <span style='color: {primary_color};'>✦</span> RAGFoundry
            </div>
            <div style='font-size: 12px; color: {text_sec}; margin-top: 2px;'>Local AI Document Intelligence</div>
        </div>
    """, unsafe_allow_html=True)

    # WORKSPACE SECTION
    st.markdown('<div class="rf-sidebar-label">WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 13px; font-weight: 600; color: {text_main}; margin-bottom: 10px;">Documents &nbsp;·&nbsp; {doc_count}</div>', unsafe_allow_html=True)

    if doc_count > 0:
        for doc in documents_in_data:
            st.markdown(f"""
                <div class="rf-doc-card">
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 160px;">
                        <span style="color: {primary_color};">📄</span> 
                        <span style="font-size: 13px; font-weight: 500; color: {text_main};">{doc['name']}</span>
                    </div>
                    <span class="rf-badge-mint">✓ Indexed</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size: 12px; color: {text_sec}; margin-bottom: 10px;">No documents uploaded yet.</div>', unsafe_allow_html=True)

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

    st.markdown(f"<hr style='border:none; border-top:1px solid {border_color}; margin:16px 0;'>", unsafe_allow_html=True)

    # AI ENGINE SECTION
    st.markdown('<div class="rf-sidebar-label">AI ENGINE</div>', unsafe_allow_html=True)
    provider_choice = st.selectbox(
        "Select Provider",
        ["Ollama (100% Offline Local)", "Gemini (Cloud)"],
        label_visibility="collapsed"
    )
    
    if provider_choice == "Ollama (100% Offline Local)":
        selected_provider = "ollama"
        selected_model = st.text_input("Model Name", value="llama3.2", help="e.g. llama3.2, mistral")
        st.markdown(f'<div style="font-size:12px; color:{text_mint}; margin-top:4px;">● Local AI Active</div>', unsafe_allow_html=True)
    else:
        selected_provider = "gemini"
        selected_model = "gemini-2.0-flash"
        user_api_key = st.text_input("Gemini API Key (Optional)", type="password", help="Overrides default API Key")
        if user_api_key:
            os.environ["GEMINI_API_KEY"] = user_api_key.strip()
            st.markdown(f'<div style="font-size:12px; color:{text_mint}; margin-top:4px;">✓ Custom Key Applied</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:12px; color:{primary_color}; margin-top:4px;">● Gemini Cloud Active</div>', unsafe_allow_html=True)

    # SYSTEM STATUS PANEL
    if doc_count > 0:
        st.markdown(f"""
            <div class="rf-status-panel">
                ● System ready<br>
                <span style="font-size: 11px; font-weight: 400; opacity: 0.85;">{doc_count} document(s) indexed</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="rf-status-panel" style="background-color:{bg_peach}; color:{text_main};">
                ● No documents indexed<br>
                <span style="font-size: 11px; font-weight: 400; opacity: 0.85;">Upload a PDF or TXT above</span>
            </div>
        """, unsafe_allow_html=True)


# 6. INITIALIZE RAG PIPELINE (Session Cached)
if "pipeline" not in st.session_state:
    with st.spinner("Initializing RAG Engine & Indexing Documents..."):
        st.session_state["pipeline"] = RAGPipeline("data")

pipeline = st.session_state["pipeline"]


# 7. MAIN WORKSPACE CONTENT

# Top Header Layout with Theme Toggle
col_head_left, col_head_right = st.columns([3, 1])

with col_head_left:
    st.markdown('<span class="rf-badge-lavender">DOCUMENT INTELLIGENCE</span>', unsafe_allow_html=True)
    st.markdown(f'<h1 style="font-size: 32px; margin-top: 6px; margin-bottom: 4px; color: {text_main};">Ask your documents anything</h1>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 14px; color: {text_sec}; margin-bottom: 20px;">Search, reason, and answer using your private document knowledge base.</div>', unsafe_allow_html=True)

with col_head_right:
    # Theme Toggle Control Button
    theme_btn_label = "☾ Dark Mode" if theme == "light" else "☀ Light Mode"
    st.markdown('<div class="rf-secondary-btn" style="text-align: right; margin-bottom: 8px;">', unsafe_allow_html=True)
    if st.button(theme_btn_label, key="theme_toggle_btn", use_container_width=False):
        st.session_state["theme"] = "dark" if theme == "light" else "light"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div style="text-align: right;">
            <span class="rf-badge-mint">● Knowledge base · {doc_count} doc(s)</span>
            <div style="font-size: 12px; color: {text_sec}; margin-top: 4px;">{selected_provider.title()} · {selected_model}</div>
        </div>
    """, unsafe_allow_html=True)


# Session state for suggested query population
if "input_question" not in st.session_state:
    st.session_state["input_question"] = ""

# 8. LARGE AI QUERY COMPOSER
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
            <div style="font-size: 12px; color: {text_sec}; margin-top: 8px;">
                <span style="color: {primary_color};">📄</span> {doc_count} Document(s) Indexed &nbsp;·&nbsp; 
                <span style="color: {text_mint};">●</span> {selected_provider.title()} ({selected_model})
            </div>
        """, unsafe_allow_html=True)
    with col_comp_right:
        submit_button = st.form_submit_button("Send Query ➔", use_container_width=True)


# 9. SUGGESTED QUERY CARDS (Shown before asking a question)
if "last_result" not in st.session_state:
    st.markdown(f'<div style="font-size: 11px; font-weight: 700; color: {text_sec}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 20px; margin-bottom: 12px;">SUGGESTED QUERIES</div>', unsafe_allow_html=True)
    
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


# 10. PROCESS QUERY SUBMISSION
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


# 11. ERROR DISPLAY STATE
if "last_error" in st.session_state:
    st.markdown(f"""
        <div style="background-color: {bg_peach}; border: 1px solid {border_color}; border-radius: 12px; padding: 18px 22px; margin-top: 20px;">
            <div style="font-size: 15px; font-weight: 600; color: {text_main}; margin-bottom: 4px;">Unable to generate answer</div>
            <div style="font-size: 13px; color: {text_sec};">Check that your selected AI service ({selected_provider.title()}) is active and try again.</div>
            <details style="margin-top: 8px; font-size: 12px; color: {text_main};">
                <summary>Show technical details</summary>
                <code style="display:block; margin-top:4px; padding:8px; background:{bg_surface}; border-radius:6px; color:{text_main};">{st.session_state["last_error"]}</code>
            </details>
        </div>
    """, unsafe_allow_html=True)


# 12. CONVERSATION, GROUNDED ANSWER & EVIDENCE WORKSPACE
if "last_result" in st.session_state:
    res = st.session_state["last_result"]
    
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)

    # User Question Card
    st.markdown(f"""
        <div class="rf-user-card">
            <div style="font-size: 11px; font-weight: 700; color: {primary_color}; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px;">You</div>
            <div style="font-size: 15px; font-weight: 500; color: {text_main};">{res['question']}</div>
        </div>
    """, unsafe_allow_html=True)

    # AI Grounded Answer Card
    st.markdown(f"""
        <div class="rf-ai-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div style="font-size: 14px; font-weight: 600; color: {text_main}; display: flex; align-items: center; gap: 6px;">
                    <span style="color: {primary_color};">✦</span> RAGFoundry
                </div>
                <span class="rf-badge-mint">✓ Grounded in your documents</span>
            </div>
            <div style="font-size: 15px; line-height: 1.65; color: {text_main};">
                {res['answer']}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # EVIDENCE SECTION
    st.markdown(f'<h3 style="font-size: 16px; font-weight: 600; margin-top: 24px; margin-bottom: 12px; color: {text_main};">Evidence</h3>', unsafe_allow_html=True)
    
    src_cols = st.columns(min(len(res["sources"]), 3) or 1)
    for idx, src in enumerate(res["sources"]):
        col_target = src_cols[idx % len(src_cols)]
        with col_target:
            st.markdown(f"""
                <div class="rf-card" style="padding: 12px 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 13px; font-weight: 600; color: {text_main};">📄 {src}</span>
                        <span class="rf-badge-blue">Relevant source</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # COLLAPSIBLE RETRIEVED CONTEXT (FAISS & CROSS-ENCODER RERANKER)
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    with st.expander(f"▸ Retrieved context · {len(res['retrieved_chunks'])} chunks (FAISS & Two-Stage Reranker Scores)"):
        st.markdown(f'<div style="font-size: 12px; color: {text_sec}; margin-bottom: 12px;">The following text chunks were retrieved by FAISS and re-scored by the Cross-Encoder model:</div>', unsafe_allow_html=True)
        
        for rank, chunk in enumerate(res["retrieved_chunks"]):
            rerank_score = chunk.get("rerank_score", None)
            score_display = f"Rerank Score: `{rerank_score:.4f}`" if rerank_score is not None else f"Distance: `{chunk['distance_score']:.4f}`"
            
            st.markdown(f"""
                <div style="background-color: {bg_surface}; border: 1px solid {border_color}; border-radius: 10px; padding: 14px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span class="rf-badge-lavender">Rank {rank+1}</span>
                        <span style="font-size: 12px; color: {text_sec};">{score_display} &nbsp;·&nbsp; 📄 {chunk['filename']}</span>
                    </div>
                    <div style="font-size: 13px; font-family: monospace; background-color: {code_bg}; padding: 10px; border-radius: 6px; color: {text_main}; white-space: pre-wrap;">
{chunk['text']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
