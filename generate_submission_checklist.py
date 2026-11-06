import json
import os
import base64

fonts_b64 = {}
if os.path.exists("fonts_b64.json"):
    try:
        with open("fonts_b64.json") as f:
            fonts_b64 = json.load(f)
    except Exception:
        pass

font_inter_src = (
    f"url(data:font/woff2;base64,{fonts_b64['inter']})"
    if "inter" in fonts_b64
    else "url(https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7W0Q5nw.woff2)"
)
font_jbmono_src = (
    f"url(data:font/woff2;base64,{fonts_b64['jbmono']})"
    if "jbmono" in fonts_b64
    else "url(https://fonts.gstatic.com/s/jetbrainsmono/v24/tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPxDcwgknk-4.woff2)"
)
font_jakarta_src = (
    f"url(data:font/woff2;base64,{fonts_b64['jakarta']})"
    if "jakarta" in fonts_b64
    else "url(https://fonts.gstatic.com/s/plusjakartasans/v12/LDIoaomQNQcsA88c7O9yZ4KMCoOg4Ko20yygg_vb.woff2)"
)

logo_b64 = ""
for lp in ["watt-mind-logo.png"]:
    if os.path.exists(lp):
        with open(lp, "rb") as lf:
            logo_b64 = base64.b64encode(lf.read()).decode("ascii")
        break

logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" class="brand-logo" alt="Watt Mind" />'
    if logo_b64
    else '<span class="brand-logo-fallback">WM</span>'
)

README_TEMPLATE = """## Meta Global AI Hackathon 2026 — Submission Overview

- **Track & Problem Statement**: Indie Developer (or Startup) · Push the Frontier (or Build for Your World)
- **Hackathon Provenance (Oct 26 – Nov 4, 2026)**: Built 100% from scratch during the hackathon window.
- **Meta AI Runtime Models**:
  - `Muse Spark 1.3` (`api.meta.ai`) — Primary reasoning, tool-use & orchestration
  - `Muse Spark Open` / `Muse Glimmer` — Load-bearing open-weight inference stage
  - `SAM 3.1` / `Muse Wonder` / `Muse Voice` — Multimodal perception / synthesis
- **Bonus Prize Categories Targeted**:
  - Best Build on Meta Open Weight Models ($10k) · Best Agentic Use-Case · Best Creative Build
- **3-Minute Demo Video**: https://youtu.be/YOUR_VIDEO_ID
- **Quickstart & Keyless Replay**: Run `cp .env.example .env` with `MODEL_API_KEY`, or `npm run demo:replay`."""

