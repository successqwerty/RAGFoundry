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

# 3. Standardized Design Tokens for Light & Dark Mode according to User Specifications
LIGHT_THEME = {
    "bg_main": "#F8FAFC",
    "bg_sidebar": "#F1F5F9",
    "border_sidebar": "#E2E8F0",
    "bg_surface": "#FFFFFF",
    "bg_elevated": "#FFFFFF",
    "border_card": "#E2E8F0",
    "text_main": "#0F172A",
    "text_sec": "#64748B",
    "text_muted": "#94A3B8",
    "border": "#E2E8F0",
    "code_bg": "#F8FAFC",
    "grid_color": "rgba(124, 58, 237, 0.03)",
    "drawer_bg": "#FFFFFF",
    "upload_container_bg": "#FFFFFF",
    "upload_container_border": "#E2E8F0",
    "composer_bg": "#FFFFFF",
    "composer_border": "#E2E8F0",
    "composer_focus_border": "#7C3AED",
    
    # Document Intelligence Badge
    "badge_bg": "#F3E8FF",
    "badge_border": "#D8CCF5",
    "badge_text": "#6D3FB3",
    
    # Non-Sidebar Utility & Suggested Query Buttons
    "btn_lavender_bg": "#F5EEFD",
    "btn_lavender_border": "#D8CCF5",
    "btn_lavender_text": "#5B3A8E",
    "btn_lavender_icon": "#5B3A8E",
    "btn_lavender_hover_bg": "#EEE4FA",
    "btn_lavender_hover_border": "#BFA7EA",
    "btn_lavender_hover_text": "#4C2A7A",
    "btn_lavender_hover_icon": "#4C2A7A",
    
    # Send Query Button (Primary Action)
    "btn_primary_bg": "#7C3AED",
    "btn_primary_text": "#FFFFFF",
    "btn_primary_icon": "#FFFFFF",
    "btn_primary_hover_bg": "#6D28D9",
    "btn_primary_hover_text": "#FFFFFF",
    
    # Sidebar Independent Controls
    "upload_btn_bg": "#FFFFFF",
    "upload_btn_border": "#E2E8F0",
    "upload_btn_text": "#334155",
    "upload_btn_icon": "#7C3AED",
    "upload_btn_hover_bg": "#F8FAFC",
    "upload_btn_hover_border": "#7C3AED",
    "upload_btn_hover_text": "#0F172A",
    "upload_btn_hover_icon": "#6D28D9",

    "reindex_bg": "#F5EEFD",
    "reindex_border": "#D8CCF5",
    "reindex_text": "#5B3A8E",
    "reindex_icon": "#5B3A8E",
    "reindex_hover_bg": "#EEE4FA",
    "reindex_hover_border": "#BFA7EA",
    "reindex_hover_text": "#4C2A7A",
    
    "mint_bg": "#ECFDF5",
    "mint_text": "#047857",
    "peach_bg": "#FCE8D8",
    "peach_text": "#24324A",
    "info_bg": "#F3E8FF",
    "info_text": "#6D3FB3",
}

