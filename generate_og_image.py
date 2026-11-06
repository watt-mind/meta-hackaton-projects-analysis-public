import os
import json
import base64
import tempfile
from collections import Counter
from PIL import Image
from playwright.sync_api import sync_playwright

# Load audited project data
with open("projects_inventory_audited.json") as f:
    projects = json.load(f)

total_repos = len(projects)
active_repos = sum(1 for p in projects if p.get("commits_in_window", 0) > 0)
total_commits = sum(p.get("commits_in_window", 0) for p in projects)
live_deployments = sum(1 for p in projects if p.get("has_live_deploy"))
test_count = sum(1 for p in projects if p.get("has_tests"))
track_frontier = sum(1 for p in projects if "Push the Frontier" in p.get("track", ""))
track_world = total_repos - track_frontier
track_world_pct = (track_world / total_repos) * 100.0
track_frontier_pct = (track_frontier / total_repos) * 100.0

# Consolidate domain counts for clean category breakdown (sorted descending)
DOMAIN_MAP = {
    'Developer Tooling & Infrastructure': 'Developer Tooling & Security',
    'Developer Tooling, Infra & Security': 'Developer Tooling & Security',
    'General & Emerging Applications': 'General & Emerging Applications',
    'Multimodal Vision & Video (SAM / Vision)': 'Multimodal Vision & Video (SAM)',
    'Autonomous Agents & Workflow Automation': 'Autonomous Agents & Workflows',
    'Healthcare, Civic Tech & Sustainability': 'Healthcare, Civic & Sustainability',
    'Gaming, Entertainment & Creative Media': 'Gaming & Creative Media',
    'Voice, Speech & Audio AI': 'Voice, Speech & Audio AI',
    'Education & Knowledge Systems': 'Education & Knowledge Systems',
    'Business, Sales & Commerce': 'Business, Finance & Operations',
    'Finance, Crypto & Web3': 'Business, Finance & Operations',
    'Consumer & Productivity': 'Business, Finance & Operations',
    'Robotics, IoT & Manufacturing': 'Robotics, IoT & Hardware',
    'Legal & Compliance': 'Business, Finance & Operations',
}
cat_counts = Counter(DOMAIN_MAP.get(p.get("domain", "General & Emerging Applications"), p.get("domain", "General & Emerging Applications")) for p in projects)
palette_by_cat = {
    'Developer Tooling & Security': '#4fdbc8',
    'Business, Finance & Operations': '#2dd4bf',
    'Healthcare, Civic & Sustainability': '#14b8a6',
    'Multimodal Vision & Video (SAM)': '#0ea5e9',
    'Gaming & Creative Media': '#38bdf8',
    'Education & Knowledge Systems': '#818cf8',
    'Autonomous Agents & Workflows': '#a78bfa',
    'General & Emerging Applications': '#f59e0b',
    'Voice, Speech & Audio AI': '#64748b',
    'Robotics, IoT & Hardware': '#94a3b8',
}
domain_rows = [
    (cat, cnt, palette_by_cat.get(cat, '#4fdbc8'))
    for cat, cnt in cat_counts.most_common(8)
]

max_domain_count = max(c for _, c, _ in domain_rows)

# Load Watt Mind logo as base64
logo_b64 = ""
for logo_path in ["watt-mind-logo.png"]:
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as lf:
            logo_b64 = base64.b64encode(lf.read()).decode("ascii")
        break

logo_img_tag = (
    f'<img src="data:image/png;base64,{logo_b64}" class="brand-logo" alt="Watt Mind" />'
    if logo_b64
    else '<div class="brand-logo-fallback">WM</div>'
)

