import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "chatbot_logs.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                bot_version TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_query TEXT NOT NULL,
                preprocessed_text TEXT,
                detected_intent TEXT,
                extracted_slots TEXT,
                bot_response TEXT NOT NULL,
                is_answered INTEGER NOT NULL
            )
        """)
        conn.commit()

def log_interaction(session_id: str, bot_version: str, user_query: str, result: dict):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO conversation_logs (
                session_id, bot_version, timestamp, user_query,
                preprocessed_text, detected_intent, extracted_slots,
                bot_response, is_answered
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            bot_version,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_query,
            result["preprocessed_text"],
            result["detected_intent"],
            json.dumps(result["extracted_slots"]),
            result["bot_response"],
            1 if result["is_answered"] else 0
        ))
        conn.commit()

def fetch_dashboard_stats():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM conversation_logs").fetchone()[0]
        answered = conn.execute("SELECT COUNT(*) FROM conversation_logs WHERE is_answered = 1").fetchone()[0]
        unanswered_rows = conn.execute("""
            SELECT user_query, COUNT(*) as freq
            FROM conversation_logs
            WHERE is_answered = 0
            GROUP BY LOWER(TRIM(user_query))
            ORDER BY freq DESC LIMIT 15
        """).fetchall()
        recent_logs = conn.execute("""
            SELECT * FROM conversation_logs ORDER BY id DESC LIMIT 50
        """).fetchall()

    answer_rate = round((answered / total) * 100, 2) if total > 0 else 0.0
    return {
        "total": total,
        "answered": answered,
        "unanswered": total - answered,
        "answer_rate": answer_rate,
        "top_unanswered": [dict(r) for r in unanswered_rows],
        "recent_logs": [dict(r) for r in recent_logs]
    }