import os
import uuid
from pathlib import Path
from flask import Flask, render_template, request, jsonify

from database.db import init_db, log_interaction, fetch_dashboard_stats
from engine.nlp_matcher import NLPMatcher
from engine.context import SessionContextManager
from engine.production_rules import ProductionRuleEngine
from engine.dialogue import DialogueManager

BASE_DIR = Path(__file__).resolve().parent
BOT_VERSION = os.getenv("BOT_VERSION", "v2")  # Switch between "v1" and "v2"

app = Flask(__name__)
init_db()

matcher = NLPMatcher(str(BASE_DIR / "data" / f"intents_{BOT_VERSION}.json"))
context_mgr = SessionContextManager()
rule_engine = ProductionRuleEngine(str(BASE_DIR / "data" / "knowledge_base.json"))
dialogue_mgr = DialogueManager(matcher, context_mgr, rule_engine)

@app.route("/")
def index():
    return render_template("index.html", bot_version=BOT_VERSION)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_query = data.get("message", "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not user_query:
        return jsonify({"error": "Empty message"}), 400

    result = dialogue_mgr.handle_turn(session_id, user_query)
    log_interaction(session_id, BOT_VERSION, user_query, result)

    return jsonify({
        "session_id": session_id,
        "reply": result["bot_response"],
        "intent": result["detected_intent"],
        "preprocessed": result["preprocessed_text"],
        "fired_rule": result["fired_rule"],
        "context": result["context"],
        "is_answered": result["is_answered"]
    })

@app.route("/reset", methods=["POST"])
def reset():
    data = request.get_json(force=True)
    session_id = data.get("session_id")
    if session_id:
        context_mgr.reset_context(session_id)
    return jsonify({"status": "reset", "session_id": session_id})

@app.route("/admin")
def admin():
    stats = fetch_dashboard_stats()
    return render_template("admin.html", stats=stats, bot_version=BOT_VERSION)

if __name__ == "__main__":
    app.run(debug=True, port=5000)