PORTAL_FIELD_TEMPLATE = """Runtime Meta Models Used:
1. Muse Spark 1.3 (Meta Model API): Orchestrates multi-step agent planning and structured tool execution.
2. Muse Spark Open (meta-models/muse-spark-open-1026 via Baseten/Modal/Local): Load-bearing open-weight specialist stage.

Bonus Prize Categories Targeted:
- Best Build on Meta Open Weight Models ($10k)
- Best Agentic Use-Case

Provenance (Oct 26 – Nov 4): Built 100% from scratch during the hackathon window."""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meta Global AI Hackathon 2026 — Unofficial Submission & Judging Readiness Checklist</title>
<meta name="description" content="Unofficial community checklist and operational guide distilled from 580+ answered Discord Q&A and Office Hours threads for the Meta Global AI Developer Hackathon 2026.">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230c1210'/%3E%3Cpath d='M16 4L27 10.5V21.5L16 28L5 21.5V10.5L16 4Z' fill='none' stroke='%234fdbc8' stroke-width='2.5'/%3E%3Ccircle cx='16' cy='16' r='4' fill='%234fdbc8'/%3E%3C/svg%3E">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Watt Mind (Unofficial Community Guide)">
<meta property="og:title" content="Meta Global AI Hackathon 2026 — Unofficial Submission & Judging Checklist">
<meta property="og:description" content="Interactive 20-point pre-submission checklist distilled from 580+ answered Discord Q&A threads: 3-minute video rules, manual bonus prize flagging, repo setup, and track nuances.">
<meta property="og:url" content="https://artifacts.watt-mind.com/meta-hackathon-2026/checklist">
<meta property="og:image" content="https://artifacts.watt-mind.com/meta-hackathon-2026/og-checklist.png?v=1">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Meta Global AI Hackathon 2026 — Unofficial Submission & Judging Checklist">
<meta name="twitter:description" content="Interactive 20-point pre-submission checklist distilled from 580+ answered Discord Q&A threads: 3-minute video rules, manual bonus prize flagging, repo setup, and track nuances.">
<meta name="twitter:image" content="https://artifacts.watt-mind.com/meta-hackathon-2026/og-checklist.png?v=1">
<meta name="theme-color" content="#4fdbc8">
<style>
  @font-face {{
    font-family: 'Inter';
    font-style: normal;
    font-weight: 400 700;
    font-display: swap;
    src: {font_inter_src} format('woff2');
  }}
  @font-face {{
    font-family: 'JetBrains Mono';
    font-style: normal;
    font-weight: 400 700;
    font-display: swap;
    src: {font_jbmono_src} format('woff2');
  }}
  @font-face {{
    font-family: 'Plus Jakarta Sans';
    font-style: normal;
    font-weight: 600 800;
    font-display: swap;
    src: {font_jakarta_src} format('woff2');
  }}

  :root {{
    --bg: #0c1210;
    --surface: #111916;
    --surface-elevated: #16201d;
    --surface-hover: #1b2824;
    --border: #1f2d29;
    --border-strong: #2b3e38;
    --text: #e6efec;
    --text-dim: #9bb0aa;
    --text-muted: #839c95;
    --accent: #4fdbc8;
    --accent-dim: rgba(79, 219, 200, 0.12);
    --amber: #f59e0b;
    --red: #f87171;
    --blue: #38bdf8;
    --purple: #a78bfa;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-display: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  html {{
    scroll-behavior: smooth;
    overflow-x: clip;
  }}
  body {{
    background-color: var(--bg);
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 14px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
    overflow-x: clip;
  }}

  /* Sticky Navbar */
  .navbar {{
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(12, 18, 16, 0.92);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
  }}
  .navbar-inner {{
    max-width: 1280px;
    height: 54px;
    margin: 0 auto;
    padding: 0 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }}
  .brand {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: #ffffff;
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 15px;
    letter-spacing: -0.01em;
    white-space: nowrap;
    flex-shrink: 0;
  }}
  .brand-logo {{
    width: auto;
    height: 24px;
    object-fit: contain;
  }}
  .brand .divider {{
    color: var(--border-strong);
    font-weight: 400;
    margin: 0 2px;
  }}
  .brand .product {{
    color: var(--text-dim);
    font-family: var(--font-sans);
    font-weight: 500;
    font-size: 13.5px;
  }}
  .nav-meta {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: var(--font-mono);
    font-size: 11px;
    flex-wrap: nowrap;
  }}
  .nav-jump {{
    color: var(--text-dim);
    text-decoration: none;
    padding: 4px 8px;
    border-radius: 5px;
    white-space: nowrap;
    transition: color 0.15s, background 0.15s;
  }}
  .nav-jump:hover {{
    color: #ffffff;
    background: rgba(255, 255, 255, 0.05);
  }}
  .nav-ready-pill {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    color: var(--accent);
    background: rgba(79, 219, 200, 0.09);
    border: 1px solid rgba(79, 219, 200, 0.3);
    padding: 4px 9px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    text-decoration: none;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }}
  .nav-countdown-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #ffffff;
    background: rgba(79, 219, 200, 0.14);
    border: 1px solid rgba(79, 219, 200, 0.38);
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    text-decoration: none;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }}
  .cd-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 8px var(--accent);
    animation: cdPulse 2s infinite ease-in-out;
  }}
  @keyframes cdPulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.45; transform: scale(0.85); }}
  }}
  .nav-link-btn {{
    color: var(--text-dim);
    text-decoration: none;
    border: 1px solid var(--border-strong);
    background: var(--surface);
    padding: 4px 9px;
    border-radius: 6px;
    font-size: 11px;
    white-space: nowrap;
    transition: border-color 0.15s, color 0.15s;
  }}
  .nav-link-btn:hover {{
    border-color: var(--accent);
    color: #ffffff;
  }}

  .container {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 36px 32px 80px;
  }}

  /* Header */
  .page-header {{
    margin-bottom: 20px;
  }}
  .header-top-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }}
  h1 {{
    font-family: var(--font-display);
    font-size: 1.75rem;
    font-weight: 800;
    line-height: 1.2;
    letter-spacing: -0.025em;
    color: #ffffff;
    text-wrap: balance;
  }}
  h2, .stage-title, .cl-panel-title, .vb-title, .tpl-title {{
    text-wrap: balance;
  }}
  .unofficial-badge {{
    font-family: var(--font-mono);
    font-size: 0.6875rem;
    font-weight: 600;
    color: #fbbf24;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.38);
    padding: 3px 10px;
    border-radius: 999px;
    letter-spacing: 0.02em;
    white-space: nowrap;
  }}
  .page-header p {{
    color: var(--text-dim);
    font-size: 0.9375rem;
    max-width: 72ch;
    line-height: 1.55;
    text-wrap: pretty;
  }}
  .page-header p strong {{
    color: var(--text);
  }}
  .page-header p code {{
    font-family: var(--font-mono);
    font-size: 12.5px;
    color: var(--accent);
    background: rgba(79, 219, 200, 0.08);
    padding: 1px 6px;
    border-radius: 4px;
  }}

  /* Disclaimer Banner */
  .disclaimer-banner {{
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(17, 25, 22, 0.96) 60%, rgba(79, 219, 200, 0.06) 100%);
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-left: 3px solid var(--amber);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 18px;
    font-size: 12.5px;
    color: var(--text-dim);
  }}
  .disclaimer-banner strong {{
    color: var(--text);
  }}
  .disclaimer-banner a {{
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px dashed rgba(79, 219, 200, 0.45);
  }}

  /* Readiness Bar */
  .readiness-bar {{
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 14px 20px;
    margin-bottom: 26px;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 24px;
  }}
  .rb-left {{
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .rb-kicker {{
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--accent);
  }}
  .rb-sub {{
    font-size: 12px;
    color: var(--text-dim);
  }}
  .rb-mid {{
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .rb-prog-hdr {{
    display: flex;
    justify-content: space-between;
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--text-dim);
  }}
  .rb-prog-hdr strong {{
    color: #ffffff;
  }}
  .rb-track {{
    height: 8px;
    background: var(--bg);
    border: 1px solid var(--border-strong);
    border-radius: 999px;
    overflow: hidden;
  }}
  .rb-fill {{
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, #14b8a6, #4fdbc8);
    border-radius: 999px;
    transition: width 0.25s ease;
  }}
  .rb-right {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .btn-action {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-dim);
    background: var(--bg);
    border: 1px solid var(--border-strong);
    padding: 6px 11px;
    border-radius: 6px;
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
  }}
  .btn-action:hover {{
    border-color: var(--accent);
    color: #ffffff;
  }}
  .btn-action.danger:hover {{
    border-color: var(--red);
    color: #fecaca;
  }}
  .btn-submit-cv {{
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-weight: 600;
    color: var(--accent);
    background: rgba(79, 219, 200, 0.1);
    border: 1px solid rgba(79, 219, 200, 0.38);
    padding: 6px 12px;
    border-radius: 6px;
    text-decoration: none;
    white-space: nowrap;
  }}
  .btn-submit-cv:hover {{
    background: rgba(79, 219, 200, 0.18);
    color: #ffffff;
  }}

  /* Section Headers */
  .section-hdr {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
    flex-wrap: wrap;
  }}
  .section-hdr h2 {{
    font-family: var(--font-display);
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
  }}
  .section-hdr .sub {{
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--text-muted);
  }}

  /* 3-Stage Pipeline Grid */
  .stages-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 30px;
  }}
  .stage-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: 8px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .stage-card.s2 {{ border-top-color: var(--blue); }}
  .stage-card.s3 {{ border-top-color: var(--amber); }}
  .stage-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }}
  .stage-badge {{
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--accent);
    background: rgba(79, 219, 200, 0.1);
    padding: 2px 8px;
    border-radius: 4px;
  }}
  .stage-card.s2 .stage-badge {{ color: var(--blue); background: rgba(56, 189, 248, 0.1); }}
  .stage-card.s3 .stage-badge {{ color: #fbbf24; background: rgba(245, 158, 11, 0.12); }}
  .stage-date {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
  }}
  .stage-title {{
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
  }}
  .stage-desc {{
    font-size: 12.5px;
    color: var(--text-dim);
    line-height: 1.5;
  }}
  .stage-list {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin-top: 4px;
    font-size: 12px;
    color: var(--text-dim);
  }}
  .stage-list li {{
    position: relative;
    padding-left: 14px;
  }}
  .stage-list li::before {{
    content: "›";
    position: absolute;
    left: 2px;
    color: var(--accent);
    font-weight: 700;
  }}
  .stage-callout {{
    margin-top: auto;
    padding: 9px 11px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border);
    font-size: 11.5px;
    color: var(--text-dim);
  }}
  .stage-callout strong {{
    color: #ffffff;
  }}
  .stage-callout code {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent);
  }}

  /* Interactive Checklist Grid */
  .checklist-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 30px;
    align-items: stretch;
  }}
  .cl-panel {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .cl-panel-hdr {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
  }}
  .cl-panel-title {{
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 9px;
    min-width: 0;
  }}
  .cl-step-badge {{
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    color: var(--accent);
    background: var(--accent-dim);
    border: 1px solid rgba(79, 219, 200, 0.28);
    padding: 1px 7px;
    border-radius: 4px;
    flex-shrink: 0;
  }}
  .cl-count-pill {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent);
    background: var(--accent-dim);
    border: 1px solid rgba(79, 219, 200, 0.25);
    padding: 2px 9px;
    border-radius: 999px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    flex-shrink: 0;
  }}

  .cl-items {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
  }}
  .cl-item {{
    display: flex;
    align-items: flex-start;
    gap: 11px;
    padding: 10px 12px;
    border-radius: 7px;
    background: var(--bg);
    border: 1px solid var(--border);
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
    user-select: none;
    flex: 1;
  }}
  .cl-item:hover {{
    border-color: var(--border-strong);
    background: var(--surface-elevated);
  }}
  .cl-item.checked {{
    border-color: rgba(79, 219, 200, 0.35);
    background: rgba(79, 219, 200, 0.05);
  }}
  .cl-item input[type="checkbox"] {{
    appearance: none;
    -webkit-appearance: none;
    width: 17px;
    height: 17px;
    border: 1.5px solid var(--border-strong);
    border-radius: 4px;
    background: var(--surface);
    margin-top: 2px;
    flex-shrink: 0;
    display: grid;
    place-content: center;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }}
  .cl-item input[type="checkbox"]::before {{
    content: "✓";
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    color: #09110e;
    transform: scale(0);
    transition: transform 0.12s ease-in-out;
  }}
  .cl-item input[type="checkbox"]:checked {{
    background: var(--accent);
    border-color: var(--accent);
  }}
  .cl-item input[type="checkbox"]:checked::before {{
    transform: scale(1);
  }}
  .cl-body {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
    width: 100%;
  }}
  .cl-head {{
    font-size: 13px;
    font-weight: 600;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }}
  .cl-item.checked .cl-head-txt {{
    color: var(--accent);
    text-decoration: line-through;
    text-decoration-color: rgba(79, 219, 200, 0.5);
  }}
  .cl-tag {{
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.06);
    color: var(--text-dim);
    white-space: nowrap;
    flex-shrink: 0;
  }}
  .cl-tag.crit {{
    color: #fecaca;
    background: rgba(248, 113, 113, 0.14);
    border: 1px solid rgba(248, 113, 113, 0.3);
  }}
  .cl-tag.bonus {{
    color: #fde68a;
    background: rgba(245, 158, 11, 0.14);
    border: 1px solid rgba(245, 158, 11, 0.3);
  }}
  .cl-tag.info {{
    color: #bae6fd;
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.28);
  }}
  .cl-desc {{
    font-size: 12px;
    color: var(--text-dim);
    line-height: 1.5;
    text-wrap: pretty;
  }}
  .cl-desc code {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent);
    background: rgba(79, 219, 200, 0.08);
    padding: 1px 5px;
    border-radius: 3px;
  }}

  /* 3:00 Video Pacing Strip + Proportional Bar */
  .video-blueprint {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 30px;
  }}
  .vb-prop-wrap {{
    margin-bottom: 14px;
  }}
  .vb-prop-labels {{
    display: flex;
    justify-content: space-between;
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--text-muted);
    margin-bottom: 5px;
  }}
  .vb-prop-bar {{
    display: flex;
    height: 10px;
    border-radius: 999px;
    overflow: hidden;
    background: var(--bg);
    border: 1px solid var(--border-strong);
    gap: 2px;
  }}
  .vb-seg {{
    height: 100%;
  }}
  .vb-timeline {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
  }}
  .vb-step {{
    background: var(--bg);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: 6px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }}
  .vb-step:nth-child(2) {{ border-top-color: #2dd4bf; }}
  .vb-step:nth-child(3) {{ border-top-color: var(--blue); }}
  .vb-step:nth-child(4) {{ border-top-color: var(--purple); }}
  .vb-step:nth-child(5) {{ border-top-color: var(--amber); }}
  .vb-time {{
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    color: var(--accent);
    display: flex;
    justify-content: space-between;
  }}
  .vb-step:nth-child(2) .vb-time {{ color: #2dd4bf; }}
  .vb-step:nth-child(3) .vb-time {{ color: var(--blue); }}
  .vb-step:nth-child(4) .vb-time {{ color: var(--purple); }}
  .vb-step:nth-child(5) .vb-time {{ color: #fbbf24; }}
  .vb-title {{
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
  }}
  .vb-text {{
    font-size: 11.5px;
    color: var(--text-dim);
    line-height: 1.45;
  }}
  .vb-text code {{
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--accent);
  }}

  /* Two-Column Template + Bonus Matrix Row */
  .template-grid {{
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 16px;
    margin-bottom: 30px;
  }}
  .tpl-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .tpl-hdr {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .tpl-tabs {{
    display: inline-flex;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 2px;
    gap: 2px;
  }}
  .tpl-tab {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-dim);
    background: transparent;
    border: none;
    padding: 4px 9px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }}
  .tpl-tab:hover {{
    color: #ffffff;
  }}
  .tpl-tab.active {{
    background: var(--surface-elevated);
    color: var(--accent);
    font-weight: 600;
  }}
  .tpl-title {{
    font-family: var(--font-display);
    font-size: 14.5px;
    font-weight: 700;
    color: #ffffff;
  }}
  .btn-copy-tpl {{
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--accent);
    background: var(--accent-dim);
    border: 1px solid rgba(79, 219, 200, 0.35);
    padding: 4px 10px;
    border-radius: 5px;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s, color 0.15s;
  }}
  .btn-copy-tpl:hover {{
    background: rgba(79, 219, 200, 0.22);
    color: #ffffff;
  }}
  .tpl-pre {{
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 14px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    line-height: 1.5;
    color: #d3e2dd;
    overflow-x: auto;
    white-space: pre-wrap;
    flex: 1;
  }}
  .prize-list {{
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .prize-row {{
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }}
  .prize-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12.5px;
    font-weight: 700;
    color: #ffffff;
  }}
  .prize-amt {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent);
    background: var(--accent-dim);
    padding: 1px 7px;
    border-radius: 4px;
  }}
  .prize-how {{
    font-size: 11.5px;
    color: var(--text-dim);
  }}
  .prize-how code {{
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--accent);
  }}

  /* Q&A Nuances Table + Filter Tabs */
  .qa-controls {{
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }}
  .qa-tab {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-dim);
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 4px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s;
  }}
  .qa-tab:hover {{
    border-color: var(--border-strong);
    color: #ffffff;
  }}
  .qa-tab.active {{
    color: #09110e;
    background: var(--accent);
    border-color: var(--accent);
    font-weight: 600;
  }}
  .qa-panel {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 28px;
  }}
  .qa-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
  }}
  .qa-table th {{
    text-align: left;
    font-family: var(--font-mono);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    background: var(--surface-elevated);
    padding: 11px 16px;
    border-bottom: 1px solid var(--border);
  }}
  .qa-table td {{
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
    color: var(--text-dim);
  }}
  .qa-table tr:last-child td {{
    border-bottom: none;
  }}
  .qa-table td:first-child {{
    color: #ffffff;
    font-weight: 600;
    width: 30%;
  }}
  .qa-cat-badge {{
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    color: var(--accent);
    background: var(--accent-dim);
    padding: 1px 6px;
    border-radius: 4px;
    margin-bottom: 4px;
  }}
  .qa-table code {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent);
    background: rgba(79, 219, 200, 0.08);
    padding: 1px 5px;
    border-radius: 3px;
  }}

  footer {{
    border-top: 1px solid var(--border);
    padding: 20px 24px;
    text-align: center;
    font-size: 12px;
    color: var(--text-muted);
  }}
  footer a {{
    color: var(--accent);
    text-decoration: none;
  }}

  @media (max-width: 980px) {{
    .stages-grid, .checklist-grid, .template-grid {{
      grid-template-columns: 1fr;
    }}
    .vb-timeline {{
      grid-template-columns: 1fr;
    }}
    .readiness-bar {{
      grid-template-columns: 1fr;
      gap: 12px;
    }}
    .nav-jump {{
      display: none;
    }}
  }}
  @media (max-width: 680px) {{
    .navbar-inner {{
      height: 50px;
      padding: 0 14px;
      gap: 8px;
    }}
    .brand {{
      font-size: 13.5px;
      gap: 6px;
      min-width: 0;
      flex-shrink: 1;
      overflow: hidden;
    }}
    .brand-logo {{
      width: auto;
      height: 19px;
      flex-shrink: 0;
    }}
    .brand .product {{
      font-size: 12px;
      overflow: hidden;
      text-overflow: ellipsis;
      min-width: 0;
    }}
    .nav-countdown-pill,
    .nav-ready-pill {{
      display: none;
    }}
    .unofficial-badge {{
      white-space: normal;
      line-height: 1.35;
    }}
    .container {{
      padding: 20px 14px 52px;
    }}
    h1 {{
      font-size: 22px;
      line-height: 1.25;
    }}
    .qa-panel {{
      overflow-x: auto;
    }}
    .qa-table td:first-child {{
      width: 36%;
      min-width: 135px;
    }}
  }}