DARK_THEME = {
    "bg_main": "#0B0E14",
    "bg_sidebar": "#111622",
    "border_sidebar": "#1E293B",
    "bg_surface": "#141B2B",
    "bg_elevated": "#141B2B",
    "border_card": "#242E42",
    "text_main": "#F8FAFC",
    "text_sec": "#94A3B8",
    "text_muted": "#64748B",
    "border": "#242E42",
    "code_bg": "#111622",
    "grid_color": "rgba(139, 92, 246, 0.02)",
    "drawer_bg": "#111622",
    "upload_container_bg": "#141B2B",
    "upload_container_border": "#242E42",
    "composer_bg": "#141B2B",
    "composer_border": "#242E42",
    "composer_focus_border": "#8B5CF6",
    
    # Document Intelligence Badge
    "badge_bg": "#2A1B4E",
    "badge_border": "#4C2889",
    "badge_text": "#D8B4FE",
    
    # Non-Sidebar Utility & Suggested Query Buttons (NO WHITE BACKGROUNDS IN DARK MODE)
    "btn_lavender_bg": "#1F1735",
    "btn_lavender_border": "#3E2968",
    "btn_lavender_text": "#E9D5FF",
    "btn_lavender_icon": "#E9D5FF",
    "btn_lavender_hover_bg": "#2E1F4D",
    "btn_lavender_hover_border": "#6D28D9",
    "btn_lavender_hover_text": "#FFFFFF",
    "btn_lavender_hover_icon": "#FFFFFF",
    
    # Send Query Button (Primary Action in Dark Mode)
    "btn_primary_bg": "#8B5CF6",
    "btn_primary_text": "#FFFFFF",
    "btn_primary_icon": "#FFFFFF",
    "btn_primary_hover_bg": "#7C3AED",
    "btn_primary_hover_text": "#FFFFFF",
    
    # Sidebar Independent Controls (Prevents White-on-White Bug)
    "upload_btn_bg": "#1E293B",
    "upload_btn_border": "#334155",
    "upload_btn_text": "#CBD5E1",
    "upload_btn_icon": "#8B5CF6",
    "upload_btn_hover_bg": "#2A364F",
    "upload_btn_hover_border": "#8B5CF6",
    "upload_btn_hover_text": "#FFFFFF",
    "upload_btn_hover_icon": "#8B5CF6",

    "reindex_bg": "#1E293B",
    "reindex_border": "#334155",
    "reindex_text": "#CBD5E1",
    "reindex_icon": "#8B5CF6",
    "reindex_hover_bg": "#2A364F",
    "reindex_hover_border": "#8B5CF6",
    "reindex_hover_text": "#FFFFFF",
    
    "mint_bg": "#064E3B",
    "mint_text": "#34D399",
    "peach_bg": "#30201C",
    "peach_text": "#F87171",
    "info_bg": "#2A1B4E",
    "info_text": "#D8B4FE",
}

T = LIGHT_THEME if theme == "light" else DARK_THEME

# 4. Standardized CSS Rules
custom_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {{
    --bg-main: {T['bg_main']};
    --bg-sidebar: {T['bg_sidebar']};
    --border-sidebar: {T['border_sidebar']};
    --bg-card: {T['bg_surface']};
    --border-card: {T['border_card']};
    --text-primary: {T['text_main']};
    --text-secondary: {T['text_sec']};

    --btn-lavender-bg: {T['btn_lavender_bg']};
    --btn-lavender-border: {T['btn_lavender_border']};
    --btn-lavender-text: {T['btn_lavender_text']};
    --btn-lavender-icon: {T['btn_lavender_icon']};
    --btn-lavender-hover-bg: {T['btn_lavender_hover_bg']};
    --btn-lavender-hover-border: {T['btn_lavender_hover_border']};
    --btn-lavender-hover-text: {T['btn_lavender_hover_text']};
    --btn-lavender-hover-icon: {T['btn_lavender_hover_icon']};

    --btn-primary-bg: {T['btn_primary_bg']};
    --btn-primary-text: {T['btn_primary_text']};
    --btn-primary-hover: {T['btn_primary_hover_bg']};
}}

/* Hide Default Chrome Header & Footer */
header[data-testid="stHeader"] {{ background-color: transparent !important; z-index: 100 !important; }}
footer {{ visibility: hidden; }}
[data-testid="stDecoration"] {{ display: none; }}
#MainMenu {{ visibility: hidden; }}

