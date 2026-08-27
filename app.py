import os
import time
import uuid
import streamlit as st
from rag_pipeline import RAGPipeline

# 1. Session State Initialization
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

if "sidebar_state" not in st.session_state:
    st.session_state["sidebar_state"] = "expanded"

if "conversations" not in st.session_state:
    st.session_state["conversations"] = []

if "current_conv_id" not in st.session_state:
    st.session_state["current_conv_id"] = None

theme = st.session_state["theme"]
sidebar_state = st.session_state["sidebar_state"]

# 2. Page Configuration
st.set_page_config(
    page_title="RAGFoundry — Local AI Document Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state=sidebar_state
)

# 3. Centralized Semantic Theme System
LIGHT_THEME = {
    "bg_main": "#F8F9FF",
    "bg_sidebar": "#F3F1FA",
    "bg_surface": "#FFFFFF",
    "bg_elevated": "#FCFBFF",
    "primary": "#7C68D9",
    "primary_hover": "#6854C6",
    "primary_btn_text": "#FFFFFF",
    "soft_accent": "#EDE9F7",
    "info_bg": "#DCEAF7",
    "info_text": "#374151",
    "mint_bg": "#DDF3E8",
    "mint_text": "#4F8A6B",
    "peach_bg": "#FCE8D8",
    "peach_text": "#374151",
    "text_main": "#374151",
    "text_sec": "#7B8190",
    "text_muted": "#9AA1AF",
    "border": "#E7E5EF",
    "code_bg": "#F8F7FC",
}

DARK_THEME = {
    "bg_main": "#101218",
    "bg_sidebar": "#0C0E13",
    "bg_surface": "#171A22",
    "bg_elevated": "#1C202A",
    "primary": "#A78BFA",
    "primary_hover": "#8B7CF6",
    "primary_btn_text": "#101218",
    "soft_accent": "#242033",
    "info_bg": "#172536",
    "info_text": "#93C5FD",
    "mint_bg": "#142A21",
    "mint_text": "#86E3B3",
    "peach_bg": "#30201C",
    "peach_text": "#FDBA9A",
    "text_main": "#F3F4F6",
    "text_sec": "#A7ADBB",
    "text_muted": "#737B8C",
    "border": "#292E38",
    "code_bg": "#11141C",
}

T = LIGHT_THEME if theme == "light" else DARK_THEME

# 4. Atmospheric Background & Component CSS Injection
if theme == "light":
    bg_style = f"""
        background-color: {T['bg_main']} !important;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(225, 248, 240, 0.65) 0%, transparent 45%),
            radial-gradient(circle at 90% 80%, rgba(232, 225, 255, 0.7) 0%, transparent 45%),
            radial-gradient(circle at 50% 50%, rgba(228, 240, 255, 0.4) 0%, transparent 50%),
            linear-gradient(to right, rgba(139, 124, 200, 0.045) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(139, 124, 200, 0.045) 1px, transparent 1px) !important;
        background-size: 100% 100%, 100% 100%, 100% 100%, 32px 32px, 32px 32px !important;
    """
else:
    bg_style = f"""
        background-color: {T['bg_main']} !important;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(20, 42, 33, 0.4) 0%, transparent 45%),
            radial-gradient(circle at 90% 80%, rgba(36, 32, 51, 0.5) 0%, transparent 45%),
            linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px) !important;
        background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px !important;
    """

custom_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Hide Streamlit Header & Footer Chrome */
header[data-testid="stHeader"] {{
    background-color: transparent !important;
    z-index: 100 !important;
}}
footer {{ visibility: hidden; }}
[data-testid="stDecoration"] {{ display: none; }}
#MainMenu {{ visibility: hidden; }}

