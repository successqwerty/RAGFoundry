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
        precision REAL DEFAULT 0.0,
        accuracy REAL DEFAULT 0.0,
        precision_pct TEXT DEFAULT '0.0%',
        accuracy_pct TEXT DEFAULT '0.0%',
        elapsed_sec REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    )
    """)
    
    # Auto-migrate existing messages table if columns are missing
    cursor.execute("PRAGMA table_info(messages)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if "precision" not in existing_cols and len(existing_cols) > 0:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN precision REAL DEFAULT 0.0")
        except Exception:
            pass
    if "accuracy" not in existing_cols and len(existing_cols) > 0:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN accuracy REAL DEFAULT 0.0")
        except Exception:
            pass
    if "precision_pct" not in existing_cols and len(existing_cols) > 0:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN precision_pct TEXT DEFAULT '0.0%'")
        except Exception:
            pass
    if "accuracy_pct" not in existing_cols and len(existing_cols) > 0:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN accuracy_pct TEXT DEFAULT '0.0%'")
        except Exception:
            pass
    if "elapsed_sec" not in existing_cols and len(existing_cols) > 0:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN elapsed_sec REAL DEFAULT 0.0")
        except Exception:
            pass
    
    # Documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        filename TEXT,
        file_hash TEXT,
        size_kb REAL,
        status TEXT DEFAULT 'indexed',
        indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # Document Chunks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id TEXT PRIMARY KEY,
        document_id TEXT,
        user_id TEXT,
        chunk_index INTEGER,
        page_number INTEGER,
        content TEXT,
        metadata_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents (id)
    )
    """)
    
    cursor.execute("INSERT OR IGNORE INTO users (id, email) VALUES ('user_default', 'public_user@ragfoundry.local')")
    
    conn.commit()
    conn.close()

def get_document_by_hash(file_hash, user_id="user_default"):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, file_hash, size_kb, status FROM documents WHERE file_hash = ? AND user_id = ?",
        (file_hash, user_id)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def register_document(doc_id, filename, file_hash, size_kb, user_id="user_default", status="indexed"):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO documents (id, user_id, filename, file_hash, size_kb, status) VALUES (?, ?, ?, ?, ?, ?)",
        (doc_id, user_id, filename, file_hash, size_kb, status)
    )
    conn.commit()
    conn.close()

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

def generate_conversation_title(question):
    return question.strip()

