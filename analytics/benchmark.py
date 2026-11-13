import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from database.db import get_connection
from engine.nlp_matcher import NLPMatcher
from engine.context import SessionContextManager
from engine.production_rules import ProductionRuleEngine
from engine.dialogue import DialogueManager

def run_benchmark():
    with get_connection() as conn:
        logs = conn.execute("SELECT session_id, user_query FROM conversation_logs ORDER BY id ASC").fetchall()

    if not logs:
        print("No logged queries found in database. Collect user conversations first.")
        return

    def evaluate_version(rules_file: str):
        matcher = NLPMatcher(str(BASE_DIR / "data" / rules_file))
        ctx_mgr = SessionContextManager()
        rules = ProductionRuleEngine(str(BASE_DIR / "data" / "knowledge_base.json"))
        dm = DialogueManager(matcher, ctx_mgr, rules)

        answered_count = 0
        for row in logs:
            res = dm.handle_turn(f"bench_{row['session_id']}", row["user_query"])
            if res["is_answered"]:
                answered_count += 1
        return answered_count

    total = len(logs)
    v1_answered = evaluate_version("intents_v1.json")
    v2_answered = evaluate_version("intents_v2.json")

    v1_rate = (v1_answered / total) * 100
    v2_rate = (v2_answered / total) * 100
    gain = v2_rate - v1_rate

    print("=== EMPIRICAL EVALUATION BENCHMARK (v1 vs v2) ===")
    print(f"Total Logged Turns Evaluated : {total}")
    print(f"Baseline (intents_v1.json)   : {v1_answered}/{total} ({v1_rate:.2f}%)")
    print(f"Expanded (intents_v2.json)   : {v2_answered}/{total} ({v2_rate:.2f}%)")
    print(f"Net Answer Rate Improvement  : +{gain:.2f}%")

if __name__ == "__main__":
    run_benchmark()