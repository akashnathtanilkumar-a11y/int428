
class SessionContextManager:
    """In-memory multi-turn context tracker per session_id."""
    def __init__(self):
        self._sessions = {}

    def get_context(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "programme": None,
                "marks": None,
                "category": None,
                "hostel_type": None,
                "pending_intent": None
            }
        return self._sessions[session_id]

    def update_context(self, session_id: str, new_slots: dict, intent: str = None):
        ctx = self.get_context(session_id)
        for key in ["programme", "marks", "category", "hostel_type"]:
            if new_slots.get(key) is not None:
                ctx[key] = new_slots[key]
        if intent and intent != "fallback":
            ctx["pending_intent"] = intent

    def reset_context(self, session_id: str):
        self._sessions.pop(session_id, None)