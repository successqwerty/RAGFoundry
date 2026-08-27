import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join("data", "rag_foundry.db")

def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Conversations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT,
        role TEXT,
        content TEXT,
        sources_json TEXT,
        chunks_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    )
    """)
    
    # Documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        filename TEXT,
        size_kb REAL,
        indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Insert default public user if not exists
    cursor.execute("INSERT OR IGNORE INTO users (id, email) VALUES ('user_default', 'public_user@ragfoundry.local')")
    
    conn.commit()
    conn.close()

def get_or_create_user(email="public_user@ragfoundry.local"):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    user_id = f"user_{hash(email) & 0xffffffff}"
    cursor.execute("INSERT OR IGNORE INTO users (id, email) VALUES (?, ?)", (user_id, email))
    conn.commit()
    conn.close()
    return user_id

def generate_conversation_title(question):
    q = question.strip()
    words = q.split()
    if len(words) <= 5:
        return q.title()
    # Simple intelligent summary title
    cleaned = q.replace("What is", "").replace("what is", "").replace("Tell me about", "").replace("Summarize", "Summary of").strip(" ?.")
    title_words = cleaned.split()[:5]
    return " ".join(title_words).capitalize()

def create_conversation(user_id="user_default", title="New Conversation"):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    conv_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO conversations (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (conv_id, user_id, title, now, now)
    )
    conn.commit()
    conn.close()
    return conv_id

def get_user_conversations_grouped(user_id="user_default"):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)
    
    grouped = {
        "TODAY": [],
        "YESTERDAY": [],
        "PREVIOUS 7 DAYS": [],
        "OLDER": []
    }
    
    for row in rows:
        conv_date = datetime.fromisoformat(row["updated_at"]).date()
        item = {
            "id": row["id"],
            "title": row["title"],
            "updated_at": row["updated_at"]
        }
        if conv_date == today:
            grouped["TODAY"].append(item)
        elif conv_date == yesterday:
            grouped["YESTERDAY"].append(item)
        elif conv_date >= seven_days_ago:
            grouped["PREVIOUS 7 DAYS"].append(item)
        else:
            grouped["OLDER"].append(item)
            
    return grouped

def save_message(conversation_id, role, content, sources=None, chunks=None):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    sources_str = json.dumps(sources) if sources else None
    chunks_str = json.dumps(chunks) if chunks else None
    now = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content, sources_json, chunks_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (conversation_id, role, content, sources_str, chunks_str, now)
    )
    
    # Update conversation updated_at
    cursor.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
    
    conn.commit()
    conn.close()

def get_conversation_messages(conversation_id):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, sources_json, chunks_json, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
        (conversation_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for r in rows:
        messages.append({
            "role": r["role"],
            "content": r["content"],
            "sources": json.loads(r["sources_json"]) if r["sources_json"] else [],
            "chunks": json.loads(r["chunks_json"]) if r["chunks_json"] else [],
            "created_at": r["created_at"]
        })
    return messages

def update_conversation_title(conversation_id, new_title):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (new_title, conversation_id))
    conn.commit()
    conn.close()

def register_document(filename, size_kb, user_id="user_default"):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    doc_id = f"doc_{hash(filename) & 0xffffffff}"
    cursor.execute(
        "INSERT OR REPLACE INTO documents (id, user_id, filename, size_kb, indexed_at) VALUES (?, ?, ?, ?, ?)",
        (doc_id, user_id, filename, size_kb, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