/* SINGLE Persistent Sidebar Toggle Control */
[data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"] {{
    display: flex !important;
    visibility: visible !important;
    background-color: var(--btn-lavender-bg) !important;
    color: var(--btn-lavender-text) !important;
    border: 1px solid var(--btn-lavender-border) !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
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
[data-testid="collapsedControl"] *, [data-testid="stSidebarCollapseButton"] * {{
    color: var(--btn-lavender-icon) !important;
    fill: var(--btn-lavender-icon) !important;
}}
[data-testid="collapsedControl"]:hover, [data-testid="stSidebarCollapseButton"]:hover {{
    background-color: var(--btn-lavender-hover-bg) !important;
    border-color: var(--btn-lavender-hover-border) !important;
    color: var(--btn-lavender-hover-text) !important;
}}
[data-testid="collapsedControl"]:hover *, [data-testid="stSidebarCollapseButton"]:hover * {{
    color: var(--btn-lavender-hover-icon) !important;
    fill: var(--btn-lavender-hover-icon) !important;
}}

/* Global Theme Canvas */
html, body, .stApp {{
    background-color: var(--bg-main) !important;
    background-image: radial-gradient({T['grid_color']} 1px, transparent 1px) !important;
    background-size: 24px 24px !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: var(--text-primary) !important;
}}

/* Sidebar Styling */
section[data-testid="stSidebar"] {{
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-sidebar) !important;
    width: 280px !important;
}}
section[data-testid="stSidebar"] > div {{
    padding: 1.2rem 1rem !important;
}}
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span {{
    color: var(--text-primary) !important;
}}

/* Main Container Width & Spacing */
section[data-testid="stMain"] .block-container, .main .block-container {{
    max-width: 1050px !important;
    padding-top: 1.2rem !important;
    padding-bottom: 3rem !important;
    margin: 0 auto !important;
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}}

/* Large AI Query Composer Styling */
.stTextArea textarea {{
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-card) !important;
    border-radius: 18px !important;
    color: var(--text-primary) !important;
    padding: 16px !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04) !important;
    resize: none !important;
}}
.stTextArea textarea::placeholder {{
    color: var(--text-secondary) !important;
    opacity: 1 !important;
}}
.stTextArea textarea:focus {{
    border-color: {T['composer_focus_border']} !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.15) !important;
}}

/* ALL NON-SIDEBAR MAIN CONTENT BUTTONS */
section[data-testid="stMain"] .stButton > button,
section[data-testid="stMain"] .rf-history-btn button,
section[data-testid="stMain"] .rf-sec-btn button,
section[data-testid="stMain"] .rf-sug-btn button,
.main .stButton > button {{
    background-color: var(--btn-lavender-bg) !important;
    border: 1px solid var(--btn-lavender-border) !important;
    color: var(--btn-lavender-text) !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
    padding: 10px 18px !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
}}

section[data-testid="stMain"] .stButton > button *,
section[data-testid="stMain"] .rf-history-btn button *,
section[data-testid="stMain"] .rf-sec-btn button *,
section[data-testid="stMain"] .rf-sug-btn button *,
.main .stButton > button * {{
    color: var(--btn-lavender-icon) !important;
    fill: var(--btn-lavender-icon) !important;
}}

section[data-testid="stMain"] .stButton > button:hover,
section[data-testid="stMain"] .rf-history-btn button:hover,
section[data-testid="stMain"] .rf-sec-btn button:hover,
section[data-testid="stMain"] .rf-sug-btn button:hover,
.main .stButton > button:hover {{
    background-color: var(--btn-lavender-hover-bg) !important;
    border-color: var(--btn-lavender-hover-border) !important;
    color: var(--btn-lavender-hover-text) !important;
}}

section[data-testid="stMain"] .stButton > button:hover *,
section[data-testid="stMain"] .rf-history-btn button:hover *,
section[data-testid="stMain"] .rf-sec-btn button:hover *,
section[data-testid="stMain"] .rf-sug-btn button:hover *,
.main .stButton > button:hover * {{
    color: var(--btn-lavender-hover-icon) !important;
    fill: var(--btn-lavender-hover-icon) !important;
}}

/* PRIMARY ACTION BUTTON: SEND QUERY (ALIGN EXTREME RIGHT) */
section[data-testid="stMain"] div[data-testid="stFormSubmitButton"],
.main div[data-testid="stFormSubmitButton"] {{
    display: flex !important;
    justify-content: flex-end !important;
}}

