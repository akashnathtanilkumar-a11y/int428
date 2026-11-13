# INT428 Course Project — Rule-Based College Enquiry & Admission Helpdesk Chatbot

A deterministic, multi-turn **Symbolic AI** admission helpdesk built for **INT428 (Artificial Intelligence)** using **Unit II IF–THEN production rules**, **Regular Expressions (`re`)**, and **NLTK** text preprocessing—without machine learning or LLMs.

---

## 1. Problem Definition
- **Real-World Problem:** Prospective students and parents frequently ask repetitive admission questions regarding programmes, cut-offs, tuition fees, hostels, scholarships, required documents, and deadlines. Manual helpdesks face long queues, while probabilistic LLMs risk hallucinating inaccurate fees or eligibility thresholds.
- **Target Stakeholders:** Undergraduate/postgraduate applicants, parents, and university admission staff.
- **Agent Formulation (PEAS):**
  - **Performance Measure:** In-scope Answer Rate (%), Macro F1-Score, False Fallback Rate, and response latency (< 5 ms).
  - **Environment:** Multi-turn web chat interface (`/`), admin analytics dashboard (`/admin`), and SQLite conversation logs.
  - **Actuators:** Structured admission responses, slot-filling clarification prompts, and explainable rule traces.
  - **Sensors:** Raw text queries and session context state (`programme`, `marks`, `category`, `hostel_type`).

---

## 2. Knowledge Representation & Data
- `data/knowledge_base.json`: Structured institutional facts for 4 programmes (`B.Tech CSE`, `B.Tech ECE`, `BBA`, `MBA`), category-wise cut-offs (`General`, `OBC`, `SC`, `ST`), fees (₹), AC/Non-AC hostel charges, scholarships, documents, and 2026 deadlines.
- `data/intents_v1.json` & `data/intents_v2.json`: Pattern-matching rule bases mapping regex patterns (+3 score) and lemmatized keywords (+1 score) to 8 core intents and entity slots.
- `data/eval_dataset.json`: 28-query labeled ground-truth dataset covering all 8 intents and out-of-scope fallbacks.
- **Assumptions & Limitations:** Assumes static 2026–27 fee structures and fixed percentage cut-offs; relies on explicit regex/keyword patterns rather than semantic embeddings.

---

## 3. AI Technique & Architecture
- **Why Symbolic Rules over LLMs:** Admission policies require 100% factual accuracy, deterministic auditability, and zero hallucination.
- **Comparable Approaches (`v1` vs `v2`):**
  1. **Baseline (`intents_v1.json`):** Minimal seed regexes and keywords.
  2. **Expanded (`intents_v2.json`):** Iteratively expanded using unanswered queries extracted from SQLite logs (`analytics/analyze.py`).
- **Pipeline:**
  1. `engine/nlp_matcher.py`: Lowercasing, punctuation cleanup, tokenization, WordNet lemmatization, regex intent scoring, and slot extraction.
  2. `engine/context.py` & `engine/dialogue.py`: Retains session slots across turns and prompts for missing required slots (e.g., *"Which programme are you asking about?"*).
  3. `engine/production_rules.py`: Executes explicit `IF–THEN` rules over `knowledge_base.json`.

---

## 4. Performance Analysis (`v1` vs `v2`)
Evaluated on the 28-query labeled ground-truth dataset (`data/eval_dataset.json`) via `python analytics/benchmark.py`:

| Metric | `v1` (Baseline) | `v2` (Expanded) |
| :--- | :---: | :---: |
| **In-Scope Answer Rate** | 70.83% (17/24) | **95.83% (23/24)** |
| **False Fallback Rate** | 29.17% | **4.17%** |
| **Macro F1-Score** | 0.7778 | **0.9654** |
| **Avg Response Latency** | 30.475 ms *(cold start)* | **0.093 ms** |

### Per-Intent Metrics (`v2` Expanded Rule Base)

| Intent | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| `deadlines` | 1.0000 | 1.0000 | 1.0000 | 3 |
| `documents` | 1.0000 | 1.0000 | 1.0000 | 3 |
| `eligibility` | 1.0000 | 1.0000 | 1.0000 | 4 |
| `fees` | 1.0000 | 1.0000 | 1.0000 | 3 |
| `greeting` | 1.0000 | 1.0000 | 1.0000 | 2 |
| `hostel` | 1.0000 | 1.0000 | 1.0000 | 3 |
| `scholarships` | 1.0000 | 1.0000 | 1.0000 | 3 |
| `programmes` | 1.0000 | 0.6667 | 0.8000 | 3 |
| `fallback` | 0.8000 | 1.0000 | 0.8889 | 4 |

- **Error Analysis:** The single false fallback (`"Tell me about B.Tech CSE seats and duration"`) occurred because `NLPMatcher` extracted the `programme` entity (`B.Tech CSE`) without an explicit `programmes` keyword (`seats`/`duration`), demonstrating the boundary between entity extraction and intent triggering.

## 5. Explainability & Responsible AI
- **Rule Traceability:** Every response outputs the exact fired production rule ID, evaluated condition, and lemmatized input tokens (e.g., `RULE_3A_ELIGIBILITY_PASS`) directly in the chat UI.
- **Fairness & Transparency:** Category-specific eligibility cut-offs (`General`, `OBC`, `SC`, `ST`) are explicitly defined in `knowledge_base.json` and shown in the rule trace.
- **Privacy & Security:** Sessions use anonymous UUIDs (`crypto.randomUUID()`), and no personal identifiers (names, phone numbers, emails) are collected or stored in `chatbot_logs.db`.
- **Known Failure Cases:** Severe spelling errors (e.g., `"elgibility"`), regional languages/Hinglish, and unseen slang outside `intents_v2.json` trigger graceful fallbacks.

---

## 6. Setup & Deployment

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Bash/Zsh
# source .venv/bin/activate.fish # Fish shell

# 2. Install dependencies and download NLTK corpora
pip install -r requirements.txt
python setup_nltk.py

# 3. Run the web application (v2 expanded rules)
BOT_VERSION=v2 python app.py