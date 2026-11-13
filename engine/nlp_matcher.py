import json
import re
import string
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

class NLPMatcher:
    def __init__(self, rules_path: str):
        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = json.load(f)
        self.lemmatizer = WordNetLemmatizer()

    def preprocess(self, text: str) -> str:
        # Lowercase text
        text_lower = text.lower().strip()
        # Remove punctuation except % and .
        cleaned = re.sub(r"[^\w\s.%]", " ", text_lower)
        # Tokenize text
        tokens = word_tokenize(cleaned)
        # Lemmatize tokens
        lemmas = [self.lemmatizer.lemmatize(tok) for tok in tokens if tok not in string.punctuation]
        return " ".join(lemmas)

    def extract_entities(self, raw_text: str) -> dict:
        text = raw_text.lower()
        extracted = {}

        # Match categorical entities
        for entity_type, mapping in self.rules.get("entities", {}).items():
            for canonical_val, patterns in mapping.items():
                for pat in patterns:
                    if re.search(pat, text, re.IGNORECASE):
                        extracted[entity_type] = canonical_val
                        break
                if entity_type in extracted:
                    break

        # Extract marks or percentages
        marks_match = re.search(r"\b(\d{2}(?:\.\d+)?)\s*(?:%|percent|percentage|marks)?\b", text)
        if marks_match:
            val = float(marks_match.group(1))
            if 30.0 <= val <= 100.0:
                extracted["marks"] = val

        return extracted

    def detect_intent(self, raw_text: str, preprocessed_text: str) -> str:
        best_intent = "fallback"
        highest_score = 0

        for intent_obj in self.rules.get("intents", []):
            score = 0
            # Score regex matches (+3)
            for pat in intent_obj.get("patterns", []):
                if re.search(pat, raw_text, re.IGNORECASE):
                    score += 3

            # Score keyword matches (+1)
            lemma_tokens = set(preprocessed_text.split())
            for kw in intent_obj.get("keywords", []):
                if kw in lemma_tokens:
                    score += 1

            if score > highest_score:
                highest_score = score
                best_intent = intent_obj["name"]

        return best_intent if highest_score > 0 else "fallback"