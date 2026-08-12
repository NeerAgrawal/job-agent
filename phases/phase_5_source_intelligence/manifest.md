# Phase 5: India Source Expansion & Source Intelligence

This phase expands raw fetching to key India portals (Instahyre, Cutshort, Naukri) and applies deep filtering on top (Domain extraction, salary ranges/LPA, location normalization) alongside detailed tracking of fetcher operational health.

---

## 📂 Core Components Map

These modules house the intelligence logic mapping back to individual job boards:

| Component | Sub-module Path | Purpose |
| :--- | :--- | :--- |
| **India Base Scraper** | `app/services/fetchers/india/base_india_fetcher.py` | Standardizes User-Agents, headers, and rate-limits. |
| **Instahyre Fetcher** | `app/services/fetchers/india/instahyre.py` | Lightweight async HTML parsing for Instahyre. |
| **Cutshort Fetcher** | `app/services/fetchers/india/cutshort.py` | DOM selector extraction targeting Cutshort layouts. |
| **Naukri Fetcher** | `app/services/fetchers/india/naukri.py` | Light JSON-parsing endpoint crawler for Naukri. |
| **Metrics/Analytics** | `app/services/source_intelligence/analytics.py` | Tallies success rates, match rates, and volumes. |
| **Source Health Tracker**| `app/services/source_intelligence/source_health.py` | Detects blocking events, rate limits, and down-times. |
| **Global Orchestrator** | `app/services/fetchers/orchestrator.py` | Parallel async aggregator running all scrapers concurrently. |

---

## 🛠️ Primary Executables

Verify that crawlers are correctly bypassing anti-bot systems and resolving schemas:

*   **Multi-Fetcher Smoke**: `phases/phase_5_source_intelligence/test_fetchers.py`
*   **Async Aggregator Smoke**: `phases/phase_5_source_intelligence/async_smoke_test.py`

---

## 🎯 Current Operational Status
*   [x] Async `httpx` polling implemented.
*   [x] Custom User-Agent cycle established.
*   [x] India location tag normalizer finalized.
*   [x] Failure threshold alerts integrated.