bars_html = ""
for label, count, color in domain_rows:
    pct = (count / total_repos) * 100.0
    bar_w = max(6, (count / max_domain_count) * 100.0)
    bars_html += f"""
    <div class="domain-row">
      <div class="domain-meta">
        <span class="domain-name">{label}</span>
        <span class="domain-stat"><strong>{count}</strong> <span class="pct">{pct:.1f}%</span></span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width: {bar_w:.1f}%; background: {color};"></div>
      </div>
    </div>
    """

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    width: 1200px;
    height: 630px;
    overflow: hidden;
    background-color: #0c1210;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #eef4f2;
    position: relative;
    -webkit-font-smoothing: antialiased;
  }}

  /* Subtle Hairline Grid */
  .bg-grid {{
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(to right, rgba(255, 255, 255, 0.025) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
    background-size: 40px 40px;
    z-index: 1;
  }}

  .glow-left {{
    position: absolute;
    top: -160px;
    left: -120px;
    width: 640px;
    height: 640px;
    background: radial-gradient(circle, rgba(79, 219, 200, 0.09) 0%, rgba(12, 18, 16, 0) 70%);
    z-index: 2;
    pointer-events: none;
  }}

  .top-bar {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: #4fdbc8;
    z-index: 10;
  }}

  .frame-border {{
    position: absolute;
    inset: 0;
    border: 1px solid rgba(255, 255, 255, 0.08);
    z-index: 9;
    pointer-events: none;
  }}

  .canvas {{
    position: relative;
    z-index: 5;
    display: grid;
    grid-template-columns: 610px 1fr;
    gap: 40px;
    height: 100%;
    padding: 48px 52px 44px 54px;
    align-items: stretch;
  }}

  .col-left {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}

  .brand-row {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .brand-logo {{
    width: 34px;
    height: 34px;
    object-fit: contain;
  }}
  .brand-text {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .brand-text .sep {{
    color: #3b4d47;
    font-weight: 400;
  }}
  .brand-text .sub {{
    font-family: 'Inter', sans-serif;
    color: #8fa39d;
    font-weight: 500;
    font-size: 14px;
  }}
  .unofficial-og-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #fbbf24;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 5px;
    padding: 3px 9px;
  }}

  .hero-block {{
    margin-top: 4px;
  }}

  .eyebrow-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(79, 219, 200, 0.08);
    border: 1px solid rgba(79, 219, 200, 0.24);
    border-radius: 6px;
    padding: 5px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 500;
    color: #4fdbc8;
    margin-bottom: 18px;
    font-variant-numeric: tabular-nums;
  }}
  .pulse-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #4fdbc8;
  }}

  h1 {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 48px;
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.03em;
    color: #ffffff;
    margin-bottom: 18px;
  }}
  h1 .accent {{
    color: #4fdbc8;
  }}

  .subtitle {{
    font-size: 19px;
    line-height: 1.5;
    font-weight: 400;
    color: #9cb0aa;
    max-width: 580px;
  }}
  .subtitle strong {{
    color: #eef4f2;
    font-weight: 600;
  }}

  .feature-strip {{
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}
  .pills-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }}
  .stat-pill {{
    background: #131b18;
    border: 1px solid #22302c;
    border-radius: 8px;
    padding: 11px 14px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .stat-pill .val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 19px;
    font-weight: 700;
    color: #ffffff;
    font-variant-numeric: tabular-nums;
  }}
  .stat-pill .lbl {{
    font-size: 12px;
    color: #849993;
    font-weight: 500;
  }}

  .footer-meta {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    color: #748882;
  }}
  .footer-url {{
    color: #4fdbc8;
    font-weight: 500;
  }}

  /* Right Column: Category Breakdown Card */
  .col-right {{
    display: flex;
    flex-direction: column;
  }}
  .category-card {{
    flex: 1;
    background: #121917;
    border: 1px solid #22302c;
    border-radius: 10px;
    padding: 22px 24px 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}

  .card-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 12px;
    border-bottom: 1px solid #1c2824;
  }}
  .card-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13.5px;
    font-weight: 700;
    color: #e2ece9;
  }}
  .card-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
    font-weight: 500;
    color: #8fa39d;
    font-variant-numeric: tabular-nums;
  }}

  .domains-list {{
    display: flex;
    flex-direction: column;
    gap: 11px;
    margin: 12px 0;
  }}
  .domain-row {{
    display: flex;
    flex-direction: column;
    gap: 5px;
  }}
  .domain-meta {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 12.5px;
  }}
  .domain-name {{
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    color: #d0dfda;
  }}
  .domain-stat {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #ffffff;
    font-variant-numeric: tabular-nums;
  }}
  .domain-stat .pct {{
    color: #748882;
    font-weight: 400;
    font-size: 11px;
    margin-left: 4px;
  }}
  .bar-track {{
    width: 100%;
    height: 5px;
    background: #1a2421;
    border-radius: 2px;
    overflow: hidden;
  }}
  .bar-fill {{
    height: 100%;
    border-radius: 2px;
  }}

  .card-footer-stats {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 12px;
    border-top: 1px solid #1c2824;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
    color: #849993;
    font-variant-numeric: tabular-nums;
  }}
  .card-footer-stats strong {{
    color: #eef4f2;
    font-weight: 600;
  }}
