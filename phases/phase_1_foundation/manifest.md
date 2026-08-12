# Phase 1: Foundation & Core Infrastructure

This phase establishes the foundational building blocks of the **Job AI Agent** application, including the database models, configuration loaders, API lifecycles, and shared utilities.

---

## 📂 Core Components Map

The following components in the codebase form the foundation layer:

| Component | Sub-module Path | Purpose |
| :--- | :--- | :--- |
| **Config Manager** | `app/core/config/` | Manages `.env` settings, connection variables, and global toggles. |
| **Logging Engine** | `app/core/logging/` | Standardizes structured logging using `loguru` with automatic rotation. |
| **Database Gateway** | `app/core/database/` | Orchestrates primary SQLAlchemy session engines and utility connects. |
| **ORM Engine** | `app/database/` | Controls migrations (`migrations.py`), base engines, & setup seeds. |
| **Data Entities** | `app/models/` | Houses SQLAlchemy models (Job, Application, Outreach). |
| **Schema Layer** | `app/schemas/` | Validates inputs/outputs using Pydantic definitions. |
| **Base Repository** | `app/repositories/` | Provides basic CRUD pattern implementation. |
| **API Core** | `app/main.py` | Launches the FastAPI lifespan, CORS middlewares, and basic routing. |

---

## 🛠️ Primary Executables

Verify and maintain this phase using the following utilities:

*   **Database Initialization**: `phases/phase_1_foundation/init_db.py`
*   **FastAPI API Launch**: `phases/phase_1_foundation/start_api.bat`
*   **General Health / Smoke Verification**: `phases/phase_1_foundation/smoke_test.py`

---

## 🎯 Current Operational Status
*   [x] Async database support established.
*   [x] Repository CRUD pattern implemented.
*   [x] Dynamic logging rotation configured.
*   [x] Multi-table relational mapping finalized.