section[data-testid="stMain"] div[data-testid="stFormSubmitButton"] > button,
section[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button,
.main div[data-testid="stFormSubmitButton"] > button,
.main div[data-testid="stFormSubmitButton"] button {{
    background-color: var(--btn-primary-bg) !important;
    border: none !important;
    color: #FFFFFF !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    transition: all 0.2s ease !important;
}}

section[data-testid="stMain"] div[data-testid="stFormSubmitButton"] > button *,
section[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button *,
.main div[data-testid="stFormSubmitButton"] > button *,
.main div[data-testid="stFormSubmitButton"] button * {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}}

section[data-testid="stMain"] div[data-testid="stFormSubmitButton"] > button:hover,
section[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button:hover,
.main div[data-testid="stFormSubmitButton"] > button:hover,
.main div[data-testid="stFormSubmitButton"] button:hover {{
    background-color: var(--btn-primary-hover) !important;
    color: #FFFFFF !important;
}}

section[data-testid="stMain"] div[data-testid="stFormSubmitButton"] > button:hover *,
section[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button:hover *,
.main div[data-testid="stFormSubmitButton"] > button:hover *,
.main div[data-testid="stFormSubmitButton"] button:hover * {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}}

/* SIDEBAR INDEPENDENT STYLING */
section[data-testid="stSidebar"] button,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] button,
section[data-testid="stSidebar"] .rf-reindex-btn button {{
    background-color: {T['upload_btn_bg']} !important;
    border: 1px solid {T['upload_btn_border']} !important;
    color: {T['upload_btn_text']} !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}}

section[data-testid="stSidebar"] button *,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] button *,
section[data-testid="stSidebar"] .rf-reindex-btn button * {{
    color: {T['upload_btn_icon']} !important;
    fill: {T['upload_btn_icon']} !important;
}}

section[data-testid="stSidebar"] button:hover,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] button:hover,
section[data-testid="stSidebar"] .rf-reindex-btn button:hover {{
    background-color: {T['upload_btn_hover_bg']} !important;
    border-color: {T['upload_btn_hover_border']} !important;
    color: {T['upload_btn_hover_text']} !important;
}}

section[data-testid="stSidebar"] button:hover *,
section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] button:hover *,
section[data-testid="stSidebar"] .rf-reindex-btn button:hover * {{
    color: {T['upload_btn_hover_icon']} !important;
    fill: {T['upload_btn_hover_icon']} !important;
}}

/* File Uploader Dropzone Container */
div[data-testid="stFileUploaderDropzone"], section[data-testid="stFileUploaderDropzone"] {{
    background-color: {T['upload_container_bg']} !important;
    border: 1px dashed {T['upload_container_border']} !important;
    color: var(--text-primary) !important;
    border-radius: 12px !important;
    transition: all 0.2s ease !important;
}}
div[data-testid="stFileUploaderDropzone"] small {{
    color: var(--text-secondary) !important;
}}

/* Checkbox Styling */
div[data-baseweb="checkbox"] label span {{
    color: var(--text-primary) !important;
}}

/* Selectbox & Inputs */
.stSelectbox div[data-baseweb="select"] > div, .stTextInput > div > div > input {{
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-card) !important;
    color: var(--text-primary) !important;
    border-radius: 10px !important;
}}

/* Custom Cards */
.rf-card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}}

.rf-user-card {{
    background-color: {T['bg_elevated']};
    border: 1px solid var(--border-card);
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 16px;
    color: var(--text-primary);
}}

.rf-ai-card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}}

.rf-doc-card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
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
    background-color: {T['badge_bg']} !important;
    color: {T['badge_text']} !important;
    border: 1px solid {T['badge_border']} !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    padding: 4px 12px !important;
    border-radius: 14px !important;
    display: inline-block !important;
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

