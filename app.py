import os
import json
import streamlit as st
from rag_pipeline import RAGPipeline
import db_manager

# 1. State & DB Initialization
db_manager.init_db()

if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

if "sidebar_state" not in st.session_state:
    st.session_state["sidebar_state"] = "expanded"

if "show_history_drawer" not in st.session_state:
    st.session_state["show_history_drawer"] = False

if "current_conversation_id" not in st.session_state:
    st.session_state["current_conversation_id"] = None

theme = st.session_state["theme"]
sidebar_state = st.session_state["sidebar_state"]
current_user_id = "user_default"

# 2. Page Setup
st.set_page_config(
    page_title="RAGFoundry — Local AI Document Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state=sidebar_state
)

# 3. Theme System Palettes
LIGHT_THEME = {
    "bg_main": "#F8F9FF",
    "bg_sidebar": "#F3F1FA",
    "bg_surface": "#FFFFFF",
    "bg_elevated": "#FCFBFF",
    "primary": "#8B7CC8",
    "primary_hover": "#7668B5",
    "primary_btn_text": "#FFFFFF",
    "soft_accent": "#EDE9F7",
    "info_bg": "#E4F0FF",
    "info_text": "#374151",
    "mint_bg": "#E1F8F0",
    "mint_text": "#4F8A6B",
    "peach_bg": "#FCE8D8",
    "peach_text": "#374151",
    "purple_soft_bg": "#EDE9F7",
    "purple_soft_text": "#7C68D9",
    "purple_soft_border": "rgba(124,104,217,0.2)",
    "text_main": "#374151",
    "text_sec": "#7B8190",
    "text_muted": "#9AA1AF",
    "border": "#E7E5EF",
    "code_bg": "#F8F7FC",
    "grid_color": "rgba(139, 124, 200, 0.055)",
    "drawer_bg": "#FFFFFF",
    "toggle_bg": "#FFFFFF",
    "toggle_border": "#E7E5EF",
    "toggle_color": "#6F638F",
    "upload_bg": "#FFFFFF",
    "upload_border": "#E7E5EF",
    "composer_bg": "#FFFFFF",
    "composer_border": "#E7E5EF",
    "sug_bg": "#FFFFFF",
    "sug_border": "#E7E5EF",
    "sug_text": "#374151",
    "sug_icon": "#8B7CC8",
    "sug_hover_bg": "#EDE9F7",
    "sug_hover_border": "#D9D1F0",
    "top_btn_bg": "#FFFFFF",
    "top_btn_border": "#E7E5EF",
    "top_btn_text": "#374151",
    "top_btn_hover_bg": "#EDE9F7",
    "top_btn_hover_border": "#6366F1",
}

DARK_THEME = {
    "bg_main": "#0B0F17",
    "bg_sidebar": "#111827",
    "bg_surface": "#1A2234",
    "bg_elevated": "#1E293B",
    "primary": "#6366F1",
    "primary_hover": "#4F46E5",
    "primary_btn_text": "#FFFFFF",
    "soft_accent": "#1E293B",
    "info_bg": "#161F30",
    "info_text": "#3B82F6",
    "mint_bg": "#064E3B",
    "mint_text": "#34D399",
    "peach_bg": "#30201C",
    "peach_text": "#FDBA9A",
    "purple_soft_bg": "#2E1E4F",
    "purple_soft_text": "#C084FC",
    "purple_soft_border": "rgba(192, 132, 252, 0.20)",
    "text_main": "#F8FAFC",
    "text_sec": "#94A3B8",
    "text_muted": "#64748B",
    "border": "#2D3748",
    "code_bg": "#111827",
    "grid_color": "rgba(99, 102, 241, 0.02)",
    "drawer_bg": "#111827",
    "toggle_bg": "#1E293B",
    "toggle_border": "#2D3748",
    "toggle_color": "#F8FAFC",
    "upload_bg": "#1E293B",
    "upload_border": "#475569",
    "composer_bg": "#111827",
    "composer_border": "#1F293D",
    "sug_bg": "#161F30",
    "sug_border": "#283548",
    "sug_text": "#E2E8F0",
    "sug_icon": "#C084FC",
    "sug_hover_bg": "#1E2B42",
    "sug_hover_border": "#3B82F6",
    "top_btn_bg": "#161F30",
    "top_btn_border": "#283548",
    "top_btn_text": "#E2E8F0",
    "top_btn_hover_bg": "#1E2B42",
    "top_btn_hover_border": "#3B82F6",
}

