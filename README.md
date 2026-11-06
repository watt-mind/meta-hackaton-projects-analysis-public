# Unofficial Meta Global AI Hackathon 2026 — Project Directory & Telemetry Pipeline

> **Unofficial Community Telemetry Index** — Independent community project built by the [Watt Mind](https://watt-mind.com) team ([`watt-mind/pii-guard`](https://github.com/watt-mind/pii-guard)). Not affiliated with or endorsed by Meta or Cerebral Valley.

Live deployment: **[https://artifacts.watt-mind.com/meta-hackathon-2026/](https://artifacts.watt-mind.com/meta-hackathon-2026/)**

---

## Overview

This repository contains the complete dataset (`4,115` audited public hackathon repositories, `373,802` commits in window, `1,554` live deployments, and `1,247` demo videos) and the static-analysis, multimodal video auditing, and HTML generation pipeline behind the **Unofficial Meta Global AI Hackathon 2026 Project Directory**.

Because all pre-scraped and audited JSON datasets are committed directly to this repository, **you do not need to re-scrape GitHub or re-audit videos to explore the data, tweak the scoring rubric, or regenerate the interactive HTML reports**.

---

## Included Pre-Computed Datasets

All datasets reflect the final post-submission snapshot (**November 5, 2026**):

| File | Description |
| :--- | :--- |
| `projects_inventory_audited.json` | Final scored & ranked dataset of **4,115** hackathon repositories with full 4-pillar score breakdowns, track/category classification, commit/PR counts, live URLs, and video audit summaries. |
| `projects_inventory_audited.csv` | Flat CSV export of all 4,115 ranked repositories for spreadsheet/pandas analysis. |
| `PROJECTS.md` | Markdown directory table of indexed projects. |
| `audit_results_raw.json` | Raw GitHub GraphQL forensic audit cache (commit histories before/during the Oct 26 – Nov 4 window, PR counts, file trees, Docker/test signals, and README excerpts). |
| `video_audit_results.json` | Multimodal video evaluation results (`0.00–2.50` scale) generated via `yt-dlp`, `ffprobe`, **SAM 3.1**, and **Muse Spark 1.3**. |
| `llm_enrichments.json` | Cached LLM semantic summaries, technical highlight tags, and track/domain classifications. |
| `history/timeseries.json` | Cumulative 4-hour time-series telemetry (repositories, commits, live deployments, video demos) from Oct 29 to Nov 5, 2026. |

---

## Quickstart (Zero Scraping Required)

### 1. Re-score & Regenerate the Interactive HTML Directory

You can immediately modify the scoring weights in `process_audit_and_rescore.py` or the UI template in `generate_html_report.py` and rebuild the standalone HTML files using the committed JSON data:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 1. Recompute 4-pillar rubric scores & CSV/JSON exports from cached audit data
python3 process_audit_and_rescore.py

# 2. Generate the standalone interactive HTML directory (meta_hackathon_competitor_analysis_report.html)
python3 generate_html_report.py

# 3. Generate the 20-point Submission & Judging Checklist page (meta_hackathon_submission_checklist.html)
python3 generate_submission_checklist.py
```

Open `meta_hackathon_competitor_analysis_report.html` directly in any browser.

### 2. Optional: Re-run Live GitHub Discovery, LLM Enrichment, or Video Auditing

If you want to run the live crawlers or multimodal video auditor yourself:

1. Copy `.env.example` to `.env` and populate `META_API_KEY`:
   ```bash
   cp .env.example .env
   ```
2. Ensure the GitHub CLI (`gh`) is authenticated (`gh auth status`) and `ffmpeg` / `ffprobe` are installed.
3. Run individual pipeline stages:
   ```bash
   # Discover & GraphQL-audit repositories via GitHub CLI
   python3 update_all_data.py

   # Enrich README summaries & categories with Muse Spark
   python3 llm_enrich.py

   # Audit demo videos with yt-dlp + ffprobe + SAM 3.1 + Muse Spark
   python3 analyze_videos.py

   # Regenerate OpenGraph social preview images (requires Playwright Chromium)
   python3 generate_og_image.py

   # Bundle into a Cloudflare Worker inside wattmind-artifacts/
   python3 build_worker.py
   ```

---

## License

MIT