/* Sidebar Labels & Panels */
.rf-sidebar-label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: var(--text-secondary);
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

# 5. Helper Function to Get Documents List & Dynamic Suggestions Generator
def get_documents_info(data_folder="data"):
    if not os.path.exists(data_folder):
        return []
    files = os.listdir(data_folder)
    doc_list = []
    for f in files:
        file_path = os.path.join(data_folder, f)
        if os.path.isfile(file_path) and not f.endswith(".db") and not f.endswith(".faiss") and not f.endswith(".json"):
            size_kb = round(os.path.getsize(file_path) / 1024, 1)
            doc_list.append({"name": f, "size_kb": size_kb})
    return doc_list

def get_dynamic_suggested_queries(documents):
    """Dynamically generates 3 smart suggested query chips based on uploaded documents."""
    if not documents:
        return [
            ("✦ What are the main topics?", "What are the main topics covered in these documents?"),
            ("≡ Summarize this document", "Summarize the key information in these documents."),
            ("◇ Key takeaways & concepts", "What are the key takeaways and important concepts?")
        ]
    
    doc_names_lower = " ".join([d["name"].lower() for d in documents])
    
    if any(k in doc_names_lower for k in ["unit", "chapter", "lecture", "syllabus", "hrpm", "exam", "notes", "module", "book", "subject"]):
        return [
            ("✦ Key concepts in Unit 1", "What are the key concepts and main topics in this unit?"),
            ("≡ Summarize this unit", "Provide a comprehensive summary of this unit."),
            ("◇ Main definitions & terms", "What are the main definitions and key terms explained?")
        ]
    elif any(k in doc_names_lower for k in ["resume", "cv", "bio", "profile", "portfolio"]):
        return [
            ("✦ Main projects & experience", "What are the main projects and work experience listed?"),
            ("≡ Professional summary", "Summarize the professional background and qualifications."),
            ("◇ Skills & technical stack", "What technical skills and tools are mentioned?")
        ]
    elif any(k in doc_names_lower for k in ["report", "paper", "project", "research", "thesis", "proposal"]):
        return [
            ("✦ Main objectives & findings", "What are the main objectives and findings of this document?"),
            ("≡ Executive summary", "Summarize the key executive findings and conclusions."),
            ("◇ Methodology & results", "What methodologies and key results are presented?")
        ]
    else:
        first_name = documents[0]["name"].rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        return [
            (f"✦ Overview of {first_name[:14]}", f"What is the main overview of {first_name}?"),
            ("≡ Summarize this document", "Summarize the key points in this document."),
            ("◇ Important insights & details", "What are the most important insights and details covered?")
        ]

documents_in_data = get_documents_info("data")
doc_count = len(documents_in_data)