</style>
</head>
<body>
  <div class="bg-grid"></div>
  <div class="glow-left"></div>
  <div class="top-bar"></div>
  <div class="frame-border"></div>

  <div class="canvas">
    <!-- Left Column -->
    <div class="col-left">
      <div class="brand-row">
        {logo_img_tag}
        <div class="brand-text">
          <span>Watt Mind</span>
          <span class="sep">&middot;</span>
          <span class="sub">Unofficial Community Tracker</span>
          <span class="unofficial-og-badge">Unofficial &middot; Auto Telemetry</span>
        </div>
      </div>

      <div class="hero-block">
        <div class="eyebrow-pill">
          <span class="pulse-dot"></span>
          <span>UNOFFICIAL INDEX &middot; {total_repos} public repos &middot; {total_commits:,} commits</span>
        </div>
        <h1>
          Unofficial Meta Global AI<br/>
          Hackathon 2026<br/>
          <span class="accent">Project Directory</span>
        </h1>
        <p class="subtitle">
          <strong>Unofficial community index</strong> of {total_repos} public hackathon repositories &mdash; automated GitHub telemetry by category, track, tests, and live demos.
        </p>
      </div>

      <div class="feature-strip">
        <div class="pills-row">
          <div class="stat-pill">
            <span class="val">{active_repos}</span>
            <span class="lbl">Active since Oct 26</span>
          </div>
          <div class="stat-pill">
            <span class="val">{test_count}</span>
            <span class="lbl">Automated tests</span>
          </div>
          <div class="stat-pill">
            <span class="val">{live_deployments}</span>
            <span class="lbl">Live deployments</span>
          </div>
        </div>
        <div class="footer-meta">
          <span class="footer-url">artifacts.watt-mind.com/meta-hackathon-2026</span>
          <span>&middot;</span>
          <span>Not affiliated with Meta / CV</span>
        </div>
      </div>
    </div>

    <!-- Right Column -->
    <div class="col-right">
      <div class="category-card">
        <div class="card-header">
          <span class="card-title">Projects by Category</span>
          <span class="card-badge">{total_repos} repositories</span>
        </div>

        <div class="domains-list">
          {bars_html}
        </div>

        <div class="card-footer-stats">
          <span>Track 1: <strong>{track_world}</strong> ({track_world_pct:.1f}%)</span>
          <span>&middot;</span>
          <span>Track 2: <strong>{track_frontier}</strong> ({track_frontier_pct:.1f}%)</span>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""

with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
    tmp.write(html)
    tmp_path = tmp.name

