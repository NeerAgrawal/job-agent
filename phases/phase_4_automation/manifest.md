# Phase 4: Job Orchestration & Telegram Automation

This phase unifies the fetchers and the shortlisted reports into an entirely hands-off background operation. It uses schedulers to poll jobs, compiles them into daily digests, and publishes alerts automatically to Telegram.

---

## 📂 Core Components Map

These automation engines provide high-frequency operational status and push delivery:

| Component | Sub-module Path | Purpose |
| :--- | :--- | :--- |
| **Background Scheduler**| `app/services/automation/scheduler.py` | Governs APScheduler cron timings for fetching cycles. |
| **Telegram Bot Gateway**| `app/services/automation/telegram.py` | Delivers Markdown alerts and notifications via Telegram API. |
| **Digest Orchestrator** | `app/services/automation/digest.py` | Groups recent jobs into readable push-notifications. |
| **Delivery Tracker** | `app/services/automation/delivery_tracker.py` | Prevents duplicate pushes of the same job ID. |

---

## 🛠️ Primary Executables

Monitor and trigger automation flow using:

*   **Push Notification Check**: `phases/phase_4_automation/test_telegram_delivery.py`
*   **Full Cycle Simulator**: `phases/phase_4_automation/run_daily_automation.py`

---

## 🎯 Current Operational Status
*   [x] Anti-duplication hash tracker implemented.
*   [x] Auto-retry mechanism on HTTP timeouts.
*   [x] Rich telegram markdown formatting active.
*   [x] APScheduler background loop stabilized.