/* Persistent Sidebar Open/Close Toggle Button */
[data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"] {{
    display: flex !important;
    visibility: visible !important;
    background-color: {T['bg_surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    color: {T['primary']} !important;
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
    background-color: {T['soft_accent']} !important;
    color: {T['primary']} !important;
}}

/* Global Atmospheric Background */
html, body, .stApp {{
    {bg_style}
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

/* Main Workspace Centering */
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

/* Query Composer Form & Textarea Container */
div[data-testid="stForm"] {{
    background-color: {T['bg_surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 18px !important;
    padding: 16px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
}}
.stTextArea textarea {{
    background-color: transparent !important;
    border: none !important;
    color: {T['text_main']} !important;
    padding: 0px !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: none !important;
    resize: none !important;
}}
.stTextArea textarea::placeholder {{
    color: {T['text_muted']} !important;
    opacity: 1 !important;
}}
.stTextArea textarea:focus {{
    border: none !important;
    box-shadow: none !important;
}}

/* Circular Send Button inside Form (Reference Style!) */
div[data-testid="stForm"] .stButton > button {{
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    border-radius: 50% !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background-color: {T['primary']} !important;
    color: {T['primary_btn_text']} !important;
    font-size: 20px !important;
    border: none !important;
    transition: transform 0.15s ease, background-color 0.2s ease !important;
}}
div[data-testid="stForm"] .stButton > button:hover {{
    background-color: {T['primary_hover']} !important;
    color: {T['primary_btn_text']} !important;
    transform: scale(1.04) !important;
}}

/* Secondary Buttons */
.rf-secondary-btn button {{
    background-color: {T['bg_surface']} !important;
    color: {T['text_main']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
}}
.rf-secondary-btn button:hover {{
    background-color: {T['soft_accent']} !important;
}}

/* Sidebar Close Button */
.rf-sidebar-close-btn button {{
    background-color: {T['soft_accent']} !important;
    color: {T['primary']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    padding: 4px 10px !important;
}}

/* Suggested Query Outline Cards */
.rf-sug-btn button {{
    background-color: {T['bg_surface']} !important;
    color: {T['text_main']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    text-align: left !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
}}
.rf-sug-btn button:hover {{
    border-color: {T['primary']} !important;
    background-color: {T['soft_accent']} !important;
    color: {T['text_main']} !important;
}}

/* History Items in Sidebar */
.rf-history-btn button {{
    background-color: transparent !important;
    color: {T['text_main']} !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    text-align: left !important;
    font-size: 12.5px !important;
    padding: 6px 10px !important;
    margin-bottom: 2px !important;
}}
.rf-history-btn button:hover {{
    background-color: {T['soft_accent']} !important;
    color: {T['primary']} !important;
}}
.rf-history-active button {{
    background-color: {T['soft_accent']} !important;
    color: {T['primary']} !important;
    font-weight: 600 !important;
}}

/* Workspace Cards */
.rf-card {{
    background-color: {T['bg_surface']};
    border: 1px solid {T['border']};
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}}

.rf-user-card {{
    background-color: {T['soft_accent']};
    border: 1px solid {T['border']};
    border-radius: 12px;
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
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}}

.rf-doc-card {{
    background-color: {T['bg_surface']};
    border: 1px solid {T['border']};
    border-radius: 10px;
    padding: 8px 12px;
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
    padding: 3px 8px;
    border-radius: 12px;
    display: inline-block;
}}

.rf-badge-lavender {{
    background-color: {T['soft_accent']};
    color: {T['primary']};
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 12px;
    display: inline-block;
}}

.rf-badge-blue {{
    background-color: {T['info_bg']};
    color: {T['info_text']};
    font-size: 11px;
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 12px;
    display: inline-block;
}}

/* Streamlit Expander */
div[data-testid="stExpander"] {{
    background-color: {T['bg_surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 12px !important;
}}
div[data-testid="stExpander"] summary {{
    color: {T['text_sec']} !important;
    font-weight: 500 !important;
}}

/* Sidebar Label Headers */
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

# 5. Conversation Data Model Helpers
def get_or_create_active_conversation():
    convs = st.session_state["conversations"]
    curr_id = st.session_state.get("current_conv_id")
    
    if curr_id:
        for c in convs:
            if c["id"] == curr_id:
                return c
                
    # Create new conversation
    new_id = str(uuid.uuid4())
    new_conv = {
        "id": new_id,
        "title": "New Conversation",
        "timestamp": time.time(),
        "messages": []
    }
    convs.insert(0, new_conv)
    st.session_state["current_conv_id"] = new_id
    return new_conv

def start_new_conversation():
    new_id = str(uuid.uuid4())
    new_conv = {
        "id": new_id,
        "title": "New Conversation",
        "timestamp": time.time(),
        "messages": []
    }
    st.session_state["conversations"].insert(0, new_conv)
    st.session_state["current_conv_id"] = new_id

# 6. Helper Function to Get Documents List
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

# 7. SIDEBAR RENDERING (BRANDING, HISTORY, WORKSPACE, MODEL & SYSTEM)
with st.sidebar:
    # Branding & Close Button
    sb_hcol1, sb_hcol2 = st.columns([3, 1])
    with sb_hcol1:
        st.markdown(f"""
            <div style='margin-bottom: 12px;'>
                <div style='font-size: 18px; font-weight: 700; color: {T["text_main"]}; display: flex; align-items: center; gap: 6px;'>
                    <span style='color: {T["primary"]};'>✦</span> RAGFoundry
                </div>
                <div style='font-size: 11px; color: {T["text_sec"]}; margin-top: 1px;'>Local AI Document Intelligence</div>
            </div>
        """, unsafe_allow_html=True)
    with sb_hcol2:
        st.markdown('<div class="rf-sidebar-close-btn">', unsafe_allow_html=True)
        if st.button("◀ Close", key="btn_close_sidebar", help="Hide Workspace Sidebar"):
            st.session_state["sidebar_state"] = "collapsed"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 1. HISTORY SECTION
    st.markdown('<div class="rf-sidebar-label">HISTORY</div>', unsafe_allow_html=True)
    st.markdown('<div class="rf-secondary-btn" style="margin-bottom: 10px;">', unsafe_allow_html=True)
    if st.button("+ New conversation", key="btn_new_chat", use_container_width=True):
        start_new_conversation()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Render History List
    active_conv = get_or_create_active_conversation()
    all_convs = st.session_state["conversations"]
    
    if len(all_convs) > 0:
        st.markdown(f'<div style="font-size: 11px; font-weight: 600; color: {T["text_sec"]}; margin-bottom: 6px;">Recent Chats</div>', unsafe_allow_html=True)
        for c in all_convs[:8]: # Display recent conversations
            is_active = (c["id"] == active_conv["id"])
            btn_class = "rf-history-active" if is_active else "rf-history-btn"
            title_display = c["title"][:24] + "..." if len(c["title"]) > 24 else c["title"]
            
            st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
            if st.button(f"💬 {title_display}", key=f"hist_{c['id']}", use_container_width=True):
                st.session_state["current_conv_id"] = c["id"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<hr style='border:none; border-top:1px solid {T['border']}; margin:14px 0;'>", unsafe_allow_html=True)

    # 2. WORKSPACE / DOCUMENTS SECTION
    st.markdown('<div class="rf-sidebar-label">DOCUMENTS</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 13px; font-weight: 600; color: {T["text_main"]}; margin-bottom: 10px;">Knowledge Base &nbsp;·&nbsp; {doc_count}</div>', unsafe_allow_html=True)

    if doc_count > 0:
        for doc in documents_in_data:
            st.markdown(f"""
                <div class="rf-doc-card">
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 160px;">
                        <span style="color: {T["primary"]};">📄</span> 
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

    st.markdown(f"<hr style='border:none; border-top:1px solid {T['border']}; margin:14px 0;'>", unsafe_allow_html=True)

    # 3. AI ENGINE SECTION
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

    # 4. SYSTEM STATUS PANEL
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


# 8. INITIALIZE RAG PIPELINE (Session Cached)
if "pipeline" not in st.session_state:
    with st.spinner("Initializing RAG Engine & Indexing Documents..."):
        st.session_state["pipeline"] = RAGPipeline("data")

pipeline = st.session_state["pipeline"]


# 9. MAIN WORKSPACE CONTENT

# Top Header Layout with Compact Theme Toggle
col_head_left, col_head_right = st.columns([3, 1])

with col_head_left:
    if sidebar_state == "collapsed":
        st.markdown('<div class="rf-secondary-btn" style="margin-bottom: 8px;">', unsafe_allow_html=True)
        if st.button("▶ Open Sidebar / Workspace", key="btn_open_sidebar", help="Open Workspace Sidebar"):
            st.session_state["sidebar_state"] = "expanded"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<span class="rf-badge-lavender">DOCUMENT INTELLIGENCE</span>', unsafe_allow_html=True)
    st.markdown(f'<h1 style="font-size: 32px; margin-top: 6px; margin-bottom: 4px; color: {T["text_main"]};">Ask your documents anything</h1>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 14px; color: {T["text_sec"]}; margin-bottom: 20px;">Search, reason, and answer using your private document knowledge base.</div>', unsafe_allow_html=True)

with col_head_right:
    theme_btn_label = "☾ Dark Mode" if theme == "light" else "☀ Light Mode"
    st.markdown('<div class="rf-secondary-btn" style="text-align: right; margin-bottom: 8px;">', unsafe_allow_html=True)
    if st.button(theme_btn_label, key="theme_toggle_btn", use_container_width=False):
        st.session_state["theme"] = "dark" if theme == "light" else "light"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div style="text-align: right;">
            <span class="rf-badge-mint">● Knowledge base · {doc_count} doc(s)</span>
            <div style="font-size: 12px; color: {T['text_sec']}; margin-top: 4px;">{selected_provider.title()} · {selected_model}</div>
        </div>
    """, unsafe_allow_html=True)


# Get current active conversation
active_conv = get_or_create_active_conversation()

# 10. LARGE AI QUERY COMPOSER WITH CIRCULAR PURPLE SEND BUTTON (Matching Reference Screenshot!)
with st.form(key="query_composer_form", clear_on_submit=True):
    user_query = st.text_area(
        "Ask anything about your documents...",
        value=st.session_state.get("pending_query", ""),
        height=85,
        placeholder="Ask anything about your documents (e.g. What is the second project listed in the resume?)...",
        label_visibility="collapsed"
    )
    
    col_comp_left, col_comp_right = st.columns([5, 1])
    with col_comp_left:
        st.markdown(f"""
            <div style="font-size: 12px; color: {T['text_sec']}; margin-top: 12px;">
                <span style="color: {T['primary']};">📄</span> {doc_count} Document(s) Indexed &nbsp;·&nbsp; 
                <span style="color: {T['mint_text']};">●</span> {selected_provider.title()} ({selected_model})
            </div>
        """, unsafe_allow_html=True)
    with col_comp_right:
        # Circular Purple Send Button with White Arrow (Matching Visual Reference!)
        submit_button = st.form_submit_button("➔", help="Send Query")

if "pending_query" in st.session_state:
    del st.session_state["pending_query"]


# 11. SUGGESTED QUERY CARDS (Shown when current conversation has no messages)
if len(active_conv["messages"]) == 0:
    st.markdown(f'<div style="font-size: 11px; font-weight: 700; color: {T["text_sec"]}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 20px; margin-bottom: 12px;">SUGGESTED QUESTIONS</div>', unsafe_allow_html=True)
    
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        st.markdown('<div class="rf-sug-btn">', unsafe_allow_html=True)
        if st.button("✦ What are the main projects?", key="sug_p1", use_container_width=True):
            st.session_state["pending_query"] = "What are the main projects?"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with s_col2:
        st.markdown('<div class="rf-sug-btn">', unsafe_allow_html=True)
        if st.button("≡ Summarize this document", key="sug_p2", use_container_width=True):
            st.session_state["pending_query"] = "Summarize this document"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with s_col3:
        st.markdown('<div class="rf-sug-btn">', unsafe_allow_html=True)
        if st.button("◇ What skills are mentioned?", key="sug_p3", use_container_width=True):
            st.session_state["pending_query"] = "What skills are mentioned?"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# 12. PROCESS QUERY SUBMISSION & APPEND TO CONVERSATION
if submit_button and user_query.strip():
    query_str = user_query.strip()
    
    # Auto-generate title for first message in conversation
    if len(active_conv["messages"]) == 0:
        short_title = query_str[:28] + "..." if len(query_str) > 28 else query_str
        active_conv["title"] = short_title

    with st.spinner("✦ Searching knowledge base & generating grounded answer..."):
        try:
            # Production dynamic retrieval (K=10 with parent section expansion & CrossEncoder reranking)
            result = pipeline.ask(query_str, k=10, provider=selected_provider, model_name=selected_model)
            
            # Append Q&A Pair to Conversation History
            active_conv["messages"].append({
                "question": query_str,
                "answer": result["answer"],
                "sources": result["sources"],
                "retrieved_chunks": result["retrieved_chunks"],
                "timestamp": time.time()
            })
            
            if "last_error" in st.session_state:
                del st.session_state["last_error"]
        except Exception as e:
            st.session_state["last_error"] = str(e)


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


# 14. DISPLAY ACTIVE CONVERSATION HISTORY (All messages in current chat session)
if len(active_conv["messages"]) > 0:
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    
    for msg in active_conv["messages"]:
        # User Question Card
        st.markdown(f"""
            <div class="rf-user-card">
                <div style="font-size: 11px; font-weight: 700; color: {T['primary']}; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px;">You</div>
                <div style="font-size: 15px; font-weight: 500; color: {T['text_main']};">{msg['question']}</div>
            </div>
        """, unsafe_allow_html=True)

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
                    {msg['answer']}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # EVIDENCE SECTION
        st.markdown(f'<h3 style="font-size: 15px; font-weight: 600; margin-top: 16px; margin-bottom: 10px; color: {T["text_main"]};">Evidence</h3>', unsafe_allow_html=True)
        
        src_cols = st.columns(min(len(msg["sources"]), 3) or 1)
        for idx, src in enumerate(msg["sources"]):
            col_target = src_cols[idx % len(src_cols)]
            with col_target:
                st.markdown(f"""
                    <div class="rf-card" style="padding: 10px 14px; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13px; font-weight: 600; color: {T['text_main']};">📄 {src}</span>
                            <span class="rf-badge-blue">Relevant source</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        # COLLAPSIBLE RETRIEVED CONTEXT
        with st.expander(f"▸ Retrieved context · {len(msg['retrieved_chunks'])} chunks (FAISS & Two-Stage Reranker Scores)"):
            st.markdown(f'<div style="font-size: 12px; color: {T["text_sec"]}; margin-bottom: 12px;">The following text chunks were retrieved by FAISS and re-scored by the Cross-Encoder model:</div>', unsafe_allow_html=True)
            
            for rank, chunk in enumerate(msg["retrieved_chunks"]):
                rerank_score = chunk.get("rerank_score", None)
                score_display = f"Rerank Score: `{rerank_score:.4f}`" if rerank_score is not None else f"Distance: `{chunk['distance_score']:.4f}`"
                
                st.markdown(f"""
                    <div style="background-color: {T['bg_surface']}; border: 1px solid {T['border']}; border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span class="rf-badge-lavender">Rank {rank+1}</span>
                            <span style="font-size: 12px; color: {T['text_sec']};">{score_display} &nbsp;·&nbsp; 📄 {chunk['filename']}</span>
                        </div>
                        <div style="font-size: 13px; font-family: monospace; background-color: {T['code_bg']}; padding: 10px; border-radius: 6px; color: {T['text_main']}; white-space: pre-wrap;">
{chunk['text']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:1px solid rgba(139,124,200,0.15); margin:24px 0;'>", unsafe_allow_html=True)