checklist_og_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    width: 1200px;
    height: 630px;
    overflow: hidden;
    background-color: #0c1210;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #eef4f2;
    position: relative;
    -webkit-font-smoothing: antialiased;
  }}
  .bg-grid {{
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(to right, rgba(255, 255, 255, 0.025) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
    background-size: 40px 40px;
    z-index: 1;
  }}
  .glow-left {{
    position: absolute;
    top: -160px;
    left: -120px;
    width: 640px;
    height: 640px;
    background: radial-gradient(circle, rgba(79, 219, 200, 0.1) 0%, rgba(12, 18, 16, 0) 70%);
    z-index: 2;
    pointer-events: none;
  }}
  .top-bar {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #4fdbc8 0%, #38bdf8 55%, #f59e0b 100%);
    z-index: 10;
  }}
  .frame-border {{
    position: absolute;
    inset: 0;
    border: 1px solid rgba(255, 255, 255, 0.08);
    z-index: 9;
    pointer-events: none;
  }}
  .canvas {{
    position: relative;
    z-index: 5;
    display: grid;
    grid-template-columns: 590px 1fr;
    gap: 38px;
    height: 100%;
    padding: 46px 50px 42px 52px;
    align-items: stretch;
  }}
  .col-left {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .brand-row {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .brand-logo {{
    width: 34px;
    height: 34px;
    object-fit: contain;
  }}
  .brand-text {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 9px;
  }}
  .brand-text .sep {{
    color: #3b4d47;
    font-weight: 400;
  }}
  .brand-text .sub {{
    font-family: 'Inter', sans-serif;
    color: #8fa39d;
    font-weight: 500;
    font-size: 13.5px;
  }}
  .unofficial-og-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #fbbf24;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 5px;
    padding: 3px 8px;
  }}
  .hero-block {{
    margin-top: 2px;
  }}
  .eyebrow-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(79, 219, 200, 0.09);
    border: 1px solid rgba(79, 219, 200, 0.28);
    border-radius: 6px;
    padding: 5px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
    font-weight: 600;
    color: #4fdbc8;
    margin-bottom: 16px;
  }}
  .pulse-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #4fdbc8;
  }}
  h1 {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 46px;
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.03em;
    color: #ffffff;
    margin-bottom: 16px;
  }}
  h1 .accent {{
    color: #4fdbc8;
  }}
  .subtitle {{
    font-size: 18px;
    line-height: 1.48;
    font-weight: 400;
    color: #9cb0aa;
    max-width: 570px;
  }}
  .subtitle strong {{
    color: #eef4f2;
    font-weight: 600;
  }}
  .feature-strip {{
    display: flex;
    flex-direction: column;
    gap: 15px;
  }}
  .pills-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }}
  .stat-pill {{
    background: #131b18;
    border: 1px solid #22302c;
    border-radius: 8px;
    padding: 11px 14px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .stat-pill .val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
  }}
  .stat-pill .val.teal {{ color: #4fdbc8; }}
  .stat-pill .val.amber {{ color: #fbbf24; }}
  .stat-pill .lbl {{
    font-size: 12px;
    color: #849993;
    font-weight: 500;
  }}
  .footer-meta {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #748882;
  }}
  .footer-url {{
    color: #4fdbc8;
    font-weight: 500;
  }}
  /* Right Column */
  .col-right {{
    display: flex;
    flex-direction: column;
  }}
  .blueprint-card {{
    flex: 1;
    background: #121917;
    border: 1px solid #22302c;
    border-radius: 10px;
    padding: 20px 22px 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .card-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 10px;
    border-bottom: 1px solid #1c2824;
  }}
  .card-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 13.5px;
    font-weight: 700;
    color: #e2ece9;
    white-space: nowrap;
  }}
  .card-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    color: #4fdbc8;
    background: rgba(79, 219, 200, 0.1);
    border: 1px solid rgba(79, 219, 200, 0.28);
    padding: 2px 8px;
    border-radius: 4px;
    white-space: nowrap;
  }}
  .rubric-bars {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin-top: 10px;
  }}
  .rb-box {{
    background: #0d1412;
    border: 1px solid #1e2c28;
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }}
  .rb-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11.5px;
    font-weight: 600;
    color: #dde8e4;
  }}
  .rb-wt {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #4fdbc8;
  }}
  .rb-bar {{
    height: 4px;
    background: #1a2421;
    border-radius: 2px;
    overflow: hidden;
  }}
  .rb-fill {{
    height: 100%;
    border-radius: 2px;
  }}
  .check-list {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin: 10px 0;
  }}
  .chk-row {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    background: #0d1412;
    border: 1px solid #1e2c28;
    border-radius: 7px;
    padding: 9px 11px;
  }}
  .chk-box {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    background: #4fdbc8;
    color: #09110e;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 1px;
  }}
  .chk-txt {{
    font-size: 12px;
    line-height: 1.38;
    color: #a5b8b2;
    flex: 1;
  }}
  .chk-txt strong {{
    color: #ffffff;
    font-weight: 600;
  }}
  .chk-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    white-space: nowrap;
    flex-shrink: 0;
  }}
  .chk-tag.crit {{
    color: #fecaca;
    background: rgba(248, 113, 113, 0.14);
    border: 1px solid rgba(248, 113, 113, 0.3);
  }}
  .chk-tag.bonus {{
    color: #fde68a;
    background: rgba(245, 158, 11, 0.14);
    border: 1px solid rgba(245, 158, 11, 0.3);
  }}
  .chk-tag.info {{
    color: #bae6fd;
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.28);
  }}
  .card-footer-stats {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 10px;
    border-top: 1px solid #1c2824;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #849993;
  }}
  .card-footer-stats strong {{
    color: #eef4f2;
    font-weight: 600;
  }}
