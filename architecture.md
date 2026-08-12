# Job AI Agent — Architecture

## Overview

A local-first system that runs a Product Manager job hunt end to end: it fetches
postings from a dozen sources, filters them against a specific candidate profile
(a QA → Product transition targeting India), scores them with embeddings, and
delivers a daily Telegram digest with an LLM-tailored resume attached for the
strongest matches.

The **daily automation pipeline is the product**. FastAPI and Streamlit exist as
a supporting API and dashboard, but nothing in the core loop depends on them.

---

## The Pipeline

`DailyScheduler._run_daily_automation()` in
`app/services/automation/scheduler.py` is the spine. APScheduler fires it once a
day at `DELIVERY_HOUR`.

```
 1. CLEANUP    shortlist/cleanup.py         archive stale jobs
       |
 2. FETCH      fetchers/orchestrator.py     ~8 sources, concurrent, browser fallback
       |                                     -> location policy
       |                                     -> recruiter-repost filter
       |                                     -> experience-requirement filter
       |                                     -> PM title prefilter
       |                                     -> dedupe -> SQLite
       |
 3. SCORE      ai/scorer.py                 embeddings + weighted scoring
       |                                     (resume profile, or baseline fallback)
       |
 4. SHORTLIST  shortlist/generator.py       re-applies every filter, ranks
       |
 5. VERIFY     automation/link_verifier.py  drop postings whose links are dead
       |
 6. DELIVER    automation/telegram.py       digest + tailored resume PDF (score >= 80)
       |
 7. TRACK      automation/delivery_tracker.py  never send the same job twice
```

### Why filters run twice

Steps 2 and 4 apply the *same* location and recruiter-repost checks. This is
deliberate, not redundant: the database holds jobs saved by earlier runs, from
before a given filter existed. Enforcing only at fetch time would let those
older rows leak into delivery forever. **Any new filter must be added in both
places.**

---

## Sources

| Source | Module | Type | Notes |
| :--- | :--- | :--- | :--- |
| Greenhouse | `fetchers/greenhouse.py` | HTTP/JSON | Curated default company board list |
| Lever | `fetchers/lever.py` | HTTP/JSON | |
| Wellfound | `fetchers/wellfound.py` | HTTP | Browser fallback available (authenticated) |
| Remotely | `fetchers/remotely.py` | HTTP | |
| Career pages | `fetchers/career_pages.py` | HTTP | Direct employer pages |
| Cutshort | `fetchers/india/cutshort.py` | HTTP | Browser fallback available |
| Naukri | `fetchers/india/naukri.py` | HTTP | Browser fallback available |
| Instahyre | `fetchers/india/instahyre.py` | — | **Disabled.** Login-gated feed; the browser path is an auth-skip stub yielding ~0 usable jobs for ~38s/run |

Each lightweight fetcher gets a Playwright fallback if it fails or returns
nothing (`_safe_fetch_with_browser_fallback`). Fetch concurrency is capped at 3;
**browser concurrency is capped at 1** — concurrent Playwright contexts on
Windows hang on subprocess cleanup, which is worked around rather than
root-caused.

---

## Filtering Rules

These encode a specific job search, and loosening them re-introduces the noise
they were added to remove.

**Location policy** (`orchestrator._enforce_location_policy`)
- India sources (`instahyre`, `cutshort`, `naukri`, `career_pages`): any work mode.
- International sources: must be `remote_status == "remote"` **and** explicitly
  mention India. A bare "remote" flag is not enough — "Remote-US" and
  "Remote-Canada" postings were leaking through. Silence on India is not treated
  as eligibility.

**Recruiter reposts** (`source_intelligence/quality_filter.py`)
Deliberately conservative, flagging only clear signals: "our client" JD framing,
placeholder company names, staffing/recruitment keywords, and JD prose leaked
into the company-name field. Bare "consulting"/"consultancy"/"solutions" are
intentionally *not* flagged — real employers use them.

**Experience requirements** (`ai/seniority.py`)
`MAX_YEARS_REQUIRED = 3`. The JD *body* is parsed for the lowest credible years
demand and the posting is dropped above that bar. This cannot be done from
titles: postings titled "Associate Product Manager" have been observed demanding
6 years. Postings that state no requirement are kept, since silence usually
means flexible or junior-friendly.

The parser ignores year counts that describe the company rather than the
candidate ("founded 10 years ago", "over the last 5 years"), and takes the floor
of a range, since that is what actually gates an applicant.

**Titles** (`ai/title_filters.py`)
`get_title_category()` returns `pm` / `reject` / `unknown` in staged precedence:
seniority markers → too-senior product roles → allowed target roles → generic
non-product list → unknown. Allowed roles are checked *before* the reject list,
so "technical program manager" and "product analyst" survive despite containing
"program manager" and "analyst".

Seniority is a **hard reject**, not a penalty — senior/lead/principal/staff/
director/VP roles aren't realistic first product roles.

> Callers treat `reject` and `unknown` identically; every consumer accepts only
> `pm`. The distinction exists for rejection statistics and reporting.

---

## Scoring

`ai/scorer.py` combines four dimensions into `final_score` (0–100):

| Dimension | Source |
| :--- | :--- |
| `semantic_score` | Cosine similarity, resume vs JD (`sentence-transformers`) |
| `qa_to_pm_score` | Transition fit for a QA background |
| `salary_score` | Parsed compensation vs preferences (handles LPA format) |
| Title/seniority | Bonuses for AI/Platform/Technical PM; penalties otherwise |
| Experience fit | Applied after normalization; bonus for 0-3 year asks |