def get_user_conversations_grouped(user_id="user_default"):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.title, c.created_at, c.updated_at,
               (SELECT content FROM messages WHERE conversation_id = c.id AND role = 'assistant' ORDER BY id ASC LIMIT 1) as first_assistant_msg,
               (SELECT content FROM messages WHERE conversation_id = c.id ORDER BY id ASC LIMIT 1) as first_msg,
               (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as msg_count
        FROM conversations c 
        WHERE c.user_id = ? 
        ORDER BY c.updated_at DESC
    """, (user_id,))
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
        raw_preview = row["first_assistant_msg"] or row["first_msg"] or "No messages yet"
        preview = (raw_preview[:95] + "...") if len(raw_preview) > 95 else raw_preview
        item = {
            "id": row["id"],
            "title": row["title"],
            "preview": preview,
            "msg_count": row["msg_count"],
            "created_at": row["created_at"],
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

def get_all_conversations(user_id="user_default"):
    """Returns flat list of all conversations for user with message count and preview."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.title, c.created_at, c.updated_at,
               (SELECT content FROM messages WHERE conversation_id = c.id AND role = 'assistant' ORDER BY id ASC LIMIT 1) as first_assistant_msg,
               (SELECT content FROM messages WHERE conversation_id = c.id ORDER BY id ASC LIMIT 1) as first_msg,
               (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as msg_count
        FROM conversations c 
        WHERE c.user_id = ? 
        ORDER BY c.updated_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        raw_preview = row["first_assistant_msg"] or row["first_msg"] or "No messages yet"
        preview = (raw_preview[:95] + "...") if len(raw_preview) > 95 else raw_preview
        result.append({
            "id": row["id"],
            "title": row["title"],
            "preview": preview,
            "msg_count": row["msg_count"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })
    return result

def get_conversation(conversation_id):
    """Retrieves full conversation metadata and its messages list."""
    if not conversation_id:
        return None
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, title, created_at, updated_at FROM conversations WHERE id = ?",
        (conversation_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        conv = dict(row)
        conv["messages"] = get_conversation_messages(conversation_id)
        return conv
    return None


def save_message(conversation_id, role, content, sources=None, chunks=None, precision=0.0, accuracy=0.0, precision_pct=None, accuracy_pct=None, elapsed_sec=0.0):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    sources_str = json.dumps(sources) if sources else None
    chunks_str = json.dumps(chunks) if chunks else None
    now = datetime.now().isoformat()
    
    prec_num = float(precision or 0.0)
    acc_num = float(accuracy or 0.0)
    prec_pct = precision_pct or (f"{prec_num:.1f}%" if prec_num > 0 else "0.0%")
    acc_pct = accuracy_pct or (f"{acc_num:.1f}%" if acc_num > 0 else "0.0%")
    elapsed_num = float(elapsed_sec or 0.0)
    
    cursor.execute(
        """INSERT INTO messages 
           (conversation_id, role, content, sources_json, chunks_json, precision, accuracy, precision_pct, accuracy_pct, elapsed_sec, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (conversation_id, role, content, sources_str, chunks_str, prec_num, acc_num, prec_pct, acc_pct, elapsed_num, now)
    )
    
    cursor.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
    
    conn.commit()
    conn.close()

def get_conversation_messages(conversation_id):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC",
        (conversation_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for r in rows:
        r_dict = dict(r)
        
        chunks = json.loads(r_dict["chunks_json"]) if r_dict.get("chunks_json") else []
        sources = json.loads(r_dict["sources_json"]) if r_dict.get("sources_json") else []
        
        msg_precision = r_dict.get("precision", 0.0) or 0.0
        msg_accuracy = r_dict.get("accuracy", 0.0) or 0.0
        msg_precision_pct = r_dict.get("precision_pct")
        msg_accuracy_pct = r_dict.get("accuracy_pct")
        
        # Calculate dynamic fallback if precision/accuracy was not stored on older rows
        if (msg_accuracy == 0.0 or msg_accuracy is None) and r_dict.get("role") == "assistant" and chunks:
            try:
                from rag_pipeline import calculate_rag_metrics
                metrics = calculate_rag_metrics("", r_dict.get("content", ""), chunks)
                msg_precision = metrics["precision"]
                msg_accuracy = metrics["accuracy"]
                msg_precision_pct = metrics["precision_pct"]
                msg_accuracy_pct = metrics["accuracy_pct"]
            except Exception:
                pass

        if not msg_precision_pct:
            msg_precision_pct = f"{float(msg_precision):.1f}%" if msg_precision else "0.0%"
        if not msg_accuracy_pct:
            msg_accuracy_pct = f"{float(msg_accuracy):.1f}%" if msg_accuracy else "0.0%"

        messages.append({
            "role": r_dict["role"],
            "content": r_dict["content"],
            "sources": sources,
            "chunks": chunks,
            "precision": float(msg_precision),
            "accuracy": float(msg_accuracy),
            "precision_pct": msg_precision_pct,
            "accuracy_pct": msg_accuracy_pct,
            "elapsed_sec": float(r_dict.get("elapsed_sec") or 0.0),
            "created_at": r_dict["created_at"]
        })
    return messages

def delete_conversation(conversation_id):
    """Deletes a single conversation and its associated messages safely by conversation_id."""
    if not conversation_id:
        return False
    try:
        init_db()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting conversation {conversation_id}: {e}")
        return False