</style>
</head>
<body>
  <div class="bg-grid"></div>
  <div class="glow-left"></div>
  <div class="top-bar"></div>
  <div class="frame-border"></div>

  <div class="canvas">
    <!-- Left Column -->
    <div class="col-left">
      <div class="brand-row">
        {logo_img_tag}
        <div class="brand-text">
          <span>Watt Mind</span>
          <span class="sep">&middot;</span>
          <span class="sub">Unofficial Community Guide</span>
          <span class="unofficial-og-badge">Unofficial &middot; 580+ Q&amp;A</span>
        </div>
      </div>

      <div class="hero-block">
        <div class="eyebrow-pill">
          <span class="pulse-dot"></span>
          <span>FREEZE: WED NOV 4, 21:00 EST &middot; 20-PT READINESS CHECKLIST</span>
        </div>
        <h1>
          Meta Global AI<br/>
          Hackathon 2026<br/>
          <span class="accent">Submission Checklist</span>
        </h1>
        <p class="subtitle">
          <strong>Unofficial pre-submission checklist</strong> distilled from 580+ answered Discord Q&amp;A threads &mdash; 3-stage judging workflow, 3:00 video cutoff, manual bonus prize flagging &amp; README templates.
        </p>
      </div>

      <div class="feature-strip">
        <div class="pills-row">
          <div class="stat-pill">
            <span class="val teal">20 Checks</span>
            <span class="lbl">4 Core Pillars</span>
          </div>
          <div class="stat-pill">
            <span class="val amber">&le; 3:00 Cap</span>
            <span class="lbl">Hard Video Cutoff</span>
          </div>
          <div class="stat-pill">
            <span class="val">12 Rulings</span>
            <span class="lbl">Official Q&amp;A Table</span>
          </div>
        </div>
        <div class="footer-meta">
          <span class="footer-url">artifacts.watt-mind.com/meta-hackathon-2026/checklist</span>
          <span>&middot;</span>
          <span>Not affiliated with Meta</span>
        </div>
      </div>
    </div>

    <!-- Right Column -->
    <div class="col-right">
      <div class="blueprint-card">
        <div class="card-header">
          <span class="card-title">Rubric Weights &amp; Key Submission Checks</span>
          <span class="card-badge">30/25/20/25 Split</span>
        </div>

        <div class="rubric-bars">
          <div class="rb-box">
            <div class="rb-top"><span>1. Impact</span><span class="rb-wt">30% &middot; 3.0p</span></div>
            <div class="rb-bar"><div class="rb-fill" style="width:100%;background:#4fdbc8;"></div></div>
          </div>
          <div class="rb-box">
            <div class="rb-top"><span>2. Meta AI Tooling</span><span class="rb-wt">25% &middot; 2.5p</span></div>
            <div class="rb-bar"><div class="rb-fill" style="width:83%;background:#2dd4bf;"></div></div>
          </div>
          <div class="rb-box">
            <div class="rb-top"><span>3. Demo &amp; Repo</span><span class="rb-wt">25% &middot; 2.5p</span></div>
            <div class="rb-bar"><div class="rb-fill" style="width:83%;background:#38bdf8;"></div></div>
          </div>
          <div class="rb-box">
            <div class="rb-top"><span>4. Technical Depth</span><span class="rb-wt">20% &middot; 2.0p</span></div>
            <div class="rb-bar"><div class="rb-fill" style="width:67%;background:#a78bfa;"></div></div>
          </div>
        </div>

        <div class="check-list">
          <div class="chk-row">
            <div class="chk-box">&#10003;</div>
            <div class="chk-txt"><strong>3:00 Video Cutoff:</strong> Judges stop playback at 3:00; open with 1-line Oct 26&ndash;Nov 4 provenance</div>
            <span class="chk-tag crit">Hard Stop</span>
          </div>
          <div class="chk-row">
            <div class="chk-box">&#10003;</div>
            <div class="chk-txt"><strong>Manual Bonus Flagging:</strong> State $10k Open Weights &amp; Agentic targets in README + form</div>
            <span class="chk-tag bonus">No Checkbox</span>
          </div>
          <div class="chk-row">
            <div class="chk-box">&#10003;</div>
            <div class="chk-txt"><strong>Runnable Public Repo:</strong> Quickstart, <code>.env.example</code>, keyless replay &amp; <code>LICENSE</code></div>
            <span class="chk-tag info">Zero Friction</span>
          </div>
          <div class="chk-row">
            <div class="chk-box">&#10003;</div>
            <div class="chk-txt"><strong>Nov 9 Live Finals:</strong> No live pitch or Q&amp;A &mdash; Top 5 Indie &amp; Top 5 Startup videos air live on stream</div>
            <span class="chk-tag bonus">Prizes Stack</span>
          </div>
        </div>

        <div class="card-footer-stats">
          <span>Stage 1: <strong>Nov 5&ndash;6</strong> Triage</span>
          <span>&middot;</span>
          <span>Stage 2: <strong>Nov 6&ndash;8</strong> Rubric</span>
          <span>&middot;</span>
          <span>Finals: <strong>Nov 9</strong></span>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""

