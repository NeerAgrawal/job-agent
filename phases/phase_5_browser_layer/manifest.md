# Phase 5 (Parallel): Playwright Browser Fallback Layer

To ensure resilience against Cloudflare, aggressive JavaScript rendering, and API protection mechanisms, this phase adds a robust Headless Browser fallback layer using Playwright. It integrates persistent sessions and health checks to degrade gracefully to browser fetching if lightweight HTTP fails.

---

## 📂 Core Components Map

These advanced browser-automations are placed under the specialized fallback library:

| Component | Sub-module Path | Purpose |
| :--- | :--- | :--- |
| **Playwright Manager** | `app/services/fetchers/browser/playwright_manager.py` | Controls browser pooling, launches, and disposal cycles. |
| **Browser Base** | `app/services/fetchers/browser/base_browser_fetcher.py`| Common class detailing scroll triggers & DOM waits. |
| **Instahyre Browser** | `app/services/fetchers/browser/instahyre_browser.py` | Headless crawler fallback for Instahyre. |
| **Cutshort Browser** | `app/services/fetchers/browser/cutshort_browser.py` | Headless crawler fallback for Cutshort. |
| **Session Store** | `app/services/fetchers/browser/session_store.py` | Preserves cookies and tokens under `/sessions/` for reuse. |
| **Health Monitor** | `app/services/fetchers/browser/browser_health.py` | Evaluates RAM overhead, crash counts, and page load delays. |

---

## 🛠️ Primary Executables

Trigger browser-level scripts to test real visual-rendering loops:

*   **Browser Fetch Runner**: `scripts/testing/test_fetchers.py` (Specify browser engines).
*   **Cached Cookie Hub**: Review JSON files under `/sessions/`.

---

## 🎯 Current Operational Status
*   [x] Automated resource disposal (anti-leaking).
*   [x] Visual viewport randomization (human mimicry).
*   [x] Persistent session loading established.
*   [ ] Captcha resolving modules (Planned Future).