</style>
</head>
<body>

<nav class="navbar">
  <div class="navbar-inner">
    <a href="/meta-hackathon-2026/" class="brand">
      {logo_html}
      <span>Watt Mind</span>
      <span class="divider">/</span>
      <span class="product">Submission &amp; Judging Checklist</span>
    </a>
    <div class="nav-meta">
      <a href="#stages" class="nav-jump">3-Stage Flow</a>
      <a href="#checklist" class="nav-jump">20-Pt Checklist</a>
      <a href="#video-pacing" class="nav-jump">3:00 Video</a>
      <a href="#readme-template" class="nav-jump">Templates</a>
      <a href="#qa" class="nav-jump">Q&amp;A (12)</a>
      <a href="#checklist" class="nav-ready-pill" id="nav-ready-pill">0/20 Ready</a>
      <a href="/meta-hackathon-2026/" class="nav-link-btn">&larr; Directory</a>
    </div>
  </div>
</nav>

<main class="container">

  <header class="page-header">
    <div class="header-top-row">
      <h1>Unofficial Meta Global AI Hackathon 2026 &mdash; Submission &amp; Judging Checklist</h1>
      <span class="unofficial-badge">Unofficial Community Guide &middot; Distilled from 580+ Q&amp;A Threads</span>
    </div>
    <p>Practical pre-submission checklist synthesizing <strong>official organizer clarifications from 580+ Discord <code>#questions</code> and <code>#office-hours</code> threads</strong> &mdash; covering the 3-stage judging workflow, the 3:00 video cutoff, manual bonus-prize flagging, repository reproducibility, and track eligibility.</p>
  </header>

  <section class="disclaimer-banner">
    <strong>Unofficial Community Resource:</strong> Compiled by <a href="https://watt-mind.com" target="_blank" rel="noopener">Watt Mind</a> as a reference for fellow builders. This page is not affiliated with Meta or Cerebral Valley &mdash; always refer to the <a href="https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details" target="_blank" rel="noopener">Official Hackathon Rules &amp; Participant Guide</a> as the final authority. Your checkbox progress is saved locally in your browser.
  </section>

  <!-- Interactive Readiness Progress Bar -->
  <section class="readiness-bar">
    <div class="rb-left">
      <span class="rb-kicker">Your Submission Readiness</span>
      <span class="rb-sub">Saved automatically in local browser storage</span>
    </div>
    <div class="rb-mid">
      <div class="rb-prog-hdr">
        <span id="rb-count-txt"><strong>0 / 20</strong> checklist items verified</span>
        <span id="rb-pct-txt"><strong>0%</strong> ready</span>
      </div>
      <div class="rb-track">
        <div class="rb-fill" id="rb-fill"></div>
      </div>
    </div>
    <div class="rb-right">
      <button type="button" class="btn-action" id="btn-check-all">Check All</button>
      <button type="button" class="btn-action danger" id="btn-reset-cl">Reset</button>
      <a href="https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit" target="_blank" rel="noopener" class="btn-submit-cv">Submission Portal &#8599;</a>
    </div>
  </section>

  <!-- 1. How the 3-Stage Judging Workflow Operates -->
  <div class="section-hdr" id="stages">
    <h2>1. How the 3-Stage Judging Workflow Operates</h2>
    <span class="sub">Submission Freeze: Wed, Nov 4 at 9:00 PM EST (Thu, Nov 5 at 02:00 UTC)</span>
  </div>

  <section class="stages-grid">
    <div class="stage-card s1">
      <div class="stage-top">
        <span class="stage-badge">Stage 1 &middot; Triage &amp; Flagging</span>
        <span class="stage-date">Nov 5&ndash;6</span>
      </div>
      <div class="stage-title">Pass/Fail Screening &amp; Bonus Flagging</div>
      <p class="stage-desc">Every submission is screened pass/fail before entering rubric scoring:</p>
      <ul class="stage-list">
        <li>Addresses <strong>Build for Your World</strong> or <strong>Push the Frontier</strong></li>
        <li>Meaningfully uses <strong>Meta Model API</strong> and/or <strong>Meta open-weight models</strong> at runtime</li>
        <li>Public GitHub repository showing work built Oct 26 &ndash; Nov 4</li>
        <li>Working, publicly accessible 3-minute demo video</li>
        <li>Complies with Anti-Project rules (not a generic 1-prompt wrapper)</li>
      </ul>
      <div class="stage-callout">
        <strong>Critical Nuance:</strong> There are <strong>no opt-in checkboxes</strong> on the form for technical bonus prizes (<em>$10k Open Weights</em>, <em>Best Agentic</em>, <em>Best Creative</em>). Stage 1 screeners <strong>manually flag</strong> projects based on your video, top of README, and the &ldquo;Use of Meta products&rdquo; form field.
      </div>
    </div>

    <div class="stage-card s2">
      <div class="stage-top">
        <span class="stage-badge">Stage 2 &middot; 10-Point Rubric</span>
        <span class="stage-date">Nov 6&ndash;8</span>
      </div>
      <div class="stage-title">Weighted Rubric &amp; Partner Verification</div>
      <p class="stage-desc">Projects passing Stage 1 are scored on the Official Rules weights (overriding the &ldquo;equally weighted&rdquo; typo in the guide):</p>
      <ul class="stage-list">
        <li><strong>Impact (30% &middot; 3.0 pts)</strong>: Real-world utility, problem severity &amp; post-hackathon viability</li>
        <li><strong>Use of Meta AI Tooling (25% &middot; 2.5 pts)</strong>: Creative, load-bearing multi-model or open-weight usage</li>
        <li><strong>Technical Depth (20% &middot; 2.0 pts)</strong>: Architecture, engineering quality &amp; quantitative benchmarks</li>
        <li><strong>Demo Quality (25% &middot; 2.5 pts)</strong>: Clear 3-minute video + reproducible repo setup instructions</li>
      </ul>
      <div class="stage-callout">
        <strong>Partner Check:</strong> Infrastructure partners (Baseten, Modal, Fireworks) verify projects flagged for the <strong>$10k Open Weights</strong> bonus to confirm <code>Muse Glimmer</code> or <code>Muse Spark Open</code> is a load-bearing component.
      </div>
    </div>

    <div class="stage-card s3">
      <div class="stage-top">
        <span class="stage-badge">Stage 3 &middot; Live Finals</span>
        <span class="stage-date">Mon, Nov 9 &middot; 12:00 PM EST</span>
      </div>
      <div class="stage-title">Top 5 Indie &amp; Top 5 Startup Broadcast</div>
      <p class="stage-desc">The Top 5 projects in the Indie track and Top 5 in the Startup track (10 finalists total) advance to the Closing Ceremony stream:</p>
      <ul class="stage-list">
        <li><strong>No live pitch or live Q&amp;A required</strong> from finalists</li>
        <li>Final Round Judges <strong>watch the submitted 3-minute demo videos live on stream</strong></li>
        <li>Ranked using the same 4-pillar rubric to crown track winners</li>
        <li>Prizes stack: a project can win Main Track + multiple Bonus Prizes</li>
      </ul>
      <div class="stage-callout">
        <strong>Key Takeaway:</strong> Your submitted 3-minute video is the <strong>exact artifact played live for the Final Judges</strong> on November 9 &mdash; it must stand completely on its own.
      </div>
    </div>
  </section>

  <!-- 2. Interactive 20-Point Pre-Submission Checklist -->
  <div class="section-hdr" id="checklist">
    <h2>2. Interactive 20-Point Pre-Submission Checklist</h2>
    <span class="sub">Click any item to mark it complete (5 items per pillar)</span>
  </div>

  <section class="checklist-grid">

    <!-- Panel A: 3-Minute Video -->
    <div class="cl-panel" data-panel="video">
      <div class="cl-panel-hdr">
        <span class="cl-panel-title"><span class="cl-step-badge">01</span> The 3-Minute Demo Video (25% + Finals)</span>
        <span class="cl-count-pill" id="cnt-video">0 / 5</span>
      </div>
      <div class="cl-items">
        <label class="cl-item">
          <input type="checkbox" data-cl="v1" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Duration strictly &le; 3:00 (aim for 2:50&ndash;2:55)</span><span class="cl-tag crit">Hard Stop at 3:00</span></div>
            <p class="cl-desc">Organizers confirmed they will not disqualify a video that is a few seconds over, but <strong>they stop playback at the 3:00 mark</strong>. Never put your benchmarks, key results, or conclusion after <code>2:55</code>.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="v2" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Opening 1-line provenance in first 10 seconds</span><span class="cl-tag crit">Disqualification Risk</span></div>
            <p class="cl-desc">Open your video (spoken + on-screen callout) with one clear sentence stating whether the project was built <strong>100% from scratch during Oct 26&ndash;Nov 4</strong> or what existed beforehand vs. what you built this week.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="v3" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">80%+ real product execution (not slides or IDE code)</span><span class="cl-tag info">Format</span></div>
            <p class="cl-desc">Record a live walkthrough of the working product rather than a slide presentation. You do not need to scroll through source code files on camera &mdash; the video just needs to match the code in your repo.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="v4" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Live Meta model calls &amp; roles visible on screen</span><span class="cl-tag bonus">Bonus Trigger</span></div>
            <p class="cl-desc">Show the end-to-end flow with live Meta model calls/telemetry visible, and explicitly show <em>where</em> and <em>how</em> each Meta model (<code>Muse Spark</code>, <code>Muse Spark Open</code>, <code>Muse Glimmer</code>, <code>SAM 3.1</code>, etc.) is used.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="v5" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Public/Unlisted link + clear English audio &amp; captions</span><span class="cl-tag info">Access</span></div>
            <p class="cl-desc">Host on YouTube (public or unlisted), Loom, or Vimeo with zero login wall. Human presenter/voiceover is preferred (English AI voiceover + burned-in captions are allowed). Speeding up long runs (e.g. <code>4x SPEED</code>) is permitted.</p>
          </div>
        </label>
      </div>
    </div>

    <!-- Panel B: Repository & Reproducibility -->
    <div class="cl-panel" data-panel="repo">
      <div class="cl-panel-hdr">
        <span class="cl-panel-title"><span class="cl-step-badge">02</span> GitHub Repository &amp; Judge Reproducibility</span>
        <span class="cl-count-pill" id="cnt-repo">0 / 5</span>
      </div>
      <div class="cl-items">
        <label class="cl-item">
          <input type="checkbox" data-cl="r1" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Single self-contained public GitHub repository</span><span class="cl-tag crit">Required</span></div>
            <p class="cl-desc">Must be a public <strong>GitHub</strong> repository (GitLab and private repos with judge invites are rejected). Keep everything needed to run the demo in one repo; if building on a startup backend, submit a clean standalone repo created during the hackathon window.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="r2" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Step-by-step Quickstart + <code>.env.example</code></span><span class="cl-tag info">Live URL Optional</span></div>
            <p class="cl-desc">A hosted live deployment is optional &mdash; what judges require is a <strong>runnable repository with clear setup instructions</strong> and a <code>.env.example</code> showing where to supply <code>MODEL_API_KEY</code> (never commit live API keys).</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="r3" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Keyless demo / recorded-trace replay mode included</span><span class="cl-tag bonus">High Judge Signal</span></div>
            <p class="cl-desc">Include a keyless replay mode, pre-recorded execution traces, or deterministic evaluation runner so judges without local GPUs or specific hardware can still verify your outputs immediately.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="r4" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Zero third-party OAuth / login barriers on live demos</span><span class="cl-tag info">Zero Friction</span></div>
            <p class="cl-desc">Never require judges to authenticate with their own personal accounts (e.g., Google Calendar, Slack, GitHub OAuth) to test your app. Provide a one-click <strong>Guest / Demo Mode</strong> or pre-filled demo credentials in the README.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="r5" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Quantitative benchmarks + open-sourced custom weights</span><span class="cl-tag bonus">20% Tech Depth</span></div>
            <p class="cl-desc">Organizers emphasized that <strong>benchmarks greatly strengthen your project</strong> (latency, accuracy, A/B comparisons). If your demo relies on fine-tuned LoRA adapters or custom weights, they must be published openly (e.g., Hugging Face Hub).</p>
          </div>
        </label>
      </div>
    </div>

    <!-- Panel C: Bonus Prizes & Track Selection -->
    <div class="cl-panel" data-panel="bonus">
      <div class="cl-panel-hdr">
        <span class="cl-panel-title"><span class="cl-step-badge">03</span> Bonus Prizes, Tracks &amp; Team Rules</span>
        <span class="cl-count-pill" id="cnt-bonus">0 / 5</span>
      </div>
      <div class="cl-items">
        <label class="cl-item">
          <input type="checkbox" data-cl="b1" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Explicitly call out Bonus Prizes in README &amp; form</span><span class="cl-tag bonus">No Form Checkbox!</span></div>
            <p class="cl-desc">Because Stage 1 screeners manually flag projects for <strong>Best Build on Meta Open Weight Models ($10k)</strong>, <strong>Best Agentic Use-Case</strong>, and <strong>Best Creative Build</strong>, state which bonus categories your project targets at the very top of your README and in the &ldquo;Use of Meta products&rdquo; submission field.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="b2" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">$10k Open Weight: <code>Muse Glimmer</code> / <code>Muse Spark Open</code></span><span class="cl-tag bonus">$10,000 Prize</span></div>
            <p class="cl-desc">To qualify for the $10k Open Weight bonus, <code>Muse Glimmer</code> or <code>Muse Spark Open</code> (<code>meta-models/muse-spark-open-1026</code>) must run as a load-bearing stage (partner inference or self-hosted). Combining hosted <code>Muse Spark 1.3</code> with <code>Muse Spark Open</code> <strong>does qualify</strong>; hosted <code>SAM 3.1</code> alone does not.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="b3" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Correct Track selected: Indie Developer vs. Startup</span><span class="cl-tag info">Legal Entity Rule</span></div>
            <p class="cl-desc">You choose your track on the submission form (regardless of your initial application). <strong>Startup Track</strong> requires an incorporated legal entity with the ability to employ people (EIN / Tax ID in the US; solo incorporated founders qualify). Unincorporated builders/teams must select <strong>Indie Developer</strong>.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="b4" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">$20k Most Viral on X: Link X video post in form</span><span class="cl-tag bonus">$20,000 Prize</span></div>
            <p class="cl-desc">Post your demo video on X before the Nov 4 deadline and paste the post URL into the submission form. Measured strictly by <strong>Likes + Reposts + Comments</strong> (views do not count; no specific hashtag required) through <strong>Sunday, Nov 8 at 11:59 PM EST</strong>.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="b5" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">All contributors are approved participants (max 4)</span><span class="cl-tag crit">Strict Rule</span></div>
            <p class="cl-desc">Every person who contributes code or is listed on the team (up to 4 members) <strong>must be an individually accepted hackathon participant</strong>, and no participant may belong to more than one team or submit multiple projects.</p>
          </div>
        </label>
      </div>
    </div>

    <!-- Panel D: Anti-Project Nuances & Freeze -->
    <div class="cl-panel" data-panel="rules">
      <div class="cl-panel-hdr">
        <span class="cl-panel-title"><span class="cl-step-badge">04</span> Compliance, Licensing &amp; Deadline Freeze</span>
        <span class="cl-count-pill" id="cnt-rules">0 / 5</span>
      </div>
      <div class="cl-items">
        <label class="cl-item">
          <input type="checkbox" data-cl="d1" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Respect Red Lines &amp; differentiate from &ldquo;1-Prompt Slop&rdquo;</span><span class="cl-tag crit">Eligibility</span></div>
            <p class="cl-desc"><strong>Hard red lines:</strong> Mental health/therapy advisors, patient-facing medical diagnosis/advice, and political/defense tools are strictly ineligible. For other domains (education, finance, sports, healthcare ops), organizers clarified the rule targets <em>generic 1-prompt wrappers</em> &mdash; explicitly state in paragraph 1 of your README how your system uses domain-specific depth, deterministic verification, or multi-model pipelines.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="d2" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Include an open-source / source-available <code>LICENSE</code> file</span><span class="cl-tag info">Repo Hygiene</span></div>
            <p class="cl-desc">Add a clear <code>LICENSE</code> file (e.g., MIT or Apache-2.0) in the root of your repository so judges and partner verifiers have unambiguous permission to clone, build, and execute your submission.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="d3" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Verify all 6 Cerebral Valley submission form fields</span><span class="cl-tag info">Portal Check</span></div>
            <p class="cl-desc">Confirm your form has: (1) Public GitHub URL, (2) 3-minute Video URL, (3) Track (<code>Indie</code> vs <code>Startup</code>), (4) Problem Statement (<code>Build for Your World</code> vs <code>Push the Frontier</code>), (5) Detailed &ldquo;Use of Meta products&rdquo; summary, and (6) X Post URL.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="d4" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Submit draft early, then refine until Wed Nov 4, 9:00 PM EST</span><span class="cl-tag info">Strategy</span></div>
            <p class="cl-desc">Submitting early gives zero judging advantage (nothing is reviewed before the deadline), <strong>but</strong> submitting a draft early lets you verify your form links and edit freely right up until <strong>Wednesday, Nov 4 at 9:00 PM EST</strong>.</p>
          </div>
        </label>
        <label class="cl-item">
          <input type="checkbox" data-cl="d5" />
          <div class="cl-body">
            <div class="cl-head"><span class="cl-head-txt">Zero commits or pushes after Wed Nov 4, 9:00 PM EST</span><span class="cl-tag crit">Hard Freeze</span></div>
            <p class="cl-desc">Once the deadline passes (<code>Wed Nov 4, 21:00 EST</code> / <code>Thu Nov 5, 02:00 UTC</code>), stop pushing to the submission branch &mdash; judges verify the exact commit state at the deadline.</p>
          </div>
        </label>
      </div>
    </div>

  </section>

  <!-- 3. Recommended 3:00 Video Pacing Blueprint -->
  <div class="section-hdr" id="video-pacing">
    <h2>3. Recommended 3:00 Video Pacing Blueprint</h2>
    <span class="sub">Proportional 180-second allocation for Stage 1 screening, Stage 2 rubric &amp; Stage 3 live finals</span>
  </div>

  <section class="video-blueprint">
    <div class="vb-prop-wrap">
      <div class="vb-prop-labels">
        <span>0:00 Start</span>
        <span>0:15 Live Demo (45% of runtime)</span>
        <span>1:35 Meta AI Stack (22%)</span>
        <span>2:15 Benchmarks (17%)</span>
        <span>2:55 Stop (3:00 Cutoff)</span>
      </div>
      <div class="vb-prop-bar">
        <div class="vb-seg" style="width: 8.3%; background: #4fdbc8;" title="0:00–0:15 Hook & Provenance (15s)"></div>
        <div class="vb-seg" style="width: 44.4%; background: #2dd4bf;" title="0:15–1:35 Live Product Walkthrough (80s)"></div>
        <div class="vb-seg" style="width: 22.2%; background: #38bdf8;" title="1:35–2:15 Meta AI Architecture (40s)"></div>
        <div class="vb-seg" style="width: 16.7%; background: #a78bfa;" title="2:15–2:45 Benchmarks & Proof (30s)"></div>
        <div class="vb-seg" style="width: 5.6%; background: #f59e0b;" title="2:45–2:55 Summary & Clean Stop (10s)"></div>
        <div class="vb-seg" style="width: 2.8%; background: #ef4444; opacity: 0.45;" title="2:55–3:00 Safety Buffer (5s)"></div>
      </div>
    </div>

    <div class="vb-timeline">
      <div class="vb-step">
        <span class="vb-time"><span>0:00 &ndash; 0:15</span><span>15s</span></span>
        <span class="vb-title">Hook &amp; Provenance</span>
        <p class="vb-text">1-sentence problem statement + <strong>mandatory 1-line provenance callout</strong> stating what was built from scratch during Oct 26&ndash;Nov 4.</p>
      </div>
      <div class="vb-step">
        <span class="vb-time"><span>0:15 &ndash; 1:35</span><span>80s</span></span>
        <span class="vb-title">Live Product Walkthrough</span>
        <p class="vb-text">Jump straight into the running product (no slide deck). Show a real end-to-end user workflow with <strong>live Meta model calls visible on screen</strong>.</p>
      </div>
      <div class="vb-step">
        <span class="vb-time"><span>1:35 &ndash; 2:15</span><span>40s</span></span>
        <span class="vb-title">Meta AI Architecture</span>
        <p class="vb-text">Show how Meta models work together under the hood (e.g. <code>Muse Spark</code> + <code>Muse Spark Open</code> / <code>Muse Glimmer</code> / <code>SAM 3.1</code>) to trigger <strong>Stage 1 bonus prize flagging</strong>.</p>
      </div>
      <div class="vb-step">
        <span class="vb-time"><span>2:15 &ndash; 2:45</span><span>30s</span></span>
        <span class="vb-title">Benchmarks &amp; Proof</span>
        <p class="vb-text">Show quantitative evaluation metrics (accuracy, latency, A/B model comparison, test suite, 1-command reproducibility).</p>
      </div>
      <div class="vb-step">
        <span class="vb-time"><span>2:45 &ndash; 2:55</span><span>10s</span></span>
        <span class="vb-title">Summary &amp; Clean Stop</span>
        <p class="vb-text">Final summary card with repo URL, Meta models used, and headline metrics &mdash; finishing cleanly at <strong>2:55</strong> before the 3:00 cutoff.</p>
      </div>
    </div>
  </section>

  <!-- 4. Copy-Paste README Header Template & Bonus Prize Matrix -->
  <div class="section-hdr" id="readme-template">
    <h2>4. Copy-Paste README Provenance Header &amp; Bonus Prize Guide</h2>
    <span class="sub">Help Stage 1 screeners &amp; Stage 2 judges verify your project in 10 seconds</span>
  </div>

  <section class="template-grid">
    <div class="tpl-card">
      <div class="tpl-hdr">
        <div class="tpl-tabs" id="tpl-tabs">
          <button type="button" class="tpl-tab active" data-tpl="readme">1. Top of README.md</button>
          <button type="button" class="tpl-tab" data-tpl="portal">2. Portal &ldquo;Use of Meta products&rdquo; Field</button>
        </div>
        <button type="button" class="btn-copy-tpl" id="btn-copy-readme">Copy Snippet</button>
      </div>
      <pre class="tpl-pre" id="readme-tpl-code">{README_TEMPLATE}</pre>
      <pre class="tpl-pre" id="portal-tpl-code" style="display:none;">{PORTAL_FIELD_TEMPLATE}</pre>
    </div>

    <div class="tpl-card">
      <div class="tpl-hdr">
        <span class="tpl-title">How Bonus Prizes Are Flagged &amp; Verified</span>
        <span class="sub" style="font-family:var(--font-mono);font-size:11px;color:var(--accent);">Prizes Stack!</span>
      </div>
      <div class="prize-list">
        <div class="prize-row">
          <div class="prize-top"><span>Best Build on Meta Open Weight Models</span><span class="prize-amt">$10,000</span></div>
          <p class="prize-how"><strong>How to qualify:</strong> Use <code>Muse Glimmer</code> or <code>Muse Spark Open</code> (<code>meta-models/muse-spark-open-1026</code>) as a load-bearing runtime stage (partner inference or local GPU). Manually flagged in Stage 1 &amp; verified by Baseten / Modal / Fireworks.</p>
        </div>
        <div class="prize-row">
          <div class="prize-top"><span>Best Agentic Use-Case &amp; Best Creative Build</span><span class="prize-amt">Bonus</span></div>
          <p class="prize-how"><strong>How to qualify:</strong> No form checkbox &mdash; Stage 1 screeners flag contenders based on multi-step tool/agent autonomy or creative multimodal synthesis shown in your 3-minute video and README header.</p>
        </div>
        <div class="prize-row">
          <div class="prize-top"><span>Most Viral Project on X</span><span class="prize-amt">$20,000</span></div>
          <p class="prize-how"><strong>How to qualify:</strong> Post your demo video on X before Nov 4 and paste the X URL in the submission form. Ranked by <strong>Likes + Reposts + Comments</strong> (views excluded) through <strong>Sun, Nov 8 at 11:59 PM EST</strong>.</p>
        </div>
        <div class="prize-row">
          <div class="prize-top"><span>Community Vote Winner</span><span class="prize-amt">$10,000</span></div>
          <p class="prize-how"><strong>How to qualify:</strong> Opens on the Cerebral Valley project gallery after the Nov 4 deadline (1 vote per verified account; winner announced <strong>Mon, Nov 16</strong>).</p>
        </div>
      </div>
    </div>
  </section>

  <!-- 5. Quick Reference: Common Discord Q&A Clarifications -->
  <div class="section-hdr" id="qa">
    <h2>5. Common Questions &amp; Official Clarifications (12 Key Rulings)</h2>
    <div class="qa-controls" id="qa-tabs">
      <button type="button" class="qa-tab active" data-qacat="all">All (12)</button>
      <button type="button" class="qa-tab" data-qacat="Scoring & Finals">Scoring &amp; Finals</button>
      <button type="button" class="qa-tab" data-qacat="Models & Prizes">Models &amp; Prizes</button>
      <button type="button" class="qa-tab" data-qacat="Video & Repo">Video &amp; Repo</button>
      <button type="button" class="qa-tab" data-qacat="Tracks & Teams">Tracks &amp; Teams</button>
    </div>
  </div>

  <section class="qa-panel">
    <table class="qa-table" id="qa-table">
      <thead>
        <tr>
          <th>Topic / Question</th>
          <th>Official Clarification from Discord Q&amp;A</th>
        </tr>
      </thead>
      <tbody>
        <tr data-qacat="Scoring & Finals">
          <td><span class="qa-cat-badge">Scoring &amp; Finals</span><br/>Are the 4 rubric pillars equally weighted (25% each) or 30/25/20/25?</td>
          <td><strong>30% Impact / 25% Meta AI Tooling / 20% Technical Depth / 25% Demo Quality.</strong> Organizers confirmed on Oct 26 that the Official Rules weights (<code>30/25/20/25</code>) govern and override the &ldquo;equally weighted&rdquo; typo in the Participant Guide.</td>
        </tr>
        <tr data-qacat="Scoring & Finals">
          <td><span class="qa-cat-badge">Scoring &amp; Finals</span><br/>Do finalists have to pitch live or answer Q&amp;A on November 9?</td>
          <td><strong>No.</strong> There is no live pitch or live Q&amp;A for finalists. During the Closing Ceremony broadcast (<code>Mon Nov 9, 12:00 PM EST</code>), Final Round Judges watch the Top 5 submitted 3-minute demo videos per track live on stream and select the winners.</td>
        </tr>
        <tr data-qacat="Models & Prizes">
          <td><span class="qa-cat-badge">Models &amp; Prizes</span><br/>How do we apply for the $10k Open Weights, Best Agentic, or Best Creative bonus prizes?</td>
          <td>There are <strong>no separate checkboxes</strong> on the submission form. Stage 1 screeners manually flag projects for bonus categories based on what you write in the &ldquo;Use of Meta products&rdquo; form field, the top of your <code>README.md</code>, and your 3-minute video.</td>
        </tr>
        <tr data-qacat="Models & Prizes">
          <td><span class="qa-cat-badge">Models &amp; Prizes</span><br/>Does combining hosted <code>Muse Spark 1.3</code> with <code>Muse Spark Open</code> or <code>Muse Glimmer</code> qualify for the $10k Open Weights prize?</td>
          <td><strong>Yes!</strong> Combining multiple Meta models is explicitly encouraged. As long as <code>Muse Glimmer</code> or <code>Muse Spark Open</code> (<code>meta-models/muse-spark-open-1026</code>) is a load-bearing stage of your pipeline (via Baseten, Modal, Fireworks, or local hardware), hybrid architectures qualify. Using hosted <code>SAM 3.1</code> alone does not count as an open-weight build.</td>
        </tr>
        <tr data-qacat="Models & Prizes">
          <td><span class="qa-cat-badge">Models &amp; Prizes</span><br/>Can we use Claude Code, Cursor, OpenCode, or Copilot to write code?</td>
          <td><strong>Yes, unrestricted.</strong> Coding assistants used during development do not need to be disclosed and are not restricted. The Meta model requirement applies to the <strong>runtime models</strong> powering your application.</td>
        </tr>
        <tr data-qacat="Models & Prizes">
          <td><span class="qa-cat-badge">Models &amp; Prizes</span><br/>Can we use deterministic algorithms or small custom classifiers alongside Meta models?</td>
          <td><strong>Yes.</strong> Deterministic engines (parsers, solvers, compilers, rule engines) are not competing AI models. Small self-trained classifiers/forecasters alongside Meta models are also permitted provided the training/eval code is open in the repository.</td>
        </tr>
        <tr data-qacat="Video & Repo">
          <td><span class="qa-cat-badge">Video &amp; Repo</span><br/>What happens if our demo video is 3:05 or 3:15 long?</td>
          <td>Organizers stated they will not disqualify a video for being a few seconds over, <strong>but judges stop watching at the 3:00 mark</strong>. Keep your video at or under <code>2:55&ndash;3:00</code> so your benchmarks and closing summary are never cut off.</td>
        </tr>
        <tr data-qacat="Video & Repo">
          <td><span class="qa-cat-badge">Video &amp; Repo</span><br/>Is a hosted live web URL mandatory?</td>
          <td><strong>No.</strong> A hosted web deployment is optional. Judges require a working 3-minute demo video and a public GitHub repository with clear setup instructions (plus a keyless/replay mode if your app needs special hardware or external setup).</td>
        </tr>
        <tr data-qacat="Video & Repo">
          <td><span class="qa-cat-badge">Video &amp; Repo</span><br/>What if we started from an existing codebase or startup product?</td>
          <td>Only work built during the hackathon window (<code>Oct 26 &ndash; Nov 4</code>) is evaluated. Organizers recommend submitting a <strong>clean standalone repository created during the hackathon</strong> containing the new module/application, and clearly stating in the first line of your video and README what existed prior vs. what was built this week.</td>
        </tr>
        <tr data-qacat="Tracks & Teams">
          <td><span class="qa-cat-badge">Tracks &amp; Teams</span><br/>Can I switch between Indie and Startup track, or switch between Build for Your World and Push the Frontier?</td>
          <td><strong>Yes.</strong> You make your final track and problem-statement selection directly on the Cerebral Valley submission form (regardless of what you selected when registering).</td>
        </tr>
        <tr data-qacat="Tracks & Teams">
          <td><span class="qa-cat-badge">Tracks &amp; Teams</span><br/>Who qualifies for the Startup Track vs. Indie Developer Track?</td>
          <td><strong>Startup Track</strong> requires a legally incorporated company in your country of origin with the ability to employ people (e.g. US EIN / Tax ID; solo incorporated founders may enter Startup). Unincorporated individuals and teams must enter the <strong>Indie Developer Track</strong>.</td>
        </tr>
        <tr data-qacat="Tracks & Teams">
          <td><span class="qa-cat-badge">Tracks &amp; Teams</span><br/>Can a teammate who wasn&rsquo;t accepted to the hackathon contribute code?</td>
          <td><strong>No.</strong> Every contributor to the repository and every listed team member (maximum 4 people per team) must be an individually approved hackathon participant, and each participant can only be on <strong>one team / one submission</strong>.</td>
        </tr>
      </tbody>
    </table>
  </section>