The experience-fit adjustment exists because the rest of the scoring works
*against* the transition. Semantic similarity is measured against a resume dense
with 4.5 years of technical work, so job descriptions written for experienced
hires match it better. Before this correction, postings demanding 5-6 years
consistently outranked genuinely entry-level ones: an APM role asking for 1 year
scored 57.9 and was cut, while an "Associate PM" demanding 6 years scored 62.0
and was delivered.

The profile comes from `data/resume.pdf` via `ai/resume_parser.py` +
`ai/profile_builder.py`. **If that file is absent the scorer silently falls back
to a generic baseline PM profile** — scores still get produced, so an
unconfigured install looks like it is working while ranking against the wrong
person.

Jobs failing to score are written back at a fixed `35.0` so they aren't retried
forever.

Only jobs at or above `MIN_SCORE_THRESHOLD` reach the shortlist, and *all* of
them are delivered — there is no top-N cap.

---

## Resume Tailoring

`ai/resume_intelligence.py` triggers for any delivered job scoring ≥ 80:

1. Read `data/master_resume.txt` (content bank) and `main.tex` (LaTeX template)
2. Prompt an LLM to emit a tailored `.tex` — Groq if `GROQ_API_KEY` is set,
   otherwise OpenAI
3. Compile with `pdflatex` into `exports/`
4. Attach the PDF to the Telegram message

Requires a working `pdflatex` on PATH. Without it, delivery still succeeds but
no resume is attached.

---

## Layout

```
app/
  core/          config (pydantic-settings), logging (loguru), db connection
  database/      engine, session, migrations, health, seed
  models/        SQLAlchemy entities (job, application, outreach, resume_version, ...)
  repositories/  CRUD per entity
  schemas/       Pydantic I/O contracts
  services/
    ai/                    embeddings, matcher, scorer, seniority, title_filters,
                           resume_parser, profile_builder, resume_intelligence
    fetchers/              orchestrator + per-source fetchers
      india/               Instahyre, Cutshort, Naukri (+ shared base/utils)
      browser/             Playwright layer, session store, health tracking
    shortlist/             generator, formatter, exporter, cleanup
    automation/            scheduler, telegram, digest, delivery_tracker, link_verifier
    source_intelligence/   prefilter, quality_filter, analytics, health, weights
    resume/                parser, analyzer, optimizer, matcher, variants, workflow
  web/app.py     Streamlit dashboard
  main.py        FastAPI entry point
phases/          per-phase manifests + runnable scripts (see below)
tests/           unit + integration
archive/         superseded experiments
```

### Entry points

| Purpose | Command |
| :--- | :--- |
| Full daily pipeline | `python phases/phase_4_automation/run_daily_automation.py --run-now` |
| Telegram check | `python phases/phase_4_automation/test_telegram_delivery.py --test-connection` |
| Shortlist only | `python phases/phase_3_shortlist/generate_daily_shortlist.py` |
| Fetcher smoke test | `python phases/phase_5_source_intelligence/test_fetchers.py` |
| DB init | `python phases/phase_1_foundation/init_db.py` |
| API server | `python -m app.main` |
| Dashboard | `streamlit run app/web/app.py` |

Each `phases/*/manifest.md` documents that phase's components and status.

---

## Runtime Requirements

Beyond `requirements.txt`:

- **`.env`** — `GROQ_API_KEY` (or `OPENAI_API_KEY`), `TELEGRAM_BOT_TOKEN`,
  `TELEGRAM_CHAT_ID`, and optionally `WELLFOUND_EMAIL`/`WELLFOUND_PASSWORD`
- **`data/`** — `jobs.db`, `resume.pdf`, `master_resume.txt`
- **`playwright install chromium`** — for the browser fallback layer
- **`pdflatex`** — for resume compilation
- **`sessions/`, `logs/`, `exports/`** — created on demand

All are gitignored, so a fresh clone has none of them. The failure mode is
**silent degradation**, not a crash: missing resume → generic baseline profile;
missing Telegram config → digest skipped; missing pdflatex → no attachment.
Check these before debugging an empty or low-quality digest.

---

## Known Gaps

- `EXPORT_ENABLED` is read into config but never used, so the daily run never
  writes to `exports/`; only `generate_daily_shortlist.py` calls the exporter
- Instahyre disabled pending one-time login automation
- Playwright browser concurrency pinned to 1 (Windows cleanup hang unresolved)
- Captcha handling not implemented
- `is_transition_penalized()` is a deprecated no-op kept for compatibility
- `is_reject_role()` is redundant at every call site (`is_pm_role(t) and not
  is_reject_role(t)` reduces to `is_pm_role(t)`)

---

## Version History

- **v0.1.0** (2026-05-06) — foundation: structure, config, logging, SQLAlchemy,
  FastAPI/Streamlit scaffolding
- **v0.5-stable-india-foundation** (2026-05-09) — India sources, PM filtering,
  location normalization, source health tracking
- **v0.6-source-intelligence** (2026-05) — PM density analytics, fetch
  efficiency, Playwright browser layer with authenticated sources
- **v0.7-resume-intelligence** (2026-06) — career-page fetchers, resume
  intelligence engine, Wellfound browser automation
- **v0.8-delivery-quality** (2026-07/08) — recruiter-repost filtering, link
  liveness verification, deliver-all-meaningful (no top-N cap), India-eligible
  remote enforcement, QA→PM title taxonomy

*Last updated: August 12, 2026*
