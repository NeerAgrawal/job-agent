# Phase 3: Shortlist & Curation Architecture

This phase compiles analyzed jobs into a high-impact Daily Shortlist. It focuses on data formatting, scheduled output cleanup, and visual report rendering (CSV/Markdown).

---

## 📂 Core Components Map

The shortlist domain operates as an analytical pipeline to distill hundreds of raw jobs into a curated daily package:

| Component | Sub-module Path | Purpose |
| :--- | :--- | :--- |
| **Pipeline Generator** | `app/services/shortlist/generator.py` | Orchestrates high-scoring DB rows into a cohesive dataset. |
| **Exporter Utility** | `app/services/shortlist/exporter.py` | Serializes structured items into raw CSV formats. |
| **Shortlist Formatter**| `app/services/shortlist/formatter.py` | Transforms serialized data into user-readable markdown grids. |
| **Storage Cleanup** | `app/services/shortlist/cleanup.py` | Archives stale daily outputs after configured retention periods. |

---

## 🛠️ Primary Executables

Generate and inspect the reports using:

*   **Ad-Hoc Report Creation**: `phases/phase_3_shortlist/generate_daily_shortlist.py`
*   **Formatted Exports Sink**: Check files written to `/exports/` directory.

---

## 🎯 Current Operational Status
*   [x] Automated markdown table rendering.
*   [x] Scoring-based sorting configured.
*   [x] Dynamic date-stamped naming conventions applied.
*   [x] Automatic backup generation in exports.