</main>

<footer>
  Unofficial community checklist maintained by <a href="https://watt-mind.com" target="_blank" rel="noopener">Watt Mind</a> &middot; <a href="/meta-hackathon-2026/">Return to Unofficial Project Directory</a>
</footer>

<script>
(function() {{
  const STORAGE_KEY = 'wm_meta_hackathon_2026_checklist_v2';
  const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"][data-cl]'));
  const fillEl = document.getElementById('rb-fill');
  const countTxt = document.getElementById('rb-count-txt');
  const pctTxt = document.getElementById('rb-pct-txt');
  const navReadyPill = document.getElementById('nav-ready-pill');
  const resetBtn = document.getElementById('btn-reset-cl');
  const checkAllBtn = document.getElementById('btn-check-all');

  let saved = {{}};
  try {{
    saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}') || {{}};
  }} catch (e) {{
    saved = {{}};
  }}

  function saveState() {{
    try {{
      localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
    }} catch (e) {{}}
  }}

  function updateUI() {{
    const total = checkboxes.length;
    let done = 0;
    checkboxes.forEach(cb => {{
      const item = cb.closest('.cl-item');
      if (cb.checked) {{
        done++;
        if (item) item.classList.add('checked');
      }} else {{
        if (item) item.classList.remove('checked');
      }}
    }});

    const pct = total > 0 ? Math.round((done / total) * 100) : 0;
    if (fillEl) fillEl.style.width = pct + '%';
    if (countTxt) countTxt.innerHTML = `<strong>${{done}} / ${{total}}</strong> checklist items verified`;
    if (pctTxt) pctTxt.innerHTML = `<strong>${{pct}}%</strong> ready`;
    if (navReadyPill) navReadyPill.textContent = `${{done}}/${{total}} Ready`;

    ['video', 'repo', 'bonus', 'rules'].forEach(panelKey => {{
      const panel = document.querySelector(`.cl-panel[data-panel="${{panelKey}}"]`);
      const pill = document.getElementById(`cnt-${{panelKey}}`);
      if (!panel || !pill) return;
      const pBoxes = Array.from(panel.querySelectorAll('input[type="checkbox"][data-cl]'));
      const pDone = pBoxes.filter(b => b.checked).length;
      pill.textContent = `${{pDone}} / ${{pBoxes.length}}`;
    }});
  }}

  checkboxes.forEach(cb => {{
    const key = cb.getAttribute('data-cl');
    if (saved[key]) cb.checked = true;
    cb.addEventListener('change', () => {{
      saved[key] = cb.checked;
      saveState();
      updateUI();
    }});
  }});

  if (checkAllBtn) {{
    checkAllBtn.addEventListener('click', () => {{
      checkboxes.forEach(cb => {{
        cb.checked = true;
        saved[cb.getAttribute('data-cl')] = true;
      }});
      saveState();
      updateUI();
    }});
  }}

  if (resetBtn) {{
    resetBtn.addEventListener('click', () => {{
      checkboxes.forEach(cb => {{ cb.checked = false; }});
      saved = {{}};
      try {{
        localStorage.removeItem(STORAGE_KEY);
      }} catch (e) {{}}
      updateUI();
    }});
  }}

  updateUI();

  // Template switcher + copy button
  const copyBtn = document.getElementById('btn-copy-readme');
  const readmeCodeEl = document.getElementById('readme-tpl-code');
  const portalCodeEl = document.getElementById('portal-tpl-code');
  const tplTabs = Array.from(document.querySelectorAll('#tpl-tabs .tpl-tab'));
  let activeTpl = 'readme';

  tplTabs.forEach(tab => {{
    tab.addEventListener('click', () => {{
      activeTpl = tab.getAttribute('data-tpl') || 'readme';
      tplTabs.forEach(t => t.classList.toggle('active', t === tab));
      if (readmeCodeEl) readmeCodeEl.style.display = activeTpl === 'readme' ? '' : 'none';
      if (portalCodeEl) portalCodeEl.style.display = activeTpl === 'portal' ? '' : 'none';
    }});
  }});

  if (copyBtn) {{
    copyBtn.addEventListener('click', () => {{
      const targetEl = activeTpl === 'portal' ? portalCodeEl : readmeCodeEl;
      if (!targetEl) return;
      navigator.clipboard.writeText(targetEl.textContent || '').then(() => {{
        const orig = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {{ copyBtn.textContent = orig; }}, 1600);
      }}).catch(() => {{}});
    }});
  }}

  // Filter Q&A rows by category
  const qaTabs = Array.from(document.querySelectorAll('#qa-tabs .qa-tab'));
  const qaRows = Array.from(document.querySelectorAll('#qa-table tbody tr'));
  qaTabs.forEach(tab => {{
    tab.addEventListener('click', () => {{
      const cat = tab.getAttribute('data-qacat') || 'all';
      qaTabs.forEach(t => t.classList.toggle('active', t === tab));
      qaRows.forEach(row => {{
        const rCat = row.getAttribute('data-qacat') || '';
        row.style.display = (cat === 'all' || rCat === cat) ? '' : 'none';
      }});
    }});
  }});
}})();
</script>
</body>
</html>
"""

with open("meta_hackathon_submission_checklist.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Generated meta_hackathon_submission_checklist.html successfully!")