# 6. SIDEBAR RENDERING
with st.sidebar:
    st.markdown(f"""
        <div style='margin-bottom: 20px;'>
            <div style='font-size: 20px; font-weight: 700; color: {T["text_main"]}; display: flex; align-items: center; gap: 8px;'>
                <span style='color: {T["btn_primary_bg"]};'>✦</span> RAGFoundry
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
                        <span style="color: {T["text_sec"]};">📄</span> 
                        <span style="font-size: 13px; font-weight: 500; color: {T["text_main"]};">{doc['name']}</span>
                    </div>
                    <span class="rf-badge-mint">✓ Indexed</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size: 12px; color: {T["text_sec"]}; margin-bottom: 10px;">No documents uploaded yet.</div>', unsafe_allow_html=True)

    # Upload Controls
    clear_existing = st.checkbox("Clear old documents on upload", value=True)
    uploaded_files = st.file_uploader(
        "Upload files", 
        type=["txt", "pdf", "md", "docx", "xlsx", "xls", "csv", "tsv", "pptx", "html", "xml", "json", "yaml", "png", "jpg", "jpeg", "webp"], 
        accept_multiple_files=True, 
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        os.makedirs("data", exist_ok=True)
        if clear_existing:
            for existing_file in os.listdir("data"):
                file_path_to_remove = os.path.join("data", existing_file)
                if os.path.isfile(file_path_to_remove) and not existing_file.endswith(".db"):
                    try:
                        os.remove(file_path_to_remove)
                    except Exception:
                        pass

        for file in uploaded_files:
            file_path = os.path.join("data", file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        st.markdown(f'<div class="rf-badge-mint" style="margin-top:6px;">✓ Saved {len(uploaded_files)} file(s)</div>', unsafe_allow_html=True)
        st.cache_resource.clear()
        st.rerun()

    # Re-Index Button (Sidebar Button)
    st.markdown('<div class="rf-reindex-btn" style="margin-top: 10px;">', unsafe_allow_html=True)
    if st.button("🔄 Re-Index Documents", use_container_width=True):
        st.cache_resource.clear()
        if hasattr(pipeline, "rebuild_index"):
            pipeline.rebuild_index(user_id=current_user_id)
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
            st.markdown(f'<div style="font-size:12px; color:{T["btn_primary_bg"]}; margin-top:4px;">● Gemini Cloud Active</div>', unsafe_allow_html=True)

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


# 7. INITIALIZE RAG PIPELINE WITH SINGLETON CACHING
@st.cache_resource
def get_rag_pipeline():
    return RAGPipeline("data")

try:
    pipeline = get_rag_pipeline()
    pipeline.sync(user_id=current_user_id)
except AttributeError:
    st.cache_resource.clear()
    pipeline = RAGPipeline("data")
    pipeline.sync(user_id=current_user_id)


# 8. MAIN WORKSPACE TOP HEADER
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
        st.markdown('<div class="rf-history-btn">', unsafe_allow_html=True)
        if st.button(hist_btn_text, key="top_history_btn", use_container_width=True):
            st.session_state["show_history_drawer"] = not st.session_state["show_history_drawer"]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
            
    with ctrl_col2:
        theme_btn_label = "☾ Dark Mode" if theme == "light" else "☀ Light Mode"
        st.markdown('<div class="rf-sec-btn">', unsafe_allow_html=True)
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


# 9. HISTORY DRAWER PANEL
if st.session_state["show_history_drawer"]:
    st.markdown(f"""
        <div style="background-color: {T['drawer_bg']}; border: 1px solid {T['border']}; border-radius: 14px; padding: 18px 22px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="font-size: 16px; font-weight: 700; color: {T['text_main']};">◷ Saved Conversations</div>
            </div>
    """, unsafe_allow_html=True)
    
    h_col1, h_col2 = st.columns([1, 3])
    with h_col1:
        st.markdown('<div class="rf-history-btn">', unsafe_allow_html=True)
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
                st.markdown('<div class="rf-sec-btn" style="margin-bottom:4px;">', unsafe_allow_html=True)
                if st.button(f"💬 {c['title']}", key=f"conv_{c['id']}", use_container_width=True):
                    st.session_state["current_conversation_id"] = c["id"]
                    st.session_state["show_history_drawer"] = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                    
    st.markdown('</div>', unsafe_allow_html=True)


# Session state for prompt inputs
if "input_question" not in st.session_state:
    st.session_state["input_question"] = ""

# Handle Instant Execution for Suggested Queries
query_to_execute = None

if "pending_question" in st.session_state and st.session_state["pending_question"]:
    query_to_execute = st.session_state.pop("pending_question")

# 10. LARGE AI QUERY COMPOSER WITH DYNAMIC BUTTON STATE (SEND QUERY vs ANALYZING)
is_processing = st.session_state.get("is_processing", False)
submit_label = "⟳ Analyzing..." if is_processing else "Send Query ➔"

with st.form(key="query_composer_form", clear_on_submit=False):
    user_query = st.text_area(
        "Ask anything about your documents...",
        value=st.session_state.get("input_question", ""),
        height=105,
        placeholder="Ask anything about your documents (e.g. What are the key concepts in this unit?)...",
        label_visibility="collapsed"
    )
    
    col_comp_left, col_comp_right = st.columns([3, 1])
    with col_comp_left:
        st.markdown(f"""
            <div style="font-size: 12px; color: {T['text_sec']}; margin-top: 10px;">
                <span style="color: {T['btn_primary_bg']};">📄</span> {doc_count} Document(s) Indexed &nbsp;·&nbsp; 
                <span style="color: {T['mint_text']};">●</span> {selected_provider.title()} ({selected_model})
            </div>
        """, unsafe_allow_html=True)
    with col_comp_right:
        submit_button = st.form_submit_button(submit_label, disabled=is_processing, use_container_width=False)

if submit_button and user_query.strip():
    query_to_execute = user_query.strip()
    st.session_state["is_processing"] = True


# 11. DYNAMIC SUGGESTED QUERY CARDS
if not st.session_state["current_conversation_id"] and "last_result" not in st.session_state:
    st.markdown(f'<div style="font-size: 11px; font-weight: 700; color: {T["text_sec"]}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 20px; margin-bottom: 12px;">SUGGESTED QUERIES</div>', unsafe_allow_html=True)
    
    dynamic_suggestions = get_dynamic_suggested_queries(documents_in_data)
    s_col1, s_col2, s_col3 = st.columns(3)
    
    for idx, (col_target, (label, full_prompt)) in enumerate(zip([s_col1, s_col2, s_col3], dynamic_suggestions)):
        with col_target:
            st.markdown('<div class="rf-sug-btn">', unsafe_allow_html=True)
            if st.button(label, key=f"sug_p{idx+1}", use_container_width=True, disabled=is_processing):
                st.session_state["pending_question"] = full_prompt
                st.session_state["input_question"] = full_prompt
                st.session_state["is_processing"] = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


# 12. DISPLAY PERSISTENT MULTI-TURN CONVERSATION FROM DATABASE FIRST
active_conv_id = st.session_state.get("current_conversation_id")

if active_conv_id:
    saved_messages = db_manager.get_conversation_messages(active_conv_id)
    if saved_messages:
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        for msg in saved_messages:
            if msg["role"] == "user":
                st.markdown(f"""
                    <div class="rf-user-card">
                        <div style="font-size: 11px; font-weight: 700; color: {T['btn_primary_bg']}; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px;">You</div>
                        <div style="font-size: 15px; font-weight: 500; color: {T['text_main']};">{msg['content']}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="rf-ai-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <div style="font-size: 14px; font-weight: 600; color: {T['text_main']}; display: flex; align-items: center; gap: 6px;">
                                <span style="color: {T['btn_primary_bg']};">✦</span> RAGFoundry
                            </div>
                            <span class="rf-badge-mint">✓ Grounded in your documents</span>
                        </div>
                        <div style="font-size: 15px; line-height: 1.65; color: {T['text_main']};">
                            {msg['content']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
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

                if msg.get("chunks"):
                    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
                    with st.expander(f"▸ Retrieved context · {len(msg['chunks'])} chunks (FAISS & Two-Stage Reranker Scores)"):
                        for rank, chunk in enumerate(msg["chunks"]):
                            rerank_score = chunk.get("rerank_score", None)
                            score_display = f"Rerank Score: `{rerank_score:.4f}`" if rerank_score is not None else f"Distance: `{chunk.get('distance_score', 0):.4f}`"
                            page_label = f" (Page {chunk['page_number']})" if chunk.get("page_number") else ""
                            
                            st.markdown(f"""
                                <div style="background-color: {T['bg_surface']}; border: 1px solid {T['border']}; border-radius: 10px; padding: 14px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                        <span class="rf-badge-purple">Rank {rank+1}</span>
                                        <span style="font-size: 12px; color: {T['text_sec']};">{score_display} &nbsp;·&nbsp; 📄 {chunk['filename']}{page_label}</span>
                                    </div>
                                    <div style="font-size: 13px; font-family: monospace; background-color: {T['code_bg']}; padding: 10px; border-radius: 6px; color: {T['text_main']}; white-space: pre-wrap;">
{chunk['text']}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)


# 13. PROCESS NEW QUERY SUBMISSION WITH STAGE PROGRESS & PERFORMANCE TIMING
if query_to_execute:
    question_text = query_to_execute
    st.session_state["input_question"] = ""
    
    conv_id = st.session_state.get("current_conversation_id")
    if not conv_id:
        title = db_manager.generate_conversation_title(question_text)
        conv_id = db_manager.create_conversation(current_user_id, title)
        st.session_state["current_conversation_id"] = conv_id
        
    db_manager.save_message(conv_id, "user", question_text)
    
    st.markdown(f"""
        <div class="rf-user-card">
            <div style="font-size: 11px; font-weight: 700; color: {T['btn_primary_bg']}; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px;">You</div>
            <div style="font-size: 15px; font-weight: 500; color: {T['text_main']};">{question_text}</div>
        </div>
    """, unsafe_allow_html=True)

    status_placeholder = st.empty()
    answer_card_placeholder = st.empty()
    
    accumulated_answer = ""
    retrieved_sources = []
    retrieved_chunks = []
    elapsed_sec = 0.0
    
    try:
        api_key = os.environ.get("GEMINI_API_KEY") if selected_provider == "gemini" else None
        stream_events = pipeline.ask_stream(
            question_text, 
            k=5, 
            provider=selected_provider, 
            model_name=selected_model, 
            user_id=current_user_id,
            api_key=api_key
        )
        
        for event in stream_events:
            if event["type"] == "status":
                status_placeholder.markdown(f"""
                    <div style="font-size: 13px; color: {T['text_sec']}; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <span style="color: {T['btn_primary_bg']}; font-size: 16px;">✦</span> {event['message']}
                    </div>
                """, unsafe_allow_html=True)
            elif event["type"] == "sources":
                retrieved_sources = event["sources"]
                retrieved_chunks = event["chunks"]
            elif event["type"] == "token":
                accumulated_answer += event["delta"]
                answer_card_placeholder.markdown(f"""
                    <div class="rf-ai-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <div style="font-size: 14px; font-weight: 600; color: {T['text_main']}; display: flex; align-items: center; gap: 6px;">
                                <span style="color: {T['btn_primary_bg']};">✦</span> RAGFoundry
                            </div>
                            <span class="rf-badge-mint">⟳ Generating answer...</span>
                        </div>
                        <div style="font-size: 15px; line-height: 1.65; color: {T['text_main']};">
                            {accumulated_answer}▌
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            elif event["type"] == "complete":
                elapsed_sec = event.get("elapsed_sec", 0.0)
                
        status_placeholder.empty()
        
        timing_label = f"✓ Answer generated · {elapsed_sec}s" if elapsed_sec > 0 else "✓ Grounded in your documents"
        answer_card_placeholder.markdown(f"""
            <div class="rf-ai-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div style="font-size: 14px; font-weight: 600; color: {T['text_main']}; display: flex; align-items: center; gap: 6px;">
                        <span style="color: {T['btn_primary_bg']};">✦</span> RAGFoundry
                    </div>
                    <span class="rf-badge-mint">{timing_label}</span>
                </div>
                <div style="font-size: 15px; line-height: 1.65; color: {T['text_main']};">
                    {accumulated_answer}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        db_manager.save_message(
            conv_id,
            "assistant",
            accumulated_answer,
            sources=retrieved_sources,
            chunks=retrieved_chunks
        )
        
        if "last_error" in st.session_state:
            del st.session_state["last_error"]
            
    except Exception as e:
        status_placeholder.empty()
        st.session_state["last_error"] = str(e)
    finally:
        st.session_state["is_processing"] = False
        
    st.rerun()


# 14. ERROR DISPLAY STATE
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