T = LIGHT_THEME if theme == "light" else DARK_THEME

# 4. Comprehensive Standardized CSS Injection
custom_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Hide Streamlit Default Chrome Header & Footer */
header[data-testid="stHeader"] {{ background-color: transparent !important; z-index: 100 !important; }}
footer {{ visibility: hidden; }}
[data-testid="stDecoration"] {{ display: none; }}
#MainMenu {{ visibility: hidden; }}

/* SINGLE Persistent Sidebar Toggle Control */
[data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"] {{
    display: flex !important;
    visibility: visible !important;
    background-color: {T['toggle_bg']} !important;
    border: 1px solid {T['toggle_border']} !important;
    border-radius: 12px !important;
    color: {T['toggle_color']} !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    position: fixed !important;
    top: 14px !important;
    left: 14px !important;
    z-index: 999999 !important;
    width: 44px !important;
    height: 44px !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
}}
[data-testid="collapsedControl"]:hover, [data-testid="stSidebarCollapseButton"]:hover {{
    background-color: {T['soft_accent']} !important;
    border-color: {T['primary']} !important;
    color: #FFFFFF !important;
}}

/* Global Theme Canvas */
html, body, .stApp {{
    background-color: {T['bg_main']} !important;
    background-image: radial-gradient({T['grid_color']} 1px, transparent 1px) !important;
    background-size: 24px 24px !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: {T['text_main']} !important;
}}

/* Sidebar Styling */
section[data-testid="stSidebar"] {{
    background-color: {T['bg_sidebar']} !important;
    border-right: 1px solid {T['border']} !important;
    width: 280px !important;
}}
section[data-testid="stSidebar"] > div {{
    padding: 1.2rem 1rem !important;
}}
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span {{
    color: {T['text_main']} !important;
}}

/* Main Container Width & Spacing */
.main .block-container {{
    max-width: 1050px !important;
    padding-top: 1.2rem !important;
    padding-bottom: 3rem !important;
    margin: 0 auto !important;
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Inter', sans-serif !important;
    color: {T['text_main']} !important;
    font-weight: 600 !important;
}}

/* Large AI Query Composer Styling */
.stTextArea textarea {{
    background-color: {T['composer_bg']} !important;
    border: 1px solid {T['composer_border']} !important;
    border-radius: 18px !important;
    color: {T['text_main']} !important;
    padding: 16px !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05) !important;
    resize: none !important;
}}
.stTextArea textarea::placeholder {{
    color: {T['text_sec']} !important;
    opacity: 1 !important;
}}
.stTextArea textarea:focus {{
    border-color: {T['primary']} !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15) !important;
}}

/* Form Submit Button Container & Circular Send Button (Extreme Right) */
div[data-testid="stFormSubmitButton"] {{
    display: flex !important;
    justify-content: flex-end !important;
}}
div[data-testid="stFormSubmitButton"] > button {{
    background-color: {T['primary']} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 50% !important;
    width: 44px !important;
    height: 44px !important;
    padding: 0px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 22px !important;
    font-weight: bold !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    transition: all 0.2s ease !important;
}}
div[data-testid="stFormSubmitButton"] > button:hover {{
    background-color: {T['primary_hover']} !important;
    color: #FFFFFF !important;
    transform: scale(1.05) !important;
}}

