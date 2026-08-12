# Job AI Agent

A local-first system that runs a Product Manager job hunt end to end: fetch
postings from ~8 sources, filter them hard against a specific candidate profile,
score them with embeddings, and deliver a daily Telegram digest — with an
LLM-tailored resume PDF attached for the strongest matches.

Built for a QA → Product transition targeting India (any work mode) plus
international roles that explicitly accept India-based candidates.

See [architecture.md](architecture.md) for how it works and why the filters are
shaped the way they are.

## Tech Stack

Python 3.11 · FastAPI · Streamlit · SQLAlchemy/SQLite · APScheduler ·
Playwright · sentence-transformers · Groq/OpenAI · loguru

## Setup

**Prerequisites:** Python 3.11+, and a LaTeX distribution providing `pdflatex`
(MiKTeX or TeX Live) if you want tailored-resume attachments.

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install chromium
```

Configure secrets:

```bash
copy .env.example .env         # Windows
```

Then fill in `.env`:

| Variable | Needed for |
| :--- | :--- |
| `GROQ_API_KEY` *(or `OPENAI_API_KEY`)* | Resume tailoring. Groq takes precedence |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Digest delivery |
| `MIN_SCORE_THRESHOLD` | Quality bar for the shortlist (default 60) |
| `DELIVERY_HOUR` | Hour of day to run (default 9) |
| `WELLFOUND_EMAIL`, `WELLFOUND_PASSWORD` | Wellfound browser fetcher (optional) |

Add your resume — **both files matter**:

- `data/resume.pdf` — parsed to build the scoring profile. Without it, scoring
  silently falls back to a generic baseline PM profile and ranks against the
  wrong person.
- `data/master_resume.txt` — the content bank the LLM draws on when tailoring.

Initialize the database:

```bash
python phases/phase_1_foundation/init_db.py
```

## Usage

Run the full pipeline once:

```bash
python phases/phase_4_automation/run_daily_automation.py --run-now
```

Other entry points:

```bash
python phases/phase_4_automation/run_daily_automation.py --dry-run
```

```bash
python phases/phase_4_automation/test_telegram_delivery.py --test-connection
```

```bash
python phases/phase_3_shortlist/generate_daily_shortlist.py
```

```bash
python phases/phase_5_source_intelligence/test_fetchers.py
```

Optional API and dashboard:

```bash
python -m app.main
```

```bash
streamlit run app/web/app.py
```

API docs at `http://localhost:8000/docs`, dashboard at `http://localhost:8501`.

## Project Layout

```
app/
  core/          config, logging, database connection
  models/        SQLAlchemy entities
  repositories/  CRUD per entity
  services/
    ai/                    embeddings, scoring, title filters, resume parsing
    fetchers/              orchestrator, per-source fetchers, browser layer
    shortlist/             generation, formatting, export, cleanup
    automation/            scheduler, telegram, digest, link verification
    source_intelligence/   prefilter, quality filter, source health
    resume/                parsing, analysis, optimization, variants
  web/           Streamlit dashboard
  main.py        FastAPI entry point
phases/          per-phase manifests + runnable scripts
tests/           unit + integration
archive/         superseded experiments
```

Each `phases/*/manifest.md` documents that phase's components and current status
— these are the accurate progress record.

## Troubleshooting

**Empty or low-quality digest?** Check the runtime prerequisites before
debugging logic. Missing files degrade silently rather than crashing:

| Symptom | Likely cause |
| :--- | :--- |
| Scores look generic / irrelevant | `data/resume.pdf` missing |
| Digest never arrives | `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` unset |
| No resume attached to high scorers | `pdflatex` not on PATH |
| A source returns 0 jobs | Site markup changed; check the browser fallback |
| Nothing from Instahyre | Disabled by design — login-gated, see architecture.md |

## Development

```bash
pytest
```

```bash
black app/ && isort app/
```

## License

MIT
