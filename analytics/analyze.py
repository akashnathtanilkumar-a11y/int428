import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_connection

def analyze_unanswered():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT user_query, preprocessed_text, COUNT(*) as count
            FROM conversation_logs
            WHERE is_answered = 0
            GROUP BY LOWER(TRIM(user_query))
            ORDER BY count DESC
        """).fetchall()

    print("=== TOP UNANSWERED QUERIES FOR RULE EXPANSION ===")
    if not rows:
        print("No unanswered queries found in SQLite logs.")
        return

    for idx, r in enumerate(rows, 1):
        print(f"{idx}. [Count: {r['count']}] Query: \"{r['user_query']}\" | Lemmas: \"{r['preprocessed_text']}\"")

if __name__ == "__main__":
    analyze_unanswered()