import json
import sys
import time
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from database.db import get_connection
from engine.nlp_matcher import NLPMatcher
from engine.context import SessionContextManager
from engine.production_rules import ProductionRuleEngine
from engine.dialogue import DialogueManager


def evaluate_labeled_dataset(rules_file: str, eval_data: list[dict]) -> dict:
    matcher = NLPMatcher(str(BASE_DIR / "data" / rules_file))
    kb_path = str(BASE_DIR / "data" / "knowledge_base.json")

    intents = sorted({item["expected_intent"] for item in eval_data})
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)

    latencies_ms = []
    answered_in_scope = 0
    total_in_scope = sum(1 for item in eval_data if item["expected_intent"] != "fallback")
    false_fallbacks = 0

    for idx, item in enumerate(eval_data):
        query = item["query"]
        expected = item["expected_intent"]

        # Fresh session per isolated test utterance
        ctx_mgr = SessionContextManager()
        rule_engine = ProductionRuleEngine(kb_path)
        dm = DialogueManager(matcher, ctx_mgr, rule_engine)

        t0 = time.perf_counter()
        result = dm.handle_turn(f"eval_{idx}", query)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

        predicted = result["detected_intent"]

        if predicted == expected:
            tp[expected] += 1
        else:
            fp[predicted] += 1
            fn[expected] += 1

        if expected != "fallback":
            if result["is_answered"] and predicted == expected:
                answered_in_scope += 1
            if predicted == "fallback":
                false_fallbacks += 1

    per_intent_metrics = {}
    f1_scores = []

    for intent in intents:
        precision = tp[intent] / (tp[intent] + fp[intent]) if (tp[intent] + fp[intent]) > 0 else 0.0
        recall = tp[intent] / (tp[intent] + fn[intent]) if (tp[intent] + fn[intent]) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        per_intent_metrics[intent] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": tp[intent] + fn[intent]
        }
        f1_scores.append(f1)

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    answer_rate = (answered_in_scope / total_in_scope) * 100 if total_in_scope > 0 else 0.0
    fallback_rate = (false_fallbacks / total_in_scope) * 100 if total_in_scope > 0 else 0.0
    avg_latency = sum(latencies_ms) / len(latencies_ms) if latencies_ms else 0.0

    return {
        "per_intent": per_intent_metrics,
        "macro_f1": macro_f1,
        "answer_rate": answer_rate,
        "fallback_rate": fallback_rate,
        "avg_latency_ms": avg_latency,
        "answered_in_scope": answered_in_scope,
        "total_in_scope": total_in_scope
    }


def evaluate_sqlite_logs(rules_file: str) -> tuple[int, int]:
    try:
        with get_connection() as conn:
            logs = conn.execute("SELECT session_id, user_query FROM conversation_logs ORDER BY id ASC").fetchall()
    except Exception:
        return 0, 0

    if not logs:
        return 0, 0

    matcher = NLPMatcher(str(BASE_DIR / "data" / rules_file))
    ctx_mgr = SessionContextManager()
    rules = ProductionRuleEngine(str(BASE_DIR / "data" / "knowledge_base.json"))
    dm = DialogueManager(matcher, ctx_mgr, rules)

    answered = sum(1 for row in logs if dm.handle_turn(f"replay_{row['session_id']}", row["user_query"])["is_answered"])
    return answered, len(logs)


def print_report():
    eval_path = BASE_DIR / "data" / "eval_dataset.json"
    with open(eval_path, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    v1 = evaluate_labeled_dataset("intents_v1.json", eval_data)
    v2 = evaluate_labeled_dataset("intents_v2.json", eval_data)

    print("=" * 72)
    print("EMPIRICAL BENCHMARK REPORT: BASELINE (v1) vs EXPANDED RULES (v2)")
    print("=" * 72)
    print(f"{'Metric':<32} | {'v1 (Baseline)':<16} | {'v2 (Expanded)':<16}")
    print("-" * 72)
    print(f"{'In-Scope Answer Rate':<32} | {v1['answer_rate']:>6.2f}% ({v1['answered_in_scope']}/{v1['total_in_scope']}) | {v2['answer_rate']:>6.2f}% ({v2['answered_in_scope']}/{v2['total_in_scope']})")
    print(f"{'False Fallback Rate':<32} | {v1['fallback_rate']:>15.2f}% | {v2['fallback_rate']:>15.2f}%")
    print(f"{'Macro F1-Score':<32} | {v1['macro_f1']:>16.4f} | {v2['macro_f1']:>16.4f}")
    print(f"{'Avg Response Latency (ms)':<32} | {v1['avg_latency_ms']:>13.3f} ms | {v2['avg_latency_ms']:>13.3f} ms")
    print("=" * 72)

    print("\nPER-INTENT CLASSIFICATION METRICS (v2 Expanded Rule Base)")
    print("-" * 72)
    print(f"{'Intent':<16} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
    print("-" * 72)
    for intent, m in v2["per_intent"].items():
        print(f"{intent:<16} | {m['precision']:>10.4f} | {m['recall']:>10.4f} | {m['f1']:>10.4f} | {m['support']:>8}")
    print("-" * 72)

    # Also report SQLite replay if live user logs exist
    v1_db_ans, total_db = evaluate_sqlite_logs("intents_v1.json")
    if total_db > 0:
        v2_db_ans, _ = evaluate_sqlite_logs("intents_v2.json")
        print(f"\nSQLITE LIVE LOG REPLAY ({total_db} logged turns):")
        print(f"  v1 Answer Rate: {(v1_db_ans/total_db)*100:.2f}% ({v1_db_ans}/{total_db})")
        print(f"  v2 Answer Rate: {(v2_db_ans/total_db)*100:.2f}% ({v2_db_ans}/{total_db})")


if __name__ == "__main__":
    print_report()