with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp_cl:
    tmp_cl.write(checklist_og_html)
    tmp_cl_path = tmp_cl.name

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=2)
        page.goto(f"file://{tmp_path}", wait_until="networkidle")
        page.wait_for_timeout(300)
        hi_res_path = tmp_path + "_2x.png"
        page.screenshot(path=hi_res_path, full_page=False)

        page.goto(f"file://{tmp_cl_path}", wait_until="networkidle")
        page.wait_for_timeout(300)
        hi_res_cl_path = tmp_cl_path + "_2x.png"
        page.screenshot(path=hi_res_cl_path, full_page=False)
        browser.close()

    img = Image.open(hi_res_path).convert("RGBA")
    img_1x = img.resize((1200, 630), Image.Resampling.LANCZOS)
    img_1x.save("og-image.png", "PNG", optimize=True)
    if os.path.exists(hi_res_path):
        os.remove(hi_res_path)
    print("Saved og-image.png successfully (1200x630)")

    img_cl = Image.open(hi_res_cl_path).convert("RGBA")
    img_cl_1x = img_cl.resize((1200, 630), Image.Resampling.LANCZOS)
    img_cl_1x.save("og-checklist.png", "PNG", optimize=True)
    if os.path.exists(hi_res_cl_path):
        os.remove(hi_res_cl_path)
    print("Saved og-checklist.png successfully (1200x630)")
except Exception as e:
    print(f"Warning: Playwright OG image render skipped ({e}); keeping existing OG images.")
finally:
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    if os.path.exists(tmp_cl_path):
        os.remove(tmp_cl_path)
