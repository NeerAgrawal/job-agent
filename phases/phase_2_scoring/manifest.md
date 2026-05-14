# Phase 2: AI Intelligence & Scoring Engine

This phase focuses on extracting value from job descriptions using state-of-the-art AI. It covers semantic matching, user profile evaluations, resume parsing, and relevance-based scoring algorithms to surface the best PM jobs.

---

## 📂 Core Components Map

These service packages are driven by the Open AI framework to achieve intelligence-based ranking:

| Component | Sub-module Path | Purpose |
| :--- | :--- | :--- |
| **Embeddings Generator** | `app/services/ai/embeddings.py` | Handles high-dimension vector conversions of profiles and jobs. |
| **Semantic Matcher** | `app/services/ai/matcher.py` | Implements cosine-similarity based relevance metrics. |
| **AI Scorer Engine** | `app/services/ai/scorer.py` | Synthesizes seniority, title, and resume scores into a unified value. |
| **Resume Parser** | `app/services/ai/resume_parser.py`| Extracts skills, achievements, and professional experience. |
| **Seniority Evaluator**| `app/services/ai/seniority.py` | Maps title variations to PM hierarchy (APM, Sr. PM, Director). |
| **Title Prefilter** | `app/services/ai/title_filters.py`| Whitelists PM titles and rejects unrelated fields (e.g., QA, HR). |
| **Profile Builder** | `app/services/ai/profile_builder.py`| Synthesizes unstructured resumes into structural matcher inputs. |

---

## 🛠️ Primary Executables

Verify and tune the intelligence algorithms using:

*   **AI Evaluator Run**: `scripts/testing/test_ai_matching.py`
*   **Rank Scorer Visualizer**: `scripts/debug/view_ranked_jobs.py`

---

## 🎯 Current Operational Status
*   [x] Prompt injection safety enforced.
*   [x] Core relevance scoring algorithm integrated.
*   [x] Fast regex title preprocessing optimized.
*   [ ] Resume customization (Planned).
