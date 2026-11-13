class DialogueManager:
    """Manages NLP extraction, session context, slot-filling, and rule evaluation."""
    SLOT_INTENTS = {"eligibility", "fees"}

    def __init__(self, matcher, context_mgr, rule_engine):
        self.matcher = matcher
        self.context_mgr = context_mgr
        self.rule_engine = rule_engine

    def handle_turn(self, session_id: str, user_query: str) -> dict:
        preprocessed = self.matcher.preprocess(user_query)
        detected_intent = self.matcher.detect_intent(user_query, preprocessed)
        extracted_slots = self.matcher.extract_entities(user_query)

        # Update session context
        self.context_mgr.update_context(session_id, extracted_slots, detected_intent)
        ctx = self.context_mgr.get_context(session_id)

        # Resume pending intent if user provided a slot
        active_intent = detected_intent
        if active_intent == "fallback" and ctx.get("pending_intent") and extracted_slots:
            active_intent = ctx["pending_intent"]

        # Prompt for missing programme slot
        if active_intent in self.SLOT_INTENTS and not ctx.get("programme"):
            return {
                "preprocessed_text": preprocessed,
                "detected_intent": active_intent,
                "extracted_slots": extracted_slots,
                "context": ctx,
                "bot_response": "Which programme are you asking about? (We offer **B.Tech CSE**, **B.Tech ECE**, **BBA**, and **MBA**.)",
                "is_answered": True
            }

        # Evaluate production rules
        response, is_answered = self.rule_engine.evaluate(active_intent, ctx)
        if is_answered:
            ctx["pending_intent"] = None

        return {
            "preprocessed_text": preprocessed,
            "detected_intent": active_intent,
            "extracted_slots": extracted_slots,
            "context": ctx,
            "bot_response": response,
            "is_answered": is_answered
        }