/* File Uploader Dropzone Styling */
div[data-testid="stFileUploaderDropzone"], section[data-testid="stFileUploaderDropzone"] {{
    background-color: {T['upload_bg']} !important;
    border: 1px dashed {T['upload_border']} !important;
    color: {T['text_main']} !important;
    border-radius: 12px !important;
    transition: all 0.2s ease !important;
}}
div[data-testid="stFileUploaderDropzone"]:hover {{
    background-color: #1E2B42 !important;
    border-color: #3B82F6 !important;
}}
div[data-testid="stFileUploaderDropzone"] *, div[data-testid="stFileUploader"] * {{
    color: {T['text_main']} !important;
}}
div[data-testid="stFileUploaderDropzone"] small {{
    color: {T['text_sec']} !important;
}}
div[data-testid="stFileUploaderDropzone"] button {{
    background-color: {T['primary']} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
}}
div[data-testid="stFileUploaderDropzone"] button:hover {{
    background-color: {T['primary_hover']} !important;
}}

/* Checkbox Styling */
div[data-baseweb="checkbox"] label span {{
    color: {T['text_main']} !important;
}}

/* Selectbox & Inputs */
.stSelectbox div[data-baseweb="select"] > div, .stTextInput > div > div > input {{
    background-color: {T['bg_surface']} !important;
    border: 1px solid {T['border']} !important;
    color: {T['text_main']} !important;
    border-radius: 10px !important;
}}

/* Custom Cards */
.rf-card {{
    background-color: {T['bg_surface']};
    border: 1px solid {T['border']};
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}}

.rf-user-card {{
    background-color: {T['bg_elevated']};
    border: 1px solid {T['border']};
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 16px;
    color: {T['text_main']};
}}

.rf-ai-card {{
    background-color: {T['bg_surface']};
    border: 1px solid {T['border']};
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}}

.rf-doc-card {{
    background-color: {T['bg_surface']};
    border: 1px solid {T['border']};
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s ease;
}}
.rf-doc-card:hover {{
    background-color: {T['soft_accent']};
    border-color: {T['info_text']};
}}

/* Badges */
.rf-badge-mint {{
    background-color: {T['mint_bg']};
    color: {T['mint_text']};
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 12px;
    display: inline-block;
}}

.rf-badge-purple {{
    background-color: {T['purple_soft_bg']};
    color: {T['purple_soft_text']};
    border: 1px solid {T['purple_soft_border']};
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 12px;
    display: inline-block;
}}

.rf-badge-blue {{
    background-color: {T['info_bg']};
    color: {T['info_text']};
    font-size: 11px;
    font-weight: 500;
    padding: 4px 10px;
    border-radius: 12px;
    display: inline-block;
}}

/* Standard Primary Action Buttons */
.rf-primary-btn button {{
    background-color: {T['primary']} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 8px 16px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    transition: all 0.2s ease !important;
}}
.rf-primary-btn button:hover {{
    background-color: {T['primary_hover']} !important;
    color: #FFFFFF !important;
}}

/* Standard Top-Right & Drawer Control Buttons */
.rf-top-btn button {{
    background-color: {T['top_btn_bg']} !important;
    color: {T['top_btn_text']} !important;
    border: 1px solid {T['top_btn_border']} !important;
    border-radius: 10px !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    transition: all 0.2s ease !important;
}}
.rf-top-btn button:hover {{
    background-color: {T['top_btn_hover_bg']} !important;
    border-color: {T['top_btn_hover_border']} !important;
    color: #F8FAFC !important;
}}

/* Standard Secondary Buttons */
.stButton > button {{
    background-color: {T['top_btn_bg']} !important;
    color: {T['top_btn_text']} !important;
    border: 1px solid {T['top_btn_border']} !important;
    border-radius: 10px !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    transition: all 0.2s ease !important;
}}
.stButton > button:hover {{
    background-color: {T['top_btn_hover_bg']} !important;
    border-color: {T['top_btn_hover_border']} !important;
    color: #F8FAFC !important;
}}

/* Suggested Query Secondary Cards */
.rf-sug-btn button {{
    background-color: {T['sug_bg']} !important;
    color: {T['sug_text']} !important;
    border: 1px solid {T['sug_border']} !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    text-align: left !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.03) !important;
}}
.rf-sug-btn button:hover {{
    border-color: {T['sug_hover_border']} !important;
    background-color: {T['sug_hover_bg']} !important;
    color: #F8FAFC !important;
}}

/* Streamlit Expander Styling */
div[data-testid="stExpander"] {{
    background-color: {T['sug_bg']} !important;
    border: 1px solid {T['sug_border']} !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}}
div[data-testid="stExpander"] summary {{
    color: {T['text_sec']} !important;
    font-weight: 500 !important;
}}

/* Sidebar Labels & Panels */
.rf-sidebar-label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: {T['text_sec']};
    text-transform: uppercase;
    margin-top: 18px;
    margin-bottom: 8px;
}}
.rf-status-panel {{
    background-color: {T['mint_bg']};
    color: {T['mint_text']};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 12px;
    font-weight: 500;
    margin-top: 24px;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 5. Helper Function to Get Documents List
def get_documents_info(data_folder="data"):
    if not os.path.exists(data_folder):
        return []
    files = os.listdir(data_folder)
    doc_list = []
    for f in files:
        file_path = os.path.join(data_folder, f)
        if os.path.isfile(file_path) and not f.endswith(".db"):
            size_kb = round(os.path.getsize(file_path) / 1024, 1)
            doc_list.append({"name": f, "size_kb": size_kb})
            db_manager.register_document(f, size_kb, current_user_id)
    return doc_list

documents_in_data = get_documents_info("data")
doc_count = len(documents_in_data)

# 6. SIDEBAR RENDERING (CLEAN BRANDING, WORKSPACE, DOCUMENTS & AI ENGINE)
with st.sidebar:
    # Clean Brand Header
    st.markdown(f"""
        <div style='margin-bottom: 20px;'>
            <div style='font-size: 20px; font-weight: 700; color: {T["text_main"]}; display: flex; align-items: center; gap: 8px;'>
                <span style='color: {T["primary"]};'>✦</span> RAGFoundry
            </div>
            <div style='font-size: 12px; color: {T["text_sec"]}; margin-top: 2px;'>Local AI Document Intelligence</div>
        </div>
    """, unsafe_allow_html=True)

    # WORKSPACE SECTION
    st.markdown('<div class="rf-sidebar-label">WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 13px; font-weight: 600; color: {T["text_main"]}; margin-bottom: 10px;">Documents &nbsp;·&nbsp; {doc_count}</div>', unsafe_allow_html=True)

    if doc_count > 0:
        for doc in documents_in_data:
            st.markdown(f"""
                <div class="rf-doc-card">
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 160px;">
                        <span style="color: {T["text_main"]};">📄</span> 
                        <span style="font-size: 13px; font-weight: 500; color: {T["text_main"]};">{doc['name']}</span>
                    </div>
                    <span class="rf-badge-mint">✓ Indexed</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size: 12px; color: {T["text_sec"]}; margin-bottom: 10px;">No documents uploaded yet.</div>', unsafe_allow_html=True)

    # Upload Controls
    clear_existing = st.checkbox("Clear old documents on upload", value=True)
    uploaded_files = st.file_uploader("Upload .txt or .pdf files", type=["txt", "pdf"], accept_multiple_files=True, label_visibility="collapsed")
    
    if uploaded_files:
        os.makedirs("data", exist_ok=True)
        if clear_existing:
            for existing_file in os.listdir("data"):
                file_path_to_remove = os.path.join("data", existing_file)
                if os.path.isfile(file_path_to_remove) and not existing_file.endswith(".db"):
                    os.remove(file_path_to_remove)

        for file in uploaded_files:
            file_path = os.path.join("data", file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        st.markdown(f'<div class="rf-badge-mint" style="margin-top:6px;">✓ Saved {len(uploaded_files)} file(s)</div>', unsafe_allow_html=True)
        if "pipeline" in st.session_state:
            del st.session_state["pipeline"]
        st.rerun()

    # Re-Index Button (Primary Lavender/Iris Style)
    st.markdown('<div class="rf-primary-btn" style="margin-top: 10px;">', unsafe_allow_html=True)
    if st.button("🔄 Re-Index Documents", use_container_width=True):
        if "pipeline" in st.session_state:
            del st.session_state["pipeline"]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<hr style='border:none; border-top:1px solid {T['border']}; margin:16px 0;'>", unsafe_allow_html=True)

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
        st.markdown(f'<div style="font-size:12px; color:{T["mint_text"]}; margin-top:4px;">● Local AI Active</div>', unsafe_allow_html=True)
    else:
        selected_provider = "gemini"
        selected_model = "gemini-2.0-flash"
        user_api_key = st.text_input("Gemini API Key (Optional)", type="password", help="Overrides default API Key")
        if user_api_key:
            os.environ["GEMINI_API_KEY"] = user_api_key.strip()
            st.markdown(f'<div style="font-size:12px; color:{T["mint_text"]}; margin-top:4px;">✓ Custom Key Applied</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:12px; color:{T["primary"]}; margin-top:4px;">● Gemini Cloud Active</div>', unsafe_allow_html=True)

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
            <div class="rf-status-panel" style="background-color:{T['peach_bg']}; color:{T['peach_text']};">
                ● No documents indexed<br>
                <span style="font-size: 11px; font-weight: 400; opacity: 0.85;">Upload a PDF or TXT above</span>
            </div>
        """, unsafe_allow_html=True)


# 7. INITIALIZE RAG PIPELINE (Session Cached)
if "pipeline" not in st.session_state:
    with st.spinner("Initializing RAG Engine & Indexing Documents..."):
        st.session_state["pipeline"] = RAGPipeline("data")

pipeline = st.session_state["pipeline"]


# 8. MAIN WORKSPACE TOP HEADER (TOP-RIGHT CONTROLS: HISTORY & THEME)
col_head_left, col_head_right = st.columns([3, 2])

with col_head_left:
    st.markdown('<span class="rf-badge-purple">DOCUMENT INTELLIGENCE</span>', unsafe_allow_html=True)
    st.markdown(f'<h1 style="font-size: 32px; margin-top: 6px; margin-bottom: 4px; color: {T["text_main"]};">Ask your documents anything</h1>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 14px; color: {T["text_sec"]}; margin-bottom: 16px;">Search, reason, and answer using your private document knowledge base.</div>', unsafe_allow_html=True)

with col_head_right:
    # TOP-RIGHT CONTROLS: HISTORY + THEME TOGGLE
    ctrl_col1, ctrl_col2 = st.columns(2)
    with ctrl_col1:
        hist_btn_text = "× Close History" if st.session_state["show_history_drawer"] else "◷ History"
        st.markdown('<div class="rf-top-btn">', unsafe_allow_html=True)
        if st.button(hist_btn_text, key="top_history_btn", use_container_width=True):
            st.session_state["show_history_drawer"] = not st.session_state["show_history_drawer"]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
            
    with ctrl_col2:
        theme_btn_label = "☾ Dark Mode" if theme == "light" else "☀ Light Mode"
        st.markdown('<div class="rf-top-btn">', unsafe_allow_html=True)
        if st.button(theme_btn_label, key="top_theme_btn", use_container_width=True):
            st.session_state["theme"] = "dark" if theme == "light" else "light"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div style="text-align: right; margin-top: 8px;">
            <span class="rf-badge-mint">● Knowledge base · {doc_count} doc(s)</span>
            <div style="font-size: 12px; color: {T['text_sec']}; margin-top: 4px;">{selected_provider.title()} · {selected_model}</div>
        </div>
    """, unsafe_allow_html=True)


# 9. HISTORY DRAWER PANEL (Expands on Right Top Side when active)
if st.session_state["show_history_drawer"]:
    st.markdown(f"""
        <div style="background-color: {T['drawer_bg']}; border: 1px solid {T['border']}; border-radius: 14px; padding: 18px 22px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="font-size: 16px; font-weight: 700; color: {T['text_main']};">◷ Saved Conversations</div>
            </div>
    """, unsafe_allow_html=True)
    
    h_col1, h_col2 = st.columns([1, 3])
    with h_col1:
        st.markdown('<div class="rf-primary-btn">', unsafe_allow_html=True)
        if st.button("+ New Conversation", key="drawer_new_chat", use_container_width=True):
            st.session_state["current_conversation_id"] = None
            st.session_state["input_question"] = ""
            st.session_state["show_history_drawer"] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    grouped_convs = db_manager.get_user_conversations_grouped(current_user_id)
    
    for group_name, convs in grouped_convs.items():
        if convs:
            st.markdown(f'<div style="font-size: 11px; font-weight: 700; color: {T["text_sec"]}; letter-spacing: 0.8px; margin-top: 12px; margin-bottom: 6px;">{group_name}</div>', unsafe_allow_html=True)
            for c in convs:
                if st.button(f"💬 {c['title']}", key=f"conv_{c['id']}", use_container_width=True):
                    st.session_state["current_conversation_id"] = c["id"]
                    st.session_state["show_history_drawer"] = False
                    st.rerun()
                    
    st.markdown('</div>', unsafe_allow_html=True)


# Session state for prompt inputs
if "input_question" not in st.session_state:
    st.session_state["input_question"] = ""

# 10. LARGE AI QUERY COMPOSER WITH CIRCULAR SEND BUTTON INSIDE (HORIZONTAL RIGHT ARROW ➔)
with st.form(key="query_composer_form", clear_on_submit=False):
    user_query = st.text_area(
        "Ask anything about your documents...",
        value=st.session_state.get("input_question", ""),
        height=105,
        placeholder="Ask anything about your documents (e.g. What is the second project listed in the resume?)...",
        label_visibility="collapsed"
    )
    
    col_comp_left, col_comp_right = st.columns([4, 1])
    with col_comp_left:
        st.markdown(f"""
            <div style="font-size: 12px; color: {T['text_sec']}; margin-top: 10px;">
                <span style="color: {T['primary']};">📄</span> {doc_count} Document(s) Indexed &nbsp;·&nbsp; 
                <span style="color: {T['mint_text']};">●</span> {selected_provider.title()} ({selected_model})
            </div>
        """, unsafe_allow_html=True)
    with col_comp_right:
        # Circular Send Button with Horizontal Right Arrow ➔
        submit_button = st.form_submit_button("➔", use_container_width=False)


# 11. SUGGESTED QUERY CARDS (Shown when starting a fresh chat)
if not st.session_state["current_conversation_id"] and "last_result" not in st.session_state:
    st.markdown(f'<div style="font-size: 11px; font-weight: 700; color: {T["text_sec"]}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 20px; margin-bottom: 12px;">SUGGESTED QUERIES</div>', unsafe_allow_html=True)
    
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


# 12. PROCESS QUERY SUBMISSION & PERSISTENT AUTO-SAVE TO DATABASE
if submit_button and user_query.strip():
    question_text = user_query.strip()
    st.session_state["input_question"] = ""
    
    # 1. Active conversation check or create new
    conv_id = st.session_state.get("current_conversation_id")
    if not conv_id:
        title = db_manager.generate_conversation_title(question_text)
        conv_id = db_manager.create_conversation(current_user_id, title)
        st.session_state["current_conversation_id"] = conv_id
        
    # 2. Save user message to Database
    db_manager.save_message(conv_id, "user", question_text)
    
    # 3. Run RAG Pipeline
    with st.spinner("✦ Searching knowledge base & generating grounded answer..."):
        try:
            result = pipeline.ask(question_text, k=10, provider=selected_provider, model_name=selected_model)
            
            # 4. Auto-save AI Grounded Answer to Database
            db_manager.save_message(
                conv_id, 
                "assistant", 
                result["answer"], 
                sources=result["sources"], 
                chunks=result["retrieved_chunks"]
            )
            st.session_state["last_result"] = result
            if "last_error" in st.session_state:
                del st.session_state["last_error"]
        except Exception as e:
            st.session_state["last_error"] = str(e)
            
    st.rerun()


# 13. ERROR DISPLAY STATE
if "last_error" in st.session_state:
    st.markdown(f"""
        <div style="background-color: {T['peach_bg']}; border: 1px solid {T['border']}; border-radius: 12px; padding: 18px 22px; margin-top: 20px;">
            <div style="font-size: 15px; font-weight: 600; color: {T['text_main']}; margin-bottom: 4px;">Unable to generate answer</div>
            <div style="font-size: 13px; color: {T['text_sec']};">Check that your selected AI service ({selected_provider.title()}) is active and try again.</div>
            <details style="margin-top: 8px; font-size: 12px; color: {T['text_main']};">
                <summary>Show technical details</summary>
                <code style="display:block; margin-top:4px; padding:8px; background:{T['bg_surface']}; border-radius:6px; color:{T['text_main']};">{st.session_state["last_error"]}</code>
            </details>
        </div>
    """, unsafe_allow_html=True)


# 14. DISPLAY PERSISTENT MULTI-TURN CONVERSATION FROM DATABASE
active_conv_id = st.session_state.get("current_conversation_id")

if active_conv_id:
    saved_messages = db_manager.get_conversation_messages(active_conv_id)
    
    if saved_messages:
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        
        for msg in saved_messages:
            if msg["role"] == "user":
                # User Prompt Card
                st.markdown(f"""
                    <div class="rf-user-card">
                        <div style="font-size: 11px; font-weight: 700; color: {T['primary']}; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px;">You</div>
                        <div style="font-size: 15px; font-weight: 500; color: {T['text_main']};">{msg['content']}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # AI Grounded Answer Card
                st.markdown(f"""
                    <div class="rf-ai-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <div style="font-size: 14px; font-weight: 600; color: {T['text_main']}; display: flex; align-items: center; gap: 6px;">
                                <span style="color: {T['primary']};">✦</span> RAGFoundry
                            </div>
                            <span class="rf-badge-mint">✓ Grounded in your documents</span>
                        </div>
                        <div style="font-size: 15px; line-height: 1.65; color: {T['text_main']};">
                            {msg['content']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # EVIDENCE SECTION
                if msg.get("sources"):
                    st.markdown(f'<h3 style="font-size: 16px; font-weight: 600; margin-top: 20px; margin-bottom: 12px; color: {T["text_main"]};">Evidence</h3>', unsafe_allow_html=True)
                    src_cols = st.columns(min(len(msg["sources"]), 3) or 1)
                    for idx, src in enumerate(msg["sources"]):
                        col_target = src_cols[idx % len(src_cols)]
                        with col_target:
                            st.markdown(f"""
                                <div class="rf-card" style="padding: 12px 16px; margin-bottom: 12px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="font-size: 13px; font-weight: 600; color: {T['text_main']};">📄 {src}</span>
                                        <span class="rf-badge-blue">Relevant source</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                # COLLAPSIBLE RETRIEVED CONTEXT
                if msg.get("chunks"):
                    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
                    with st.expander(f"▸ Retrieved context · {len(msg['chunks'])} chunks (FAISS & Two-Stage Reranker Scores)"):
                        for rank, chunk in enumerate(msg["chunks"]):
                            rerank_score = chunk.get("rerank_score", None)
                            score_display = f"Rerank Score: `{rerank_score:.4f}`" if rerank_score is not None else f"Distance: `{chunk['distance_score']:.4f}`"
                            
                            st.markdown(f"""
                                <div style="background-color: {T['bg_surface']}; border: 1px solid {T['border']}; border-radius: 10px; padding: 14px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                        <span class="rf-badge-purple">Rank {rank+1}</span>
                                        <span style="font-size: 12px; color: {T['text_sec']};">{score_display} &nbsp;·&nbsp; 📄 {chunk['filename']}</span>
                                    </div>
                                    <div style="font-size: 13px; font-family: monospace; background-color: {T['code_bg']}; padding: 10px; border-radius: 6px; color: {T['text_main']}; white-space: pre-wrap;">
{chunk['text']}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
