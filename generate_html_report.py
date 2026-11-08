import json
import base64
import argparse
from collections import Counter

# Load audited projects
with open('projects_inventory_audited.json') as f:
    projects = json.load(f)

raw_audit_map = {}
try:
    with open('audit_results_raw.json') as f:
        raw_audit_map = json.load(f)
except Exception:
    raw_audit_map = {}

video_audit_map = {}
try:
    with open('video_audit_results.json') as f:
        video_audit_map = json.load(f)
except Exception:
    video_audit_map = {}

timeseries_data = []
try:
    with open('history/timeseries.json') as f:
        timeseries_data = json.load(f)
except Exception:
    timeseries_data = []

fonts_b64 = {}
try:
    with open('fonts_b64.json') as f:
        fonts_b64 = json.load(f)
except Exception:
    fonts_b64 = {}
font_inter_src = f"url(data:font/woff2;base64,{fonts_b64['inter']})" if 'inter' in fonts_b64 else "url(https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7W0Q5nw.woff2)"
font_jbmono_src = f"url(data:font/woff2;base64,{fonts_b64['jbmono']})" if 'jbmono' in fonts_b64 else "url(https://fonts.gstatic.com/s/jetbrainsmono/v24/tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPxDcwgknk-4.woff2)"
font_jakarta_src = f"url(data:font/woff2;base64,{fonts_b64['jakarta']})" if 'jakarta' in fonts_b64 else "url(https://fonts.gstatic.com/s/plusjakartasans/v12/LDIoaomQNQcsA88c7O9yZ4KMCoOg4Ko20yygg_vb.woff2)"

# Normalize domain names cleanly so there are no duplicate/fragmented labels
DOMAIN_MAP = {
    'Developer Tooling & Infrastructure': 'Developer Tooling, Infra & Security',
    'Developer Tooling, Infra & Security': 'Developer Tooling, Infra & Security',
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

for p in projects:
    raw_d = p.get('domain', 'General & Emerging Applications')
    p['category'] = DOMAIN_MAP.get(raw_d, raw_d)
    p['track_short'] = 'Track 2' if 'Push the Frontier' in p.get('track', '') else 'Track 1'
    p['track_label'] = 'Track 2: Push the Frontier' if 'Push the Frontier' in p.get('track', '') else 'Track 1: Build for Your World'

# Sort projects: highest score_total first, then commits_in_window descending, then stars
projects_sorted = sorted(
    projects,
    key=lambda x: (x.get('score_total', 0), x.get('commits_in_window', 0), x.get('stars', 0)),
    reverse=True
)

total_repos = len(projects)
total_commits = sum(p.get('commits_in_window', 0) for p in projects)
active_in_window = sum(1 for p in projects if p.get('commits_in_window', 0) > 0)
ghost_repos = sum(1 for p in projects if p.get('commits_in_window', 0) == 0)
high_velocity = sum(1 for p in projects if p.get('commits_in_window', 0) >= 20)
track_frontier = sum(1 for p in projects if p['track_short'] == 'Track 2')
track_world = sum(1 for p in projects if p['track_short'] == 'Track 1')
video_demos = sum(1 for p in projects if p.get('has_video_demo'))
live_deployments = sum(1 for p in projects if p.get('has_live_deploy'))
docker_count = sum(1 for p in projects if p.get('has_docker'))
test_count = sum(1 for p in projects if p.get('has_tests'))
open_weights_count = sum(1 for p in projects if p.get('open_weights_tuning'))
pr_workflow_count = sum(1 for p in projects if (p.get('prs_merged', 0) or p.get('prs_total', 0)) > 0)
preexisting_count = sum(1 for p in projects if p.get('is_preexisting') or p.get('commits_before_window', 0) > 0)
clean_slate_count = total_repos - preexisting_count
multimodal_count = sum(
    1 for p in projects
    if 'multimodal' in p.get('domain', '').lower()
    or 'vision' in p.get('domain', '').lower()
    or 'audio' in p.get('domain', '').lower()
)

category_counts = Counter(p['category'] for p in projects)
palette_by_cat = {
    'General & Emerging Applications': '#4fdbc8',
    'Multimodal Vision & Video (SAM)': '#2dd4bf',
    'Autonomous Agents & Workflows': '#14b8a6',
    'Healthcare, Civic & Sustainability': '#0ea5e9',
    'Gaming & Creative Media': '#38bdf8',
    'Voice, Speech & Audio AI': '#818cf8',
    'Developer Tooling, Infra & Security': '#a78bfa',
    'Business, Finance & Operations': '#64748b',
    'Education & Knowledge Systems': '#f59e0b',
    'Robotics, IoT & Hardware': '#94a3b8',
}
ordered_categories = sorted(
    [(cat, palette_by_cat.get(cat, '#4fdbc8')) for cat in category_counts if category_counts[cat] > 0],
    key=lambda x: category_counts[x[0]],
    reverse=True
)
max_cat_count = max(category_counts[cat] for cat, _ in ordered_categories)

parser = argparse.ArgumentParser()
parser.add_argument('--logo', help='Optional path to a Watt Mind logo PNG')
args = parser.parse_args()
logo_path = args.logo or 'watt-mind-logo.png'
logo_html = ''
try:
    with open(logo_path, 'rb') as f:
        logo_base64 = base64.b64encode(f.read()).decode('ascii')
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="Watt Mind" width="24" height="24">'
except Exception:
    logo_html = ''

track_world_pct = (track_world / total_repos) * 100
track_frontier_pct = (track_frontier / total_repos) * 100
odds_ratio = (5 / track_frontier) / (5 / track_world)


def format_live_cell(p):
    if not p.get('has_live_deploy'):
        return '<span class="cell-dash">&mdash;</span>'
    urls = p.get('live_urls') or []
    for u in urls:
        u_clean = u.strip()
        if u_clean.startswith('http://') or u_clean.startswith('https://'):
            return f'<a href="{u_clean}" target="_blank" rel="noopener" class="sig-link">Live &#8599;</a>'
        if '/' in u_clean or u_clean.count('.') >= 2:
            return f'<a href="https://{u_clean}" target="_blank" rel="noopener" class="sig-link">Live &#8599;</a>'
    if urls:
        host = urls[0].replace('.app', '').replace('.run', '').replace('.dev', '')
        return f'<span class="sig-check" title="Referenced host: {urls[0]}">&#10003; <span class="sig-host">{host}</span></span>'
    return '<span class="sig-check">&#10003;</span>'


def format_video_cell(p):
    if not p.get('has_video_demo'):
        return '<span class="cell-dash">&mdash;</span>'
    urls = p.get('video_urls') or []
    link_html = '<span class="sig-check">&#10003;</span>'
    for u in urls:
        u_clean = u.strip()
        if u_clean.startswith('http://') or u_clean.startswith('https://'):
            link_html = f'<a href="{u_clean}" target="_blank" rel="noopener" class="sig-link">Video &#8599;</a>'
            break
        if '/' in u_clean:
            link_html = f'<a href="https://{u_clean}" target="_blank" rel="noopener" class="sig-link">Video &#8599;</a>'
            break
    va_entry = video_audit_map.get(p['full_name'])
    if va_entry:
        st = va_entry.get('status')
        if st == 'audited':
            ev = va_entry.get('muse_spark_1_3_eval') or {}
            tr = ev.get('transparent_rubric') or {}
            vs = float(tr.get('total_score', ev.get('final_video_score', 0.0)))
            v_cls = 'vid-score-pill high' if vs >= 2.0 else ('vid-score-pill mid' if vs >= 1.3 else 'vid-score-pill low')
            return f'<div class="vid-cell-wrap">{link_html}<span class="{v_cls}" data-video-repo="{p["full_name"]}" tabindex="0" role="button" aria-label="Video score breakdown for {p["full_name"]}">{vs:.2f}</span></div>'
        elif st == 'download_failed':
            return f'<div class="vid-cell-wrap">{link_html}<span class="vid-score-pill dead" data-video-repo="{p["full_name"]}" tabindex="0" role="button" aria-label="Unplayable or placeholder video link for {p["full_name"]}">0.00 &#9888;</span></div>'
    return link_html


PARTNER_BADGE_SPECS = [
    ("baseten", "Baseten", "baseten_in_deps"),
    ("fireworks", "Fireworks", "fireworks_in_deps"),
    ("modal", "Modal", "modal_in_deps"),
    ("together", "Together", "together_in_deps"),
]


def format_partner_badges_py(full_name):
    ra = raw_audit_map.get(full_name, {})
    pills = []
    for p_key, p_lbl, p_field in PARTNER_BADGE_SPECS:
        if ra.get(p_field):
            pills.append(
                f'<button type="button" class="partner-tag pt-{p_key}" data-partner="{p_key}" title="Partner Inference: {p_lbl} (click to filter directory)">{p_lbl}</button>'
            )
    return f'<span class="partner-tags-wrap">{"".join(pills)}</span>' if pills else ''


def build_initial_directory_rows(proj_list, limit=50):
    rows = []
    for p in proj_list[:limit]:
        parts = p['full_name'].split('/', 1)
        owner = parts[0] + '/' if len(parts) == 2 else ''
        repo_name = parts[1] if len(parts) == 2 else p['full_name']
        stars_html = f'<span class="repo-stars" title="{p["stars"]} GitHub stars">&#9733; {p["stars"]}</span>' if p.get('stars', 0) > 0 else ''
        if p.get('is_multi_repo') and p.get('repo_count', 1) > 1:
            lr_parts = [f"{lr['full_name'].split('/')[-1]} ({lr.get('commits_in_window', 0)}c, {lr.get('prs_merged') or lr.get('prs_total', 0)} PRs)" for lr in (p.get('linked_repos') or [])]
            mr_tip = f"Multi-repo workspace ({p['repo_count']} repositories aggregated): " + " · ".join(lr_parts)
            mr_html = f'<span class="multi-repo-badge" title="{mr_tip}">{p["repo_count"]} repos</span>'
        else:
            mr_html = ''
        trk_badge = '<span class="trk-tag t2" title="Track 2: Push the Frontier">T2</span>' if p['track_short'] == 'Track 2' else '<span class="trk-tag t1" title="Track 1: Build for Your World">T1</span>'
        score_cls = 'score-pill high' if p['score_total'] >= 7.0 else ('score-pill mid' if p['score_total'] >= 5.5 else 'score-pill')
        score_tip = f"Impact: {p.get('score_impact', 0)}/3.0 · Meta AI: {p.get('score_meta_tooling', 0)}/2.5 · Tech: {p.get('score_tech_depth', 0)}/2.0 · Demo: {p.get('score_demo', 0)}/2.5"

        c_delta = p.get('commits_delta', 0)
        c_delta_html = f'<span class="delta-up">+{c_delta}</span>' if c_delta and c_delta > 0 else ''

        pre_commits = p.get('commits_before_window', 0)
        is_pre = bool(p.get('is_preexisting') or pre_commits > 0)
        created_date = (p.get('created_at') or '')[:10]
        if pre_commits > 0:
            pre_html = f'<span class="pre-badge" title="{pre_commits} commits before Oct 26, 2026 (repo created {created_date})">{pre_commits} pre</span>'
        elif is_pre:
            pre_html = f'<span class="pre-badge" title="Repository created before Oct 26, 2026 ({created_date})">pre-Oct 26</span>'
        else:
            pre_html = ''

        prs_m = p.get('prs_merged', 0)
        prs_t = p.get('prs_total', 0)
        if prs_m > 0 or prs_t > 0:
            prs_val = prs_m if prs_m > 0 else prs_t
            prs_html = f'<span class="prs-num" title="{prs_m} merged / {prs_t} total pull requests">{prs_val}</span>'
        else:
            prs_html = '<span class="cell-dash">&mdash;</span>'

        r_delta = p.get('rank_delta', 0)
        if r_delta and r_delta > 0:
            r_delta_html = f'<span class="rank-delta up" title="Moved up {r_delta} positions">&#9650;{r_delta}</span>'
        elif r_delta and r_delta < 0:
            r_delta_html = f'<span class="rank-delta down" title="Moved down {abs(r_delta)} positions">&#9660;{abs(r_delta)}</span>'
        else:
            r_delta_html = ''

        live_html = format_live_cell(p)
        vid_html = format_video_cell(p)
        partner_html = format_partner_badges_py(p['full_name'])

        rows.append(f"""
          <tr>
            <td class="col-rank"><span class="rank-num">{p['rank']}</span>{r_delta_html}</td>
            <td class="col-repo" data-repo="{p['full_name']}">
              <a href="{p['html_url']}" target="_blank" rel="noopener" class="repo-link"><span class="repo-owner">{owner}</span><span class="repo-name">{repo_name}</span></a>
              {mr_html}{stars_html}{partner_html}
            </td>
            <td class="col-cat">
              <div class="cat-cell-wrap">
                {trk_badge}
                <span class="cat-label">{p['category']}</span>
              </div>
            </td>
            <td class="col-num"><span class="{score_cls}" data-score-repo="{p['full_name']}" tabindex="0" role="button" aria-label="Score breakdown for {p['full_name']}">{p['score_total']:.1f}</span></td>
            <td class="col-num"><span class="commits-num">{p['commits_in_window']}</span>{c_delta_html}{pre_html}</td>
            <td class="col-num">{prs_html}</td>
            <td class="col-sig">{live_html}</td>
            <td class="col-sig">{vid_html}</td>
          </tr>
        """)
    return ''.join(rows)


# Build Category rows for the Left Overview Card
category_rows_html = []
for cat, color in ordered_categories:
    cnt = category_counts[cat]
    pct = (cnt / total_repos) * 100.0
    bar_w = max(3.0, (cnt / max_cat_count) * 100.0)
    category_rows_html.append(f"""
      <button type="button" class="cat-filter-row" data-category="{cat}" title="Click to filter directory by {cat}">
        <div class="cat-row-top">
          <span class="cat-row-name">{cat}</span>
          <span class="cat-row-stats"><strong>{cnt}</strong> <span class="muted">({pct:.1f}%)</span></span>
        </div>
        <div class="bar-bg">
          <div class="bar-fg" style="width: {bar_w:.1f}%; background: {color};"></div>
        </div>
      </button>
    """)

# Build Signal rows for the Right Overview Card (sorted descending by count)
signal_items = sorted([
    ("Active since Oct 26", active_in_window, "#4fdbc8", "active"),
    ("Clean-slate repos (Oct 26+)", clean_slate_count, "#34d399", "clean"),
    ("Automated test suites", test_count, "#2dd4bf", "tests"),
    ("20+ commits in window", high_velocity, "#38bdf8", "velocity"),
    ("Uses PR workflow", pr_workflow_count, "#60a5fa", "prs"),
    ("Dockerized applications", docker_count, "#14b8a6", "docker"),
    ("Live web deployments", live_deployments, "#818cf8", "live"),
    ("Custom / local model weights", open_weights_count, "#a78bfa", "weights"),
    ("Video walkthroughs", video_demos, "#f59e0b", "video"),
], key=lambda x: x[1], reverse=True)

signal_rows_html = []
for label, cnt, color, filter_key in signal_items:
    pct = (cnt / total_repos) * 100.0
    interactive_attr = f'data-signal="{filter_key}"' if filter_key else ''
    interactive_cls = 'sig-overview-row clickable' if filter_key else 'sig-overview-row'
    signal_rows_html.append(f"""
      <div class="{interactive_cls}" {interactive_attr}>
        <div class="cat-row-top">
          <span class="cat-row-name">{label}</span>
          <span class="cat-row-stats"><strong>{cnt}</strong> <span class="muted">({pct:.1f}%)</span></span>
        </div>
        <div class="bar-bg">
          <div class="bar-fg" style="width: {max(2.0, pct):.1f}%; background: {color};"></div>
        </div>
      </div>
    """)

# Compact client-side dataset so filtering/sorting works instantaneously offline & online
def truncate_clean(text, max_len=140):
    s = (text or "").strip()
    if len(s) <= max_len:
        return s
    cut = s[:max_len].rsplit(" ", 1)[0].rstrip(".,;:-")
    return (cut or s[:max_len]) + "…"


video_perfect_count = 0
video_dead_count = 0
for _fn, _ve in video_audit_map.items():
    if _ve.get("status") == "audited":
        _ev = _ve.get("muse_spark_1_3_eval") or {}
        _tr = _ev.get("transparent_rubric") or {}
        if float(_tr.get("total_score", _ev.get("final_video_score", 0.0))) >= 2.5:
            video_perfect_count += 1
    elif _ve.get("status") == "download_failed":
        video_dead_count += 1
video_other_perfect_count = max(0, video_perfect_count - 1)

compact_projects = []
for p in projects_sorted:
    va_compact = None
    va_entry = video_audit_map.get(p["full_name"])
    if va_entry:
        if va_entry.get("status") == "audited":
            vm = va_entry.get("video_metadata") or {}
            sam = va_entry.get("sam_3_1_grounding") or {}
            ev = va_entry.get("muse_spark_1_3_eval") or {}
            tr = ev.get("transparent_rubric") or {}
            va_compact = {
                "st": "ok",
                "vs": round(float(tr.get("total_score", ev.get("final_video_score", 0.0))), 2),
                "dur": round(float(vm.get("duration_s", 0.0)), 1),
                "w3m": bool(vm.get("within_3m_limit", True)),
                "ovr": round(float(vm.get("overrun_seconds", 0.0) or 0.0), 1),
                "res": f"{vm.get('width', 0)}x{vm.get('height', 0)}" if vm.get("width") else "",
                "db": vm.get("mean_volume_db"),
                "pct": int(ev.get("product_footage_pct_estimate", 0) or 0),
                "sam": int(sam.get("total_boxes_detected", 0) or 0),
                "btn": int(sam.get("button_control_count", 0) or 0),
                "nar": ev.get("narration_type", ""),
                "cap": bool(ev.get("has_burned_in_captions")),
                "ptm": ev.get("provenance_timing") or "missing",
                "pev": truncate_clean(ev.get("provenance_evidence") or "", 135),
                "lcall": bool(ev.get("live_meta_calls_shown")),
                "mev": truncate_clean(ev.get("meta_call_evidence") or "", 150),
                "ui": (ev.get("live_ui_surfaces_seen") or [])[:2],
                "mod": (ev.get("visible_meta_models_in_video") or [])[:5],
                "bch": (ev.get("extracted_benchmark_metrics") or [])[:3],
                "str": ev.get("judge_strengths") or "",
                "wk": ev.get("judge_weaknesses_or_risks") or "",
                "c": [
                    round(float(tr.get("c1_stopwatch_compliance", 0)), 2),
                    round(float(tr.get("c2_opening_provenance", 0)), 2),
                    round(float(tr.get("c3_live_product_authenticity", 0)), 2),
                    round(float(tr.get("c4_meta_model_execution", 0)), 2),
                    round(float(tr.get("c5_quantifiable_benchmarks", 0)), 2),
                    round(float(tr.get("c6_audio_and_caption_clarity", 0)), 2),
                ],
                "bk": tr.get("breakdown") or [],
            }
        elif va_entry.get("status") == "download_failed":
            vm = va_entry.get("video_metadata") or {}
            va_compact = {
                "st": "dead",
                "vs": 0.0,
                "err": truncate_clean(vm.get("error") or "Video link unavailable, private, or placeholder URL", 200),
                "url": vm.get("primary_url") or "",
            }

    compact_projects.append({
        "r": p["rank"],
        "n": p["full_name"],
        "u": p["html_url"],
        "t": p["track_short"],
        "c": p["category"],
        "s": p["score_total"],
        "si": p.get("score_impact", 0),
        "sm": p.get("score_meta_tooling", 0),
        "st": p.get("score_tech_depth", 0),
        "sd": p.get("score_demo", 0),
        "cm": p.get("commits_in_window", 0),
        "cb": p.get("commits_before_window", 0),
        "pre": bool(p.get("is_preexisting") or p.get("commits_before_window", 0) > 0),
        "pm": p.get("prs_merged", 0),
        "pt": p.get("prs_total", 0),
        "cd": p.get("commits_delta", 0),
        "rd": p.get("rank_delta", 0),
        "st_cnt": p.get("stars", 0),
        "cr": p.get("created_at", ""),
        "lv": bool(p.get("has_live_deploy")),
        "lu": (p.get("live_urls") or [])[:1],
        "vd": bool(p.get("has_video_demo")),
        "vu": (p.get("video_urls") or [])[:1],
        "va": va_compact,
        "dk": bool(p.get("has_docker")),
        "ts": bool(p.get("has_tests")),
        "ow": bool(p.get("open_weights_tuning")),
        "mr": p.get("repo_count", 1) if p.get("is_multi_repo") else 1,
        "mt": (
            f"Multi-repo workspace ({p.get('repo_count', 1)} repositories aggregated): " +
            " · ".join(f"{lr['full_name'].split('/')[-1]} ({lr.get('commits_in_window', 0)}c, {lr.get('prs_merged') or lr.get('prs_total', 0)} PRs)" for lr in (p.get("linked_repos") or []))
        ) if p.get("is_multi_repo") else "",
        "lr": " ".join(lr.get("full_name", "") for lr in (p.get("linked_repos") or [])) if p.get("is_multi_repo") else "",
        "sm_txt": p.get("summary") or "",
        "rs": p.get("readme_summary") or p.get("summary") or "",
        "th": (p.get("tech_highlights") or [])[:3],
        "sb": p.get("score_breakdown") or {},
        "ms": [
            k for k, cond in (
                ("spark", raw_audit_map.get(p["full_name"], {}).get("readme_cites_muse_spark")),
                ("meta_api", raw_audit_map.get(p["full_name"], {}).get("meta_api_in_deps") or raw_audit_map.get(p["full_name"], {}).get("readme_cites_meta_api")),
                ("sam", raw_audit_map.get(p["full_name"], {}).get("readme_cites_sam")),
                ("wonder", raw_audit_map.get(p["full_name"], {}).get("readme_cites_muse_wonder")),
                ("code", raw_audit_map.get(p["full_name"], {}).get("readme_cites_muse_code")),
                ("glimmer", raw_audit_map.get(p["full_name"], {}).get("readme_cites_muse_glimmer")),
                ("weights", p.get("open_weights_tuning")),
                ("non_meta", raw_audit_map.get(p["full_name"], {}).get("competitor_in_deps")),
                ("baseten", raw_audit_map.get(p["full_name"], {}).get("baseten_in_deps")),
                ("fireworks", raw_audit_map.get(p["full_name"], {}).get("fireworks_in_deps")),
                ("modal", raw_audit_map.get(p["full_name"], {}).get("modal_in_deps")),
                ("together", raw_audit_map.get(p["full_name"], {}).get("together_in_deps")),
            ) if cond
        ],
    })

compact_json_str = json.dumps(compact_projects, separators=(',', ':'))

category_options_html = '\n'.join(
    f'<option value="{cat}">{cat} ({category_counts[cat]})</option>'
    for cat, _ in ordered_categories
)

# ==============================================================================
# SECOND OVERVIEW ROW: ACTIVITY OVER TIME & META AI MODEL ADOPTION
# ==============================================================================
from datetime import datetime

def parse_iso_ts(ts_str):
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00')).timestamp()
    except Exception:
        return 0.0

# Deduplicate snapshots closer than 2 hours so manual runs don't create overlapping dot clusters
raw_ts_points = timeseries_data if timeseries_data else []
ts_points = []
for idx, pt in enumerate(raw_ts_points):
    if not ts_points:
        ts_points.append(pt)
        continue
    prev_ep = parse_iso_ts(ts_points[-1]['timestamp'])
    curr_ep = parse_iso_ts(pt['timestamp'])
    # If less than 90 minutes apart, replace the previous point (unless previous was the very first baseline)
    if (curr_ep - prev_ep) < 5400 and len(ts_points) > 1:
        ts_points[-1] = pt
    else:
        ts_points.append(pt)

def build_timeseries_svg(points):
    if len(points) < 2:
        return '<div class="muted">Collecting point-in-time snapshots...</div>'
    w, h = 560, 204
    pad_l, pad_r, pad_t, pad_b = 30, 26, 12, 24
    pw = w - pad_l - pad_r
    ph = h - pad_t - pad_b

    commits_vals = [pt.get('total_commits', 0) for pt in points]
    live_vals = [pt.get('live_deployments', 0) for pt in points]
    video_vals = [pt.get('video_demos', 0) for pt in points]
    min_c = max(0, (min(commits_vals) // 2000) * 2000)
    max_c = ((max(commits_vals) // 2000) + 1) * 2000
    mid_c = (min_c + max_c) // 2

    max_l = ((max(max(live_vals + video_vals), 10) // 20) + 1) * 20
    mid_l = max_l // 2
    span_c = max(max_c - min_c, 1)

    t_epochs = [parse_iso_ts(pt['timestamp']) for pt in points]
    t_min, t_max = min(t_epochs), max(t_epochs)
    t_span = max(t_max - t_min, 1.0)

    c_coords = []
    l_coords = []
    v_coords = []
    labels_svg = []
    dots_svg = []

    for i, pt in enumerate(points):
        x = pad_l + ((t_epochs[i] - t_min) / t_span) * pw
        yc = pad_t + ph - ((pt.get('total_commits', 0) - min_c) / span_c) * ph
        yl = pad_t + ph - (pt.get('live_deployments', 0) / max_l) * ph
        yv = pad_t + ph - (pt.get('video_demos', 0) / max_l) * ph
        c_coords.append(f"{x:.1f},{yc:.1f}")
        l_coords.append(f"{x:.1f},{yl:.1f}")
        v_coords.append(f"{x:.1f},{yv:.1f}")
        ts_pretty = pt["timestamp"][5:16].replace("T", " ") + " UTC"
        dots_svg.append(
            f'<circle cx="{x:.1f}" cy="{yc:.1f}" r="3.2" fill="#0c1210" stroke="#4fdbc8" stroke-width="2">'
            f'<title>{ts_pretty} — {pt.get("total_commits", 0):,} commits across {pt.get("total_repos", 0)} repos</title></circle>'
        )
        dots_svg.append(
            f'<circle cx="{x:.1f}" cy="{yl:.1f}" r="3.0" fill="#0c1210" stroke="#818cf8" stroke-width="2">'
            f'<title>{ts_pretty} — {pt.get("live_deployments", 0)} live deployments</title></circle>'
        )
        dots_svg.append(
            f'<circle cx="{x:.1f}" cy="{yv:.1f}" r="3.0" fill="#0c1210" stroke="#f59e0b" stroke-width="2">'
            f'<title>{ts_pretty} — {pt.get("video_demos", 0)} video walkthroughs</title></circle>'
        )

    # Evenly spaced time ticks across the horizontal axis (0%, 33%, 67%, 100%)
    for frac, anchor in ((0.0, 'start'), (0.33, 'middle'), (0.67, 'middle'), (1.0, 'end')):
        tx = pad_l + frac * pw
        t_val = t_min + frac * t_span
        lbl = datetime.fromtimestamp(t_val, tz=datetime.fromisoformat(points[0]['timestamp'].replace('Z', '+00:00')).tzinfo).strftime('%b %d %H:%M')
        labels_svg.append(
            f'<text x="{tx:.1f}" y="{h - 4}" fill="#839c95" font-family="JetBrains Mono, monospace" font-size="10" text-anchor="{anchor}">{lbl}</text>'
        )

    # Vertical dashed line marking Submission Deadline & Judging Start (Nov 5, 2026 02:00 UTC / Nov 4, 6:00 PM PST)
    judging_ep = parse_iso_ts("2026-11-05T02:00:00Z")
    judging_svg = ""
    if t_min <= judging_ep <= t_max:
        jx = pad_l + ((judging_ep - t_min) / t_span) * pw
        judging_svg = f"""
      <!-- Submission Freeze / Judging Started Marker -->
      <g class="ts-judging-marker">
        <title>Submission Freeze &amp; Judging Started — Nov 5, 2026 02:00 UTC (Nov 4, 6:00 PM PST)</title>
        <line x1="{jx:.1f}" y1="{pad_t}" x2="{jx:.1f}" y2="{pad_t + ph}" stroke="#fb7185" stroke-width="1.6" stroke-dasharray="4,3" stroke-opacity="0.95"/>
      </g>"""

    area_c = f"M {pad_l},{pad_t+ph} L " + " L ".join(c_coords) + f" L {pad_l+pw},{pad_t+ph} Z"
    line_c = "M " + " L ".join(c_coords)
    line_l = "M " + " L ".join(l_coords)
    line_v = "M " + " L ".join(v_coords)

    return f"""
    <svg viewBox="0 0 {w} {h}" style="width:100%; height:auto; display:block;">
      <defs>
        <linearGradient id="gradCommits" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#4fdbc8" stop-opacity="0.22"/>
          <stop offset="100%" stop-color="#4fdbc8" stop-opacity="0.01"/>
        </linearGradient>
      </defs>
      <!-- Grid lines -->
      <line x1="{pad_l}" y1="{pad_t}" x2="{w-pad_r}" y2="{pad_t}" stroke="#1f2d29" stroke-dasharray="3,3"/>
      <line x1="{pad_l}" y1="{pad_t + ph/2:.1f}" x2="{w-pad_r}" y2="{pad_t + ph/2:.1f}" stroke="#1f2d29" stroke-dasharray="3,3"/>
      <line x1="{pad_l}" y1="{pad_t + ph}" x2="{w-pad_r}" y2="{pad_t + ph}" stroke="#2b3e38"/>

      <!-- Left Axis: Commits (flush left at x=0) -->
      <text x="0" y="{pad_t + 4}" fill="#4fdbc8" font-family="JetBrains Mono, monospace" font-size="10" text-anchor="start">{max_c/1000:.0f}k</text>
      <text x="0" y="{pad_t + ph/2 + 3:.1f}" fill="#839c95" font-family="JetBrains Mono, monospace" font-size="10" text-anchor="start">{mid_c/1000:.0f}k</text>
      <text x="0" y="{pad_t + ph}" fill="#839c95" font-family="JetBrains Mono, monospace" font-size="10" text-anchor="start">{min_c/1000:.0f}k</text>

      <!-- Right Axis: Live Apps & Video Demos (flush right at x=w) -->
      <text x="{w}" y="{pad_t + 4}" fill="#818cf8" font-family="JetBrains Mono, monospace" font-size="10" text-anchor="end">{max_l}</text>
      <text x="{w}" y="{pad_t + ph/2 + 3:.1f}" fill="#839c95" font-family="JetBrains Mono, monospace" font-size="10" text-anchor="end">{mid_l}</text>
      <text x="{w}" y="{pad_t + ph}" fill="#839c95" font-family="JetBrains Mono, monospace" font-size="10" text-anchor="end">0</text>

      <!-- Series -->
      <path d="{area_c}" fill="url(#gradCommits)"/>
      <path d="{line_c}" fill="none" stroke="#4fdbc8" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
      <path d="{line_l}" fill="none" stroke="#818cf8" stroke-width="2" stroke-dasharray="4,3" stroke-linejoin="round"/>
      <path d="{line_v}" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
      {judging_svg}
      {''.join(dots_svg)}
      {''.join(labels_svg)}
    </svg>
    """

timeseries_svg_html = build_timeseries_svg(ts_points)
first_ts = ts_points[0] if ts_points else {}
last_ts = ts_points[-1] if ts_points else {}
prev_ts = ts_points[-2] if len(ts_points) >= 2 else first_ts
ts_repo_gain = last_ts.get('total_repos', total_repos) - first_ts.get('total_repos', total_repos)
ts_commit_gain = last_ts.get('total_commits', total_commits) - first_ts.get('total_commits', total_commits)
ts_live_gain = last_ts.get('live_deployments', live_deployments) - first_ts.get('live_deployments', live_deployments)
ts_video_gain = last_ts.get('video_demos', video_demos) - first_ts.get('video_demos', video_demos)
last_4h_commits = last_ts.get('total_commits', total_commits) - prev_ts.get('total_commits', total_commits)
last_4h_repos = last_ts.get('total_repos', total_repos) - prev_ts.get('total_repos', total_repos)

# Meta AI Model & Inference Stack Adoption (Interactive filter rows)
project_names_set = {p['full_name'] for p in projects}
baseten_cnt = sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('baseten_in_deps'))
fireworks_cnt = sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('fireworks_in_deps'))
modal_cnt = sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('modal_in_deps'))
together_cnt = sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('together_in_deps'))
partner_any_cnt = sum(
    1 for fn in project_names_set
    if any(raw_audit_map.get(fn, {}).get(k) for k in ('baseten_in_deps', 'fireworks_in_deps', 'modal_in_deps', 'together_in_deps'))
)

model_counts = [
    ("Muse Spark", "spark", sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('readme_cites_muse_spark')), "#4fdbc8"),
    ("Meta Model API (api.meta.ai)", "meta_api", sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('meta_api_in_deps') or raw_audit_map.get(fn, {}).get('readme_cites_meta_api')), "#2dd4bf"),
    ("SAM 3 / Vision Segmentation", "sam", sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('readme_cites_sam')), "#38bdf8"),
    ("Muse Wonder", "wonder", sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('readme_cites_muse_wonder')), "#0ea5e9"),
    ("Muse Code", "code", sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('readme_cites_muse_code')), "#818cf8"),
    ("Muse Glimmer (Open Weights)", "glimmer", sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('readme_cites_muse_glimmer')), "#a78bfa"),
    ("Open-Weights Fine-Tuning (PEFT / vLLM)", "weights", open_weights_count, "#f59e0b"),
    ("Non-Meta SDKs (OpenAI / Anthropic)", "non_meta", sum(1 for fn in project_names_set if raw_audit_map.get(fn, {}).get('competitor_in_deps')), "#64748b"),
]
model_counts.sort(key=lambda x: x[2], reverse=True)
max_model_cnt = max((c for _, _, c, _ in model_counts), default=1)
model_bars_html = []
for m_label, m_key, m_cnt, m_col in model_counts:
    m_pct = (m_cnt / total_repos) * 100.0
    m_w = max(2.5, (m_cnt / max_model_cnt) * 100.0)
    model_bars_html.append(f"""
      <button type="button" class="cat-filter-row model-filter-row" data-model="{m_key}" title="Click to filter directory by {m_label} ({m_cnt} repositories)">
        <div class="cat-row-top">
          <span class="cat-row-name">{m_label}</span>
          <span class="cat-row-stats"><strong>{m_cnt}</strong> <span class="muted">({m_pct:.1f}%)</span></span>
        </div>
        <div class="bar-bg">
          <div class="bar-fg" style="width: {m_w:.1f}%; background: {m_col};"></div>
        </div>
      </button>
    """)

partner_overview_strip_html = f"""
      <div class="partner-overview-box">
        <div class="partner-overview-hdr">
          <span>Partner Inference Infra</span>
          <span class="muted">{partner_any_cnt} repos ({partner_any_cnt/total_repos*100:.1f}%) &middot; click to filter</span>
        </div>
        <div class="partner-overview-pills">
          <button type="button" class="partner-ov-pill model-filter-row pt-baseten" data-model="baseten" title="Filter directory by Baseten ({baseten_cnt} repositories)">
            <span class="po-name">Baseten</span>
            <span class="po-cnt">{baseten_cnt}</span>
          </button>
          <button type="button" class="partner-ov-pill model-filter-row pt-fireworks" data-model="fireworks" title="Filter directory by Fireworks AI ({fireworks_cnt} repositories)">
            <span class="po-name">Fireworks</span>
            <span class="po-cnt">{fireworks_cnt}</span>
          </button>
          <button type="button" class="partner-ov-pill model-filter-row pt-modal" data-model="modal" title="Filter directory by Modal ({modal_cnt} repositories)">
            <span class="po-name">Modal</span>
            <span class="po-cnt">{modal_cnt}</span>
          </button>
          <button type="button" class="partner-ov-pill model-filter-row pt-together" data-model="together" title="Filter directory by Together AI ({together_cnt} repositories)">
            <span class="po-name">Together</span>
            <span class="po-cnt">{together_cnt}</span>
          </button>
        </div>
      </div>
"""
model_bars_html.append(partner_overview_strip_html)

# ==============================================================================
# 1. PUBLIC COMMUNITY EDITION (Clean, Anti-Slop Engineering Directory)
# ==============================================================================
public_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Unofficial Meta Global AI Hackathon 2026 — Project Directory ({total_repos} Repositories)</title>
<meta name="description" content="Unofficial community directory of all {total_repos} public repositories in the Meta Global AI Hackathon 2026, indexed by category, track, commit activity, pull requests, test suites, containerization, and live deployments.">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230c1210'/%3E%3Cpath d='M16 4L27 10.5V21.5L16 28L5 21.5V10.5L16 4Z' fill='none' stroke='%234fdbc8' stroke-width='2.5'/%3E%3Ccircle cx='16' cy='16' r='4' fill='%234fdbc8'/%3E%3C/svg%3E">

<!-- Discord & Open Graph Meta Tags -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="Watt Mind (Unofficial Community Tracker)">
<meta property="og:title" content="Unofficial Meta Global AI Hackathon 2026 — Project Directory">
<meta property="og:description" content="Unofficial community tracker of all {total_repos} public hackathon repositories, indexed by category, commit activity, pull requests, test suites, containerization, and live deployments.">
<meta property="og:url" content="https://artifacts.watt-mind.com/meta-hackathon-2026/">
<meta property="og:image" content="https://artifacts.watt-mind.com/meta-hackathon-2026/og-image.png?v=4">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/png">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Unofficial Meta Global AI Hackathon 2026 — Project Directory">
<meta name="twitter:description" content="Unofficial community tracker of all {total_repos} public hackathon repositories, indexed by category, commit activity, pull requests, test suites, containerization, and live deployments.">
<meta name="twitter:image" content="https://artifacts.watt-mind.com/meta-hackathon-2026/og-image.png?v=4">

<meta name="theme-color" content="#4fdbc8">

<style>
  @font-face {{ font-family: 'Inter'; font-style: normal; font-weight: 400 800; font-display: block; src: url(https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa25L7W0Q5n-wU.woff2) format('woff2'); unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF; }}
  @font-face {{ font-family: 'Inter'; font-style: normal; font-weight: 400 800; font-display: block; src: {font_inter_src} format('woff2'); unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }}
  @font-face {{ font-family: 'JetBrains Mono'; font-style: normal; font-weight: 400 800; font-display: block; src: url(https://fonts.gstatic.com/s/jetbrainsmono/v24/tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPx7cwgknk-6nFg.woff2) format('woff2'); unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF; }}
  @font-face {{ font-family: 'JetBrains Mono'; font-style: normal; font-weight: 400 800; font-display: block; src: {font_jbmono_src} format('woff2'); unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }}
  @font-face {{ font-family: 'Plus Jakarta Sans'; font-style: normal; font-weight: 400 800; font-display: block; src: url(https://fonts.gstatic.com/s/plusjakartasans/v12/LDIoaomQNQcsA88c7O9yZ4KMCoOg4Ko40yygg_vbd-E.woff2) format('woff2'); unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF; }}
  @font-face {{ font-family: 'Plus Jakarta Sans'; font-style: normal; font-weight: 400 800; font-display: block; src: {font_jakarta_src} format('woff2'); unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }}

  :root {{
    --bg: #0c1210;
    --surface: #111916;
    --surface-raised: #16201d;
    --surface-hover: #1b2824;
    --border: #1f2d29;
    --border-strong: #2b3e38;
    --text: #e6efec;
    --text-secondary: #9bb0aa;
    --text-dim: #9bb0aa;
    --text-muted: #839c95;
    --accent: #4fdbc8;
    --accent-dim: rgba(79, 219, 200, 0.12);
    --font-heading: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  html, body {{
    overflow-x: clip;
  }}

  body {{
    background-color: var(--bg);
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 14px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}

  /* Top Navigation */
  .navbar {{
    background: rgba(12, 18, 16, 0.92);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 0 32px;
    height: 54px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 500;
  }}
  .nav-inner {{
    max-width: 1280px;
    width: 100%;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .nav-brand {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: #ffffff;
    font-family: var(--font-heading);
    font-weight: 700;
    font-size: 15px;
    letter-spacing: -0.01em;
  }}
  .nav-brand img {{ height: 24px; width: auto; }}
  .nav-brand .divider {{ color: var(--border-strong); font-weight: 400; margin: 0 2px; }}
  .nav-brand .product {{ color: var(--text-secondary); font-family: var(--font-sans); font-weight: 500; font-size: 13.5px; }}

  .nav-meta {{
    display: flex;
    align-items: center;
    gap: 14px;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
  }}
  .nav-meta .sep {{ color: var(--border-strong); }}
  .nav-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--accent);
    background: var(--accent-dim);
    border: 1px solid rgba(79, 219, 200, 0.25);
    padding: 3px 9px;
    border-radius: 999px;
    font-size: 11.5px;
    font-weight: 500;
  }}
  .nav-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
  }}
  .nav-countdown-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #ffffff;
    background: rgba(79, 219, 200, 0.14);
    border: 1px solid rgba(79, 219, 200, 0.38);
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 11.5px;
    font-weight: 600;
    text-decoration: none;
    transition: border-color 0.15s, background 0.15s, transform 0.12s;
  }}
  .nav-countdown-pill:hover {{
    border-color: var(--accent);
    background: rgba(79, 219, 200, 0.22);
    transform: translateY(-1px);
  }}
  .nav-countdown-pill.warn {{
    background: rgba(245, 158, 11, 0.15);
    border-color: rgba(245, 158, 11, 0.45);
    color: #fde68a;
  }}
  .nav-countdown-pill.urgent {{
    background: rgba(248, 113, 113, 0.16);
    border-color: rgba(248, 113, 113, 0.5);
    color: #fecaca;
  }}
  .cd-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 8px var(--accent);
    animation: cdPulse 2s infinite ease-in-out;
  }}
  .nav-countdown-pill.warn .cd-dot {{
    background: #f59e0b;
    box-shadow: 0 0 8px #f59e0b;
  }}
  .nav-countdown-pill.urgent .cd-dot {{
    background: #f87171;
    box-shadow: 0 0 8px #f87171;
  }}
  @keyframes cdPulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.45; transform: scale(0.85); }}
  }}
  .deadline-strip {{
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 14px 20px;
    margin-bottom: 20px;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 28px;
  }}
  .dl-left {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .dl-kicker-row {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .dl-kicker {{
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--accent);
    display: inline-flex;
    align-items: center;
    gap: 7px;
    white-space: nowrap;
  }}
  .dl-phase-tag {{
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 500;
    color: var(--text-secondary);
    background: var(--surface-raised);
    border: 1px solid var(--border);
    padding: 1px 7px;
    border-radius: 4px;
    white-space: nowrap;
  }}
  .dl-sub {{
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--text-secondary);
    white-space: nowrap;
  }}
  .dl-sub strong {{
    color: var(--text);
    font-weight: 600;
  }}
  .dl-mid {{
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 220px;
  }}
  .dl-prog-top {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-secondary);
    white-space: nowrap;
  }}
  .dl-prog-top strong {{
    color: #ffffff;
    font-weight: 600;
  }}
  .dl-bar-track {{
    height: 6px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 999px;
    overflow: hidden;
    position: relative;
  }}
  .dl-bar-fill {{
    height: 100%;
    background: linear-gradient(90deg, #0d9488 0%, #4fdbc8 100%);
    border-radius: 999px;
    transition: width 0.5s ease;
  }}
  .dl-milestones {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-muted);
    white-space: nowrap;
  }}
  .dl-right {{
    display: flex;
    align-items: center;
    gap: 14px;
    flex-shrink: 0;
  }}
  .dl-blocks {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--font-mono);
    background: var(--bg);
    border: 1px solid var(--border-strong);
    border-radius: 6px;
    padding: 5px 10px;
  }}
  .dl-unit {{
    min-width: 38px;
    text-align: center;
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 2px;
  }}
  .dl-num {{
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
    font-variant-numeric: tabular-nums;
  }}
  .dl-txt {{
    font-size: 10px;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: lowercase;
  }}
  .dl-sep {{
    color: var(--border-strong);
    font-weight: 600;
    font-size: 13px;
  }}
  .dl-submit-btn {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-weight: 600;
    color: var(--accent);
    background: rgba(79, 219, 200, 0.1);
    border: 1px solid rgba(79, 219, 200, 0.35);
    padding: 7px 12px;
    border-radius: 6px;
    text-decoration: none;
    white-space: nowrap;
    transition: background 0.15s, border-color 0.15s, color 0.15s, transform 0.12s;
    flex-shrink: 0;
  }}
  .dl-submit-btn:hover {{
    background: rgba(79, 219, 200, 0.18);
    border-color: var(--accent);
    color: #ffffff;
    transform: translateY(-1px);
  }}
  .dl-checklist-btn {{
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--text);
    background: var(--bg);
    border: 1px solid var(--border-strong);
    padding: 7px 11px;
    border-radius: 6px;
    text-decoration: none;
    white-space: nowrap;
    transition: background 0.15s, border-color 0.15s, color 0.15s, transform 0.12s;
    flex-shrink: 0;
  }}
  .dl-checklist-btn:hover {{
    border-color: var(--accent);
    color: var(--accent);
    transform: translateY(-1px);
  }}
  .nav-checklist-btn {{
    color: var(--accent);
    text-decoration: none;
    padding: 3px 9px;
    border: 1px solid rgba(79, 219, 200, 0.35);
    border-radius: 4px;
    background: rgba(79, 219, 200, 0.08);
    font-weight: 600;
    white-space: nowrap;
    transition: border-color 0.15s, background 0.15s, color 0.15s;
  }}
  .nav-checklist-btn:hover {{
    color: #ffffff;
    background: rgba(79, 219, 200, 0.18);
    border-color: var(--accent);
  }}
  .disclaimer-banner {{
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(17, 25, 22, 0.96) 55%, rgba(79, 219, 200, 0.06) 100%);
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-left: 3px solid #f59e0b;
    border-radius: 8px;
    padding: 13px 18px;
    margin-bottom: 14px;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
  }}
  .disclaimer-content {{
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 0;
  }}
  .disclaimer-title {{
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.03em;
    color: #fbbf24;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .disclaimer-tag {{
    font-size: 10.5px;
    font-weight: 600;
    color: var(--text-secondary);
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-strong);
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: none;
    letter-spacing: 0;
  }}
  .disclaimer-tag a {{
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px dashed rgba(79, 219, 200, 0.45);
  }}
  .disclaimer-tag a:hover {{
    color: #ffffff;
    border-bottom-color: #ffffff;
  }}
  .disclaimer-text {{
    font-size: 0.8125rem;
    line-height: 1.55;
    color: var(--text-secondary);
    margin: 0;
    text-wrap: pretty;
  }}
  .disclaimer-text strong {{
    color: var(--text);
    font-weight: 600;
  }}
  .disclaimer-text a {{
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px dashed rgba(79, 219, 200, 0.45);
  }}
  .disclaimer-text a:hover {{
    color: #ffffff;
    border-bottom-color: #ffffff;
  }}
  .disclaimer-cta {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: #fde68a;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.38);
    padding: 7px 12px;
    border-radius: 6px;
    text-decoration: none;
    white-space: nowrap;
    flex-shrink: 0;
    align-self: center;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
  }}
  .disclaimer-cta:hover {{
    background: rgba(245, 158, 11, 0.22);
    border-color: #fbbf24;
    color: #ffffff;
  }}
  .th-info-link {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    font-size: 9.5px;
    font-weight: 700;
    color: var(--accent);
    background: rgba(79, 219, 200, 0.14);
    border: 1px solid rgba(79, 219, 200, 0.35);
    text-decoration: none;
    margin-left: 4px;
    vertical-align: middle;
  }}
  .th-info-link:hover {{
    background: var(--accent);
    color: #0b110f;
  }}
  @media (max-width: 900px) {{
    .disclaimer-banner {{
      flex-direction: column;
      align-items: stretch;
      gap: 10px;
    }}
    .disclaimer-cta {{
      align-self: flex-start;
    }}
  }}
  @media (max-width: 1080px) {{
    .deadline-strip {{
      grid-template-columns: 1fr;
      gap: 12px;
    }}
    .dl-sub {{
      white-space: normal;
    }}
    .dl-right {{
      justify-content: space-between;
    }}
  }}
  .nav-export {{
    color: var(--text-secondary);
    text-decoration: none;
    padding: 3px 8px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--surface);
    transition: border-color 0.15s, color 0.15s;
  }}
  .nav-export:hover {{
    color: #ffffff;
    border-color: var(--border-strong);
  }}

  /* Main Container */
  .container {{
    max-width: 1280px;
    margin: 0 auto;
    padding: 36px 32px 80px;
  }}

  /* Header */
  .page-header {{
    margin-bottom: 24px;
  }}
  .header-top-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }}
  .page-header h1 {{
    font-family: var(--font-heading);
    font-size: 1.75rem;
    font-weight: 800;
    line-height: 1.2;
    letter-spacing: -0.025em;
    color: #ffffff;
    margin-bottom: 0;
    text-wrap: balance;
  }}
  h2, h3, .panel-title, .method-title {{
    text-wrap: balance;
  }}
  .unofficial-badge {{
    display: inline-flex;
    align-items: center;
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
    color: var(--text-secondary);
    font-size: 0.9375rem;
    max-width: 72ch;
    line-height: 1.55;
    text-wrap: pretty;
  }}
  .page-header p strong {{
    color: var(--text);
    font-weight: 600;
  }}

  /* Summary Metric Strip */
  .metrics-strip {{
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 24px;
    overflow: hidden;
  }}
  .metric-cell {{
    padding: 16px 18px;
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 3px;
  }}
  .metric-cell:last-child {{ border-right: none; }}
  .metric-lbl {{
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
  }}
  .metric-val {{
    font-family: var(--font-mono);
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.15;
    font-variant-numeric: tabular-nums;
  }}
  .metric-val.accent {{ color: var(--accent); }}
  .metric-sub {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }}

  /* Full-Width 2-Column Overview Grid */
  .overview-grid {{
    display: grid;
    grid-template-columns: 1.12fr 0.88fr;
    gap: 20px;
    margin-bottom: 32px;
  }}
  .panel {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px 22px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .panel-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 14px;
  }}
  .panel-title {{
    font-family: var(--font-heading);
    font-size: 14.5px;
    font-weight: 700;
    color: #ffffff;
  }}
  .panel-subtitle {{
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--text-muted);
  }}

  /* Category Interactive Rows */
  .cat-list {{
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .cat-filter-row {{
    appearance: none;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 8px;
    margin: 0 -8px;
    text-align: left;
    cursor: pointer;
    color: inherit;
    font-family: inherit;
    transition: background 0.12s, border-color 0.12s;
  }}
  .cat-filter-row:hover {{
    background: var(--surface-raised);
    border-color: var(--border);
  }}
  .cat-filter-row.active {{
    background: var(--accent-dim);
    border-color: rgba(79, 219, 200, 0.35);
  }}
  .cat-row-top {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 13px;
    margin-bottom: 5px;
  }}
  .cat-row-name {{
    color: var(--text);
    font-weight: 500;
  }}
  .cat-row-stats {{
    font-family: var(--font-mono);
    font-size: 12px;
    color: #ffffff;
    font-variant-numeric: tabular-nums;
  }}
  .cat-row-stats .muted {{
    color: var(--text-muted);
    font-weight: 400;
  }}
  .bar-bg {{
    width: 100%;
    height: 5px;
    background: #182320;
    border-radius: 2.5px;
    overflow: hidden;
  }}
  .bar-fg {{
    height: 100%;
    border-radius: 2.5px;
  }}

  /* Right Panel: Track Split + Signals */
  .track-split-box {{
    background: var(--surface-raised);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 16px;
    margin-bottom: 18px;
  }}
  .track-split-header {{
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 8px;
  }}
  .track-bar-combined {{
    display: flex;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    background: #182320;
    gap: 2px;
    margin-bottom: 10px;
  }}
  .track-seg-t1 {{ background: #64748b; }}
  .track-seg-t2 {{ background: var(--accent); }}
  .track-legend {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }}
  .track-legend-btn {{
    appearance: none;
    background: rgba(12, 18, 16, 0.55);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 8px 10px;
    text-align: left;
    cursor: pointer;
    color: var(--text);
    transition: border-color 0.12s, background 0.12s;
  }}
  .track-legend-btn:hover {{
    border-color: var(--border-strong);
    background: var(--surface-hover);
  }}
  .track-legend-btn.active {{
    border-color: var(--accent);
    background: var(--accent-dim);
  }}
  .tl-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 2px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }}
  .tl-dot {{
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 2px;
    margin-right: 6px;
  }}
  .tl-sub {{
    font-size: 11.5px;
    color: var(--text-secondary);
  }}

  .sig-list {{
    display: flex;
    flex-direction: column;
    gap: 9px;
  }}
  .sig-overview-row {{
    padding: 3px 6px;
    margin: 0 -6px;
    border-radius: 5px;
    border: 1px solid transparent;
  }}
  .sig-overview-row.clickable {{
    cursor: pointer;
    transition: background 0.12s, border-color 0.12s;
  }}
  .sig-overview-row.clickable:hover {{
    background: var(--surface-raised);
    border-color: var(--border);
  }}
  .sig-overview-row.active {{
    background: var(--accent-dim);
    border-color: rgba(79, 219, 200, 0.35);
  }}

  /* Directory Section & Controls */
  .directory-section {{
    margin-bottom: 44px;
  }}
  .dir-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 14px;
  }}
  .dir-header h2 {{
    font-family: var(--font-heading);
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
  }}
  .dir-status {{
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
  }}

  .controls-bar {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .controls-row-top {{
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }}
  .search-wrap {{
    position: relative;
    flex: 1;
    min-width: 260px;
  }}
  .search-input {{
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border-strong);
    color: #ffffff;
    padding: 8px 34px 8px 12px;
    border-radius: 6px;
    font-family: var(--font-sans);
    font-size: 13.5px;
    outline: none;
    transition: border-color 0.15s;
  }}
  .search-input:focus {{
    border-color: var(--accent);
  }}
  .search-input::placeholder {{
    color: var(--text-muted);
  }}
  .kbd-hint {{
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
    border: 1px solid var(--border);
    background: var(--surface);
    padding: 1px 6px;
    border-radius: 3px;
    pointer-events: none;
  }}

  .seg-tabs {{
    display: inline-flex;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 2px;
  }}
  .seg-tab {{
    appearance: none;
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-family: var(--font-sans);
    font-size: 12.5px;
    font-weight: 500;
    padding: 6px 11px;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.12s, color 0.12s;
    font-variant-numeric: tabular-nums;
  }}
  .seg-tab:hover {{ color: #ffffff; }}
  .seg-tab.active {{
    background: var(--surface-raised);
    color: #ffffff;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3);
  }}

  .select-ctrl {{
    background: var(--bg);
    border: 1px solid var(--border-strong);
    color: var(--text);
    padding: 7px 11px;
    border-radius: 6px;
    font-family: var(--font-sans);
    font-size: 12.5px;
    outline: none;
    cursor: pointer;
  }}
  .select-ctrl:focus {{ border-color: var(--accent); }}

  .controls-row-bottom {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--border);
  }}
  .filter-chips {{
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }}
  .chips-label {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
    margin-right: 4px;
  }}
  .chip-btn {{
    appearance: none;
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    font-family: var(--font-sans);
    font-size: 12px;
    font-weight: 500;
    padding: 4px 10px;
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.12s;
    font-variant-numeric: tabular-nums;
  }}
  .chip-btn:hover {{
    border-color: var(--border-strong);
    color: #ffffff;
  }}
  .chip-btn.active {{
    background: var(--accent-dim);
    border-color: var(--accent);
    color: var(--accent);
  }}
  .reset-btn {{
    appearance: none;
    background: transparent;
    border: none;
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 11.5px;
    cursor: pointer;
    text-decoration: underline;
    display: none;
  }}

  /* Auto-Indexing Callout Bar */
  .index-guide-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px 16px;
    background: rgba(17, 25, 22, 0.75);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 12px;
    font-size: 12.5px;
    color: var(--text-secondary);
  }}
  .index-guide-main {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
  }}
  .index-guide-title {{
    color: #ffffff;
    font-weight: 600;
    margin-right: 2px;
  }}
  .copy-tag {{
    appearance: none;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--bg);
    border: 1px solid var(--border-strong);
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 4px;
    cursor: pointer;
    transition: border-color 0.12s, background 0.12s;
  }}
  .copy-tag:hover {{
    border-color: var(--accent);
    background: var(--accent-dim);
  }}
  .copy-tag .copy-hint {{
    color: var(--text-muted);
    font-size: 10px;
  }}
  .copy-tag.copied {{
    border-color: var(--accent);
    background: rgba(79, 219, 200, 0.18);
    color: #ffffff;
  }}
  .index-guide-meta {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
    white-space: nowrap;
  }}
  .empty-state-cell {{
    text-align: center;
    padding: 36px 20px !important;
    color: var(--text-secondary);
    font-size: 13px;
    line-height: 1.6;
  }}
  .empty-state-cell strong {{
    color: #ffffff;
  }}

  /* Directory Table */
  .table-wrap {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow-x: auto;
  }}
  .table-wrap:focus-visible {{
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }}
  .dir-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    font-variant-numeric: tabular-nums;
  }}
  .dir-table th {{
    position: sticky;
    top: 0;
    z-index: 2;
    background: var(--surface-raised);
    color: var(--text-secondary);
    font-family: var(--font-mono);
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 10px 10px;
    text-align: left;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
    user-select: none;
  }}
  .dir-table th:first-child, .dir-table td:first-child {{ padding-left: 14px; }}
  .dir-table th:last-child, .dir-table td:last-child {{ padding-right: 14px; }}
  .dir-table th.col-num, .dir-table td.col-num {{ text-align: right; white-space: nowrap; }}
  .dir-table th.col-sig, .dir-table td.col-sig {{ text-align: center; white-space: nowrap; }}
  .dir-table td {{
    padding: 10px 10px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    vertical-align: middle;
  }}
  .dir-table tbody tr:last-child td {{ border-bottom: none; }}
  .dir-table tbody tr:hover td {{ background: rgba(27, 40, 36, 0.55); }}

  .col-rank {{
    width: 52px;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-muted);
    white-space: nowrap;
  }}
  .rank-num {{ color: var(--text-secondary); font-weight: 600; }}
  .rank-delta {{
    font-size: 10px;
    margin-left: 4px;
    font-weight: 600;
  }}
  .rank-delta.up {{ color: var(--accent); }}
  .rank-delta.down {{ color: #f87171; }}

  .col-repo {{
    min-width: 240px;
    max-width: 345px;
    line-height: 1.45;
  }}
  .repo-link {{
    text-decoration: none;
    font-family: var(--font-mono);
    font-size: 12.5px;
    display: inline;
    overflow-wrap: anywhere;
  }}
  .repo-owner {{
    color: var(--text-secondary);
    font-weight: 400;
  }}
  .repo-name {{
    color: #ffffff;
    font-weight: 600;
  }}
  .repo-link:hover .repo-name {{
    color: var(--accent);
    text-decoration: underline;
  }}
  .repo-stars {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: #fbbf24;
    margin-left: 6px;
    white-space: nowrap;
  }}
  .multi-repo-badge {{
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 600;
    color: #a5b4fc;
    background: rgba(129, 140, 248, 0.14);
    border: 1px solid rgba(129, 140, 248, 0.35);
    padding: 1px 6px;
    border-radius: 4px;
    margin-left: 6px;
    vertical-align: middle;
    cursor: help;
    white-space: nowrap;
  }}
  .partner-tags-wrap {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-left: 6px;
    vertical-align: middle;
  }}
  .partner-tag {{
    appearance: none;
    display: inline-flex;
    align-items: center;
    font-family: var(--font-mono);
    font-size: 9.5px;
    font-weight: 600;
    letter-spacing: 0.02em;
    color: #94a3b8;
    background: rgba(255, 255, 255, 0.025);
    border: 1px solid rgba(148, 163, 184, 0.22);
    padding: 1px 5px;
    border-radius: 3px;
    cursor: pointer;
    white-space: nowrap;
    opacity: 0.66;
    transition: opacity 0.14s ease, color 0.14s ease, border-color 0.14s ease, background 0.14s ease, transform 0.12s ease;
  }}
  tr:hover .partner-tag, .partner-tag:hover, .partner-tag:focus-visible, .partner-tag.active {{
    opacity: 1;
  }}
  tr:hover .partner-tag.pt-baseten, .partner-tag.pt-baseten:hover, .partner-tag.pt-baseten.active {{
    color: #34d399;
    border-color: rgba(52, 211, 153, 0.45);
    background: rgba(16, 185, 129, 0.12);
  }}
  tr:hover .partner-tag.pt-fireworks, .partner-tag.pt-fireworks:hover, .partner-tag.pt-fireworks.active {{
    color: #fb923c;
    border-color: rgba(251, 146, 60, 0.45);
    background: rgba(249, 115, 22, 0.12);
  }}
  tr:hover .partner-tag.pt-modal, .partner-tag.pt-modal:hover, .partner-tag.pt-modal.active {{
    color: #c084fc;
    border-color: rgba(192, 132, 252, 0.45);
    background: rgba(168, 85, 247, 0.12);
  }}
  tr:hover .partner-tag.pt-together, .partner-tag.pt-together:hover, .partner-tag.pt-together.active {{
    color: #38bdf8;
    border-color: rgba(56, 189, 248, 0.45);
    background: rgba(14, 165, 233, 0.12);
  }}
  .partner-tag:hover {{
    transform: translateY(-1px);
  }}
  .partner-overview-box {{
    margin-top: 6px;
    padding-top: 8px;
    border-top: 1px dashed var(--border-strong);
  }}
  .partner-overview-hdr {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 6px;
  }}
  .partner-overview-pills {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
  }}
  .partner-ov-pill {{
    appearance: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 4px;
    padding: 5px 8px;
    border-radius: 5px;
    background: var(--surface-raised);
    border: 1px solid var(--border-strong);
    color: var(--text-secondary);
    font-family: var(--font-mono);
    font-size: 10.5px;
    cursor: pointer;
    transition: border-color 0.14s, background 0.14s, color 0.14s, transform 0.12s;
  }}
  .partner-ov-pill .po-name {{
    font-weight: 600;
    color: #e2e8f0;
  }}
  .partner-ov-pill .po-cnt {{
    font-weight: 700;
    font-size: 10px;
  }}
  .partner-ov-pill.pt-baseten .po-cnt {{ color: #34d399; }}
  .partner-ov-pill.pt-fireworks .po-cnt {{ color: #fb923c; }}
  .partner-ov-pill.pt-modal .po-cnt {{ color: #c084fc; }}
  .partner-ov-pill.pt-together .po-cnt {{ color: #38bdf8; }}
  .partner-ov-pill:hover, .partner-ov-pill.active {{
    transform: translateY(-1px);
  }}
  .partner-ov-pill.pt-baseten:hover, .partner-ov-pill.pt-baseten.active {{
    border-color: #34d399;
    background: rgba(16, 185, 129, 0.12);
  }}
  .partner-ov-pill.pt-fireworks:hover, .partner-ov-pill.pt-fireworks.active {{
    border-color: #fb923c;
    background: rgba(249, 115, 22, 0.12);
  }}
  .partner-ov-pill.pt-modal:hover, .partner-ov-pill.pt-modal.active {{
    border-color: #c084fc;
    background: rgba(168, 85, 247, 0.12);
  }}
  .partner-ov-pill.pt-together:hover, .partner-ov-pill.pt-together.active {{
    border-color: #38bdf8;
    border-color: rgba(56, 189, 248, 0.85);
    background: rgba(14, 165, 233, 0.12);
  }}
  .rt-tag.pt-baseten {{
    color: #34d399;
    border-color: rgba(52, 211, 153, 0.42);
    background: rgba(16, 185, 129, 0.12);
  }}
  .rt-tag.pt-fireworks {{
    color: #fb923c;
    border-color: rgba(251, 146, 60, 0.42);
    background: rgba(249, 115, 22, 0.12);
  }}
  .rt-tag.pt-modal {{
    color: #c084fc;
    border-color: rgba(192, 132, 252, 0.42);
    background: rgba(168, 85, 247, 0.12);
  }}
  .rt-tag.pt-together {{
    color: #38bdf8;
    border-color: rgba(56, 189, 248, 0.42);
    background: rgba(14, 165, 233, 0.12);
  }}
  #readme-floating-tooltip {{
    position: fixed;
    z-index: 9999;
    width: 390px;
    max-width: calc(100vw - 24px);
    background-color: #0c1411;
    border: 1px solid rgba(79, 219, 200, 0.48);
    border-radius: 10px;
    padding: 13px 15px;
    box-shadow: 0 24px 56px rgba(0, 0, 0, 0.92), 0 0 0 1px rgba(79, 219, 200, 0.14);
    pointer-events: none;
    visibility: hidden;
    opacity: 0;
    isolation: isolate;
  }}
  #readme-floating-tooltip.mode-video {{
    width: 525px;
  }}
  #readme-floating-tooltip.visible {{
    visibility: visible;
    opacity: 1;
    pointer-events: auto;
  }}
  .rt-hdr {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }}
  .rt-repo {{
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 700;
    color: #ffffff;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .rt-meta {{
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
  }}
  .rt-hook {{
    font-family: var(--font-heading);
    font-size: 12.5px;
    font-weight: 600;
    color: var(--accent);
    line-height: 1.35;
    margin-bottom: 6px;
  }}
  .rt-body {{
    font-size: 12px;
    color: #d4e3df;
    line-height: 1.5;
    margin-bottom: 10px;
  }}
  .rt-tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 8px;
  }}
  .rt-tag {{
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 500;
    color: #cbd5e1;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 2px 6px;
    border-radius: 4px;
  }}
  .rt-ftr {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 7px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-muted);
  }}

  .cat-cell-wrap {{
    display: flex;
    align-items: center;
    gap: 7px;
  }}
  .trk-tag {{
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 3px;
    flex-shrink: 0;
  }}
  .trk-tag.t1 {{
    background: rgba(148, 163, 184, 0.12);
    color: #cbd5e1;
    border: 1px solid rgba(148, 163, 184, 0.25);
  }}
  .trk-tag.t2 {{
    background: rgba(79, 219, 200, 0.12);
    color: var(--accent);
    border: 1px solid rgba(79, 219, 200, 0.3);
  }}
  .cat-label {{
    color: var(--text-secondary);
    font-size: 12.5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 215px;
  }}

  .score-pill {{
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    background: var(--surface-raised);
    color: var(--text);
    border: 1px solid var(--border-strong);
    cursor: pointer;
    transition: transform 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease;
  }}
  .score-pill:hover, .score-pill:focus-visible {{
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(79, 219, 200, 0.18);
    transform: translateY(-1px);
    outline: none;
  }}
  .score-pill.high {{
    background: rgba(79, 219, 200, 0.13);
    color: var(--accent);
    border-color: rgba(79, 219, 200, 0.4);
  }}
  .score-pill.mid {{
    color: #ffffff;
  }}
  .sb-grid {{
    display: flex;
    flex-direction: column;
    gap: 9px;
    margin: 8px 0 10px;
  }}
  .sb-pillar {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 7px 9px;
  }}
  .sb-pillar-hdr {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
    font-family: var(--font-mono);
    font-size: 11px;
  }}
  .sb-pillar-name {{
    font-weight: 600;
    color: #ffffff;
  }}
  .sb-pillar-val {{
    font-weight: 700;
    color: var(--accent);
  }}
  .sb-bar-bg {{
    height: 4px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 6px;
  }}
  .sb-bar-fg {{
    height: 100%;
    border-radius: 2px;
  }}
  .sb-items {{
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .sb-item {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 8px;
    font-size: 11px;
    color: #cbd5e1;
    line-height: 1.35;
  }}
  .sb-pts {{
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 600;
    color: var(--accent);
    flex-shrink: 0;
  }}
  .sb-pts.neg {{
    color: #f87171;
  }}

  .commits-num {{
    font-family: var(--font-mono);
    font-size: 12.5px;
    color: var(--text);
  }}
  .delta-up {{
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--accent);
    margin-left: 5px;
    font-weight: 600;
  }}
  .pre-badge {{
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 10px;
    color: #fbbf24;
    background: rgba(251, 191, 36, 0.1);
    border: 1px solid rgba(251, 191, 36, 0.3);
    padding: 1px 5px;
    border-radius: 3px;
    margin-left: 5px;
    cursor: help;
    vertical-align: middle;
  }}
  .prs-num {{
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text);
    cursor: help;
  }}

  .cell-dash {{
    color: #789089;
    font-family: var(--font-mono);
    font-size: 12px;
    user-select: none;
  }}
  .sig-check {{
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 12.5px;
    font-weight: 600;
    white-space: nowrap;
  }}
  .sig-host {{
    color: var(--text-secondary);
    font-size: 11px;
    font-weight: 400;
  }}
  .sig-link {{
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-weight: 500;
    color: var(--accent);
    text-decoration: none;
    background: rgba(79, 219, 200, 0.08);
    border: 1px solid rgba(79, 219, 200, 0.25);
    padding: 2px 7px;
    border-radius: 4px;
    white-space: nowrap;
  }}
  .sig-link:hover {{
    background: rgba(79, 219, 200, 0.18);
  }}
  .vid-cell-wrap {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
  }}
  .vid-score-pill {{
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    background: var(--surface-raised);
    color: var(--text);
    border: 1px solid var(--border-strong);
    cursor: pointer;
    transition: transform 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease;
    white-space: nowrap;
  }}
  .vid-score-pill:hover, .vid-score-pill:focus-visible {{
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(79, 219, 200, 0.18);
    transform: translateY(-1px);
    outline: none;
  }}
  .vid-score-pill.high {{
    background: rgba(79, 219, 200, 0.13);
    color: var(--accent);
    border-color: rgba(79, 219, 200, 0.42);
  }}
  .vid-score-pill.mid {{
    background: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border-color: rgba(245, 158, 11, 0.35);
  }}
  .vid-score-pill.low {{
    background: rgba(248, 113, 113, 0.12);
    color: #f87171;
    border-color: rgba(248, 113, 113, 0.35);
  }}
  .vid-score-pill.dead {{
    background: rgba(248, 113, 113, 0.16);
    color: #f87171;
    border-color: rgba(248, 113, 113, 0.45);
  }}
  .vt-kpi-strip {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
    margin: 7px 0 8px;
  }}
  .vt-kpi-tile {{
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 5px 7px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .vt-kpi-lbl {{
    font-family: var(--font-mono);
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-muted);
  }}
  .vt-kpi-val {{
    font-family: var(--font-mono);
    font-size: 11.5px;
    font-weight: 700;
    color: #ffffff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .vt-kpi-sub {{
    font-size: 10px;
    color: #94a3b8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .vt-rubric-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
    margin-bottom: 8px;
  }}
  .vt-crit-card {{
    background: rgba(255, 255, 255, 0.028);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-left: 2.5px solid rgba(79, 219, 200, 0.55);
    border-radius: 6px;
    padding: 6px 8px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }}
  .vt-crit-card.mid {{
    border-color: rgba(245, 158, 11, 0.24);
    border-left: 2.5px solid #fbbf24;
    background: rgba(245, 158, 11, 0.035);
  }}
  .vt-crit-card.zero {{
    border-color: rgba(248, 113, 113, 0.26);
    border-left: 2.5px solid #f87171;
    background: rgba(248, 113, 113, 0.045);
  }}
  .vt-crit-hdr {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 4px;
    font-family: var(--font-mono);
    font-size: 10.5px;
  }}
  .vt-crit-name {{
    font-weight: 600;
    color: #f1f5f9;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .vt-crit-pts {{
    font-weight: 700;
    color: var(--accent);
    flex-shrink: 0;
  }}
  .vt-crit-pts.mid {{ color: #fbbf24; }}
  .vt-crit-pts.zero {{ color: #f87171; }}
  .vt-crit-sub {{
    font-size: 10.5px;
    color: #cbd5e1;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .vt-proof-row {{
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin-bottom: 8px;
  }}
  .vt-proof-line {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .vt-proof-lbl {{
    font-family: var(--font-mono);
    font-size: 9.5px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-right: 2px;
  }}
  .vt-chip-model {{
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    color: var(--accent);
    background: rgba(79, 219, 200, 0.1);
    border: 1px solid rgba(79, 219, 200, 0.28);
    padding: 1px 6px;
    border-radius: 4px;
  }}
  .vt-chip-bench {{
    font-family: var(--font-mono);
    font-size: 10px;
    color: #fcd34d;
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.28);
    padding: 1px 6px;
    border-radius: 4px;
    max-width: 360px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .vt-note-box {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 6px 9px;
    margin-bottom: 8px;
    font-size: 11px;
    line-height: 1.38;
    color: #cbd5e1;
  }}
  .vt-note-row {{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .vt-note-row + .vt-note-row {{
    margin-top: 4px;
    padding-top: 4px;
    border-top: 1px dashed rgba(255, 255, 255, 0.08);
  }}

  .table-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--surface-raised);
    border-top: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-secondary);
  }}
  .page-btns {{
    display: flex;
    gap: 8px;
  }}
  .page-btn {{
    appearance: none;
    background: var(--surface);
    border: 1px solid var(--border-strong);
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 12px;
    padding: 5px 12px;
    border-radius: 5px;
    cursor: pointer;
    transition: border-color 0.12s, background 0.12s;
  }}
  .page-btn:hover {{
    border-color: var(--accent);
    color: #ffffff;
  }}

  /* Methodology Section */
  .methodology-section {{
    margin-top: 40px;
  }}
  .methodology-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-top: 14px;
  }}
  .method-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 18px;
  }}
  .method-top {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 8px;
  }}
  .method-title {{
    font-family: var(--font-heading);
    font-size: 14px;
    font-weight: 700;
    color: #ffffff;
  }}
  .method-weight {{
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    color: var(--accent);
  }}
  .method-desc {{
    font-size: 12.5px;
    color: var(--text-secondary);
    line-height: 1.5;
  }}
  .rubric-details {{
    margin-top: 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}
  .rubric-summary {{
    padding: 12px 18px;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    cursor: pointer;
    user-select: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
    list-style: none;
    transition: color 0.12s, background 0.12s;
  }}
  .rubric-summary::-webkit-details-marker {{ display: none; }}
  .rubric-summary:hover {{
    color: #ffffff;
    background: var(--surface-raised);
  }}
  .rubric-toggle-wrap {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--accent);
    font-size: 11px;
    flex-shrink: 0;
  }}
  .rubric-chevron {{
    display: inline-block;
    color: var(--accent);
    font-size: 11px;
    transition: transform 0.15s ease;
  }}
  .rubric-details[open] .rubric-chevron {{
    transform: rotate(180deg);
  }}
  .rubric-body {{
    padding: 16px 18px 18px;
    border-top: 1px solid var(--border);
    background: rgba(12, 18, 16, 0.55);
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    font-size: 12px;
    color: var(--text-secondary);
    line-height: 1.55;
  }}
  @media (max-width: 820px) {{
    .rubric-body {{ grid-template-columns: 1fr; }}
  }}
  .rubric-col h3 {{
    font-family: var(--font-heading);
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
  }}
  .rubric-col h3 span {{
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--accent);
  }}
  .rubric-list {{
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .rubric-list li {{
    display: flex;
    justify-content: space-between;
    gap: 10px;
    border-bottom: 1px dashed rgba(255, 255, 255, 0.06);
    padding-bottom: 3px;
  }}
  .rubric-pts {{
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--accent);
    white-space: nowrap;
    flex-shrink: 0;
  }}
  .rubric-pts.neg {{
    color: #f87171;
  }}
  .rubric-note {{
    grid-column: 1 / -1;
    margin-top: 4px;
    padding-top: 10px;
    border-top: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
  }}

  /* Candidate Chart Previews Section */
  .preview-showcase {{
    margin-top: 48px;
    padding-top: 32px;
    border-top: 2px dashed var(--border-strong);
  }}
  .preview-badge {{
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: #0c1210;
    background: var(--accent);
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 8px;
    text-transform: uppercase;
  }}
  .ts-kpis {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 14px;
  }}
  .ts-kpi {{
    background: var(--surface-raised);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 9px 11px;
  }}
  .ts-kpi-lbl {{
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--text-muted);
    display: block;
    margin-bottom: 2px;
  }}
  .ts-kpi-val {{
    font-family: var(--font-mono);
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
  }}
  .ts-kpi-delta {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent);
    margin-left: 5px;
    font-weight: 600;
  }}
  .ts-chart-box {{
    background: var(--surface-raised);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 14px 8px;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .ts-axis-hdr {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: var(--font-mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 4px;
  }}
  .ts-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-secondary);
  }}
  .ts-legend {{
    display: flex;
    gap: 16px;
    align-items: center;
  }}
  .ts-rate {{
    color: var(--text-muted);
  }}
  .ts-rate strong {{
    color: var(--accent);
    font-weight: 600;
  }}
  .hist-wrap {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(56px, 1fr));
    gap: 10px;
    align-items: end;
    padding: 12px 10px 6px;
    background: var(--surface-raised);
    border: 1px solid var(--border);
    border-radius: 6px;
  }}
  .hist-col {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }}
  .hist-val {{
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--text);
    text-align: center;
  }}
  .hist-pct {{
    display: block;
    font-size: 9.5px;
    font-weight: 400;
    color: var(--text-muted);
  }}
  .hist-bar-Area {{
    width: 100%;
    height: 110px;
    display: flex;
    align-items: flex-end;
    justify-content: center;
  }}
  .hist-stack {{
    width: 72%;
    display: flex;
    flex-direction: column;
    border-radius: 4px 4px 0 0;
    overflow: hidden;
  }}
  .hist-seg-t2 {{
    background: #4fdbc8;
    width: 100%;
  }}
  .hist-seg-t1 {{
    background: #475569;
    width: 100%;
  }}
  .cat-qual-row {{
    padding: 5px 6px;
    border-radius: 5px;
  }}
  .cat-qual-badges {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: var(--font-mono);
    font-size: 10.5px;
  }}
  .cq-pill {{
    padding: 1px 6px;
    border-radius: 3px;
    white-space: nowrap;
  }}
  .cq-pill.avg {{
    background: var(--surface-raised);
    color: #ffffff;
    border: 1px solid var(--border-strong);
  }}
  .cq-pill.top {{
    background: rgba(79, 219, 200, 0.12);
    color: var(--accent);
    border: 1px solid rgba(79, 219, 200, 0.3);
  }}
  .cq-pill.trk {{
    color: var(--text-muted);
  }}
  .stacked-bar {{
    display: flex;
    height: 7px;
    overflow: hidden;
    background: var(--surface-raised);
  }}
  .sb-seg {{
    height: 100%;
  }}
  .sb-seg.high {{ background: #4fdbc8; }}
  .sb-seg.mid {{ background: #0ea5e9; }}
  .sb-seg.low {{ background: #334155; }}
  .hist-lbl {{
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-secondary);
    text-align: center;
    white-space: nowrap;
  }}
  .mover-list {{
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .mover-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    padding: 7px 10px;
    background: var(--surface-raised);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 12.5px;
  }}
  .mover-left {{
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    overflow: hidden;
  }}
  .mover-rank {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
    width: 30px;
    flex-shrink: 0;
  }}
  .mover-meta {{
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: #60a5fa;
    background: rgba(96, 165, 250, 0.12);
    border: 1px solid rgba(96, 165, 250, 0.25);
    padding: 1px 5px;
    border-radius: 3px;
    flex-shrink: 0;
  }}
  .mover-right {{
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }}
  .mover-total {{
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
  }}

  footer {{
    border-top: 1px solid var(--border);
    padding: 24px 32px;
    font-size: 12px;
    color: var(--text-secondary);
  }}
  .footer-inner {{
    max-width: 1280px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
  }}
  footer a {{
    color: var(--accent);
    text-decoration: none;
  }}
  footer a:hover {{ text-decoration: underline; }}

  @media (max-width: 1024px) {{
    .metrics-strip {{ grid-template-columns: repeat(3, 1fr); }}
    .metric-cell:nth-child(3) {{ border-right: none; }}
    .metric-cell:nth-child(-n+3) {{ border-bottom: 1px solid var(--border); }}
    .overview-grid {{ grid-template-columns: 1fr; }}
    .methodology-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}

  @media (max-width: 680px) {{
    .navbar {{ padding: 0 14px; height: 50px; }}
    .nav-brand {{ gap: 6px; font-size: 13.5px; white-space: nowrap; flex-shrink: 0; min-width: 0; }}
    .nav-brand img {{ height: 19px; }}
    .nav-brand .product {{ font-size: 12px; }}
    .nav-meta {{ gap: 6px; flex-shrink: 0; }}
    .nav-meta .nav-repo-cnt,
    .nav-meta .sep,
    .nav-meta .nav-csv,
    .nav-meta .nav-export,
    .nav-countdown-pill,
    .hide-mobile {{ display: none; }}
    .nav-checklist-btn {{ padding: 4px 9px; font-size: 11px; }}
    .col-repo {{ min-width: 200px; max-width: 260px; }}

    .container {{ padding: 20px 14px 56px; }}
    .page-header {{ margin-bottom: 16px; }}
    .page-header h1 {{ font-size: 22px; line-height: 1.25; }}
    .page-header p {{ font-size: 13.5px; line-height: 1.5; }}

    .deadline-strip {{ padding: 12px 14px; gap: 10px; }}
    .dl-kicker-row {{ flex-wrap: wrap; gap: 6px; }}
    .dl-phase-tag {{ white-space: normal; }}
    .dl-sub {{ font-size: 11px; white-space: normal; line-height: 1.45; }}
    .dl-mid {{ min-width: 0; }}
    .dl-prog-top {{ flex-wrap: wrap; gap: 6px; white-space: normal; }}
    .dl-milestones {{ flex-wrap: wrap; white-space: normal; }}
    .dl-right {{ flex-wrap: wrap; gap: 8px; justify-content: flex-start; }}
    .dl-blocks {{ padding: 4px 8px; gap: 4px; }}
    .dl-unit {{ min-width: 32px; }}
    .dl-num {{ font-size: 14px; }}

    .metrics-strip {{ grid-template-columns: repeat(2, 1fr); margin-bottom: 18px; }}
    .metric-cell {{ padding: 12px 14px; border-bottom: 1px solid var(--border); }}
    .metric-cell:nth-child(3) {{ border-right: 1px solid var(--border); }}
    .metric-cell:nth-child(2n) {{ border-right: none; }}
    .metric-cell:nth-last-child(-n+2) {{ border-bottom: none; }}
    .metric-val {{ font-size: 20px; }}
    .metric-sub {{ font-size: 10.5px; white-space: normal; }}

    .overview-grid {{ gap: 16px; margin-bottom: 20px; }}
    .panel {{ padding: 16px; }}
    .panel-header {{
      flex-direction: column;
      align-items: flex-start;
      gap: 3px;
      padding-bottom: 10px;
      margin-bottom: 12px;
    }}
    .cat-row-top {{ font-size: 12.5px; gap: 8px; }}
    .cat-row-name {{ min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .cat-row-stats {{ flex-shrink: 0; }}

    .track-split-box {{ padding: 12px; margin-bottom: 14px; }}
    .track-legend {{ grid-template-columns: 1fr; gap: 8px; }}

    .ts-kpis {{ grid-template-columns: repeat(2, 1fr); gap: 8px; }}
    .ts-axis-hdr {{ font-size: 9px; letter-spacing: 0.02em; }}
    .ts-footer {{ flex-direction: column; align-items: flex-start; gap: 4px; }}

    .dir-header {{
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }}
    .index-guide-bar {{ padding: 10px 12px; font-size: 12px; gap: 8px; }}
    .index-guide-meta {{ white-space: normal; line-height: 1.4; }}
    .controls-bar {{ padding: 12px; }}
    .controls-row-top {{ gap: 8px; }}
    .search-wrap {{ min-width: 100%; width: 100%; }}
    .seg-tabs {{ width: 100%; display: flex; }}
    .seg-tab {{ flex: 1; text-align: center; padding: 6px 6px; font-size: 12px; }}
    .select-ctrl {{ flex: 1; min-width: calc(50% - 4px); font-size: 12px; padding: 7px 8px; }}

    .table-footer {{
      flex-direction: column;
      align-items: stretch;
      gap: 10px;
      padding: 12px;
    }}
    .page-btns {{ width: 100%; }}
    .page-btn {{ flex: 1; text-align: center; white-space: nowrap; padding: 7px 10px; }}

    .methodology-section {{ margin-top: 28px; }}
    .methodology-grid {{ grid-template-columns: 1fr !important; gap: 10px; }}
    .rubric-summary {{ gap: 10px; align-items: flex-start; }}
    footer {{ padding: 20px 16px; }}
    .footer-inner {{ flex-direction: column; align-items: flex-start; gap: 6px; }}
  }}
</style>
</head>
<body>

<nav class="navbar">
  <div class="nav-inner">
    <a href="https://watt-mind.com" target="_blank" rel="noopener" class="nav-brand">
      {logo_html}
      <span>Watt Mind</span>
      <span class="divider">/</span>
      <span class="product">Hackathon Directory</span>
    </a>
    <div class="nav-meta">
      <span class="nav-repo-cnt">{total_repos} repositories</span>
      <span class="sep">&middot;</span>
      <span class="nav-pill hide-mobile"><span class="nav-dot" style="background:#94a3b8;box-shadow:none;"></span>Indexing stopped</span>
      <a href="/meta-hackathon-2026/checklist" class="nav-checklist-btn" title="Unofficial 20-point pre-submission &amp; judging checklist distilled from 580+ Discord Q&amp;A threads">&#10003; <span class="hide-mobile">Submission </span>Checklist</a>
      <a href="#methodology" class="nav-export" onclick="const d=document.getElementById('rubric-details');if(d)d.open=true;" title="Jump to automated scoring formula &amp; disclaimer">How We Score &darr;</a>
      <a href="/meta-hackathon-2026/projects.json" class="nav-export">JSON</a>
      <a href="/meta-hackathon-2026/projects.csv" class="nav-export nav-csv">CSV</a>
    </div>
  </div>
</nav>

<main class="container">

  <!-- Header -->
  <header class="page-header">
    <div class="header-top-row">
      <h1>Unofficial Meta Global AI Hackathon 2026 &mdash; Project Directory</h1>
      <span class="unofficial-badge" title="Independent community index — not affiliated with or endorsed by Meta or Cerebral Valley">Unofficial Community Tracker</span>
    </div>
    <p>Unofficial community tracker of <strong>{total_repos} public repositories</strong> built for the hackathon &mdash; indexed by category, track, commit activity since October 26, pull requests, automated test suites, containerization, and working deployments.</p>
  </header>

  <!-- Prominent Unofficial Disclaimer & Self-Audit Disclosure -->
  <section class="disclaimer-banner" aria-label="Unofficial Community Disclaimer and Scoring Disclosure">
    <div class="disclaimer-content">
      <div class="disclaimer-title">
        <span>&#9888;&#65039; Unofficial Community Telemetry Index &mdash; Not Official Hackathon Judging</span>
        <span class="disclaimer-tag">Author Disclosure: Built by the <a href="https://github.com/watt-mind/pii-guard" target="_blank" rel="noopener">watt-mind/pii-guard</a> team</span>
      </div>
      <p class="disclaimer-text">
        This directory is an <strong>independent community side-project</strong> and is <strong>not affiliated with Meta or Cerebral Valley</strong> &mdash; <strong>only the official judges&rsquo; evaluations determine hackathon winners</strong>. Scores (<code>0.0&ndash;10.0</code>) are automated static GitHub heuristics measuring repository completeness (commit cadence, tests, Dockerfiles, README docs, Meta SDK references, and public demo links), <strong>not</strong> an evaluation of product quality, creativity, or UX. Because we built our own project (<a href="https://github.com/watt-mind/pii-guard" target="_blank" rel="noopener"><code>watt-mind/pii-guard</code></a>) against this same internal engineering checklist, it naturally scores <code>10.0</code> on these automated checks. Hover or click any score pill to inspect the exact point ledger.
      </p>
    </div>
    <a href="#methodology" class="disclaimer-cta" onclick="const d=document.getElementById('rubric-details');if(d)d.open=true;">How We Calculate Scores &darr;</a>
  </section>

  <!-- Summary Metrics Strip -->
  <section class="metrics-strip">
    <div class="metric-cell">
      <span class="metric-lbl">Indexed Repositories</span>
      <span class="metric-val">{total_repos}</span>
      <span class="metric-sub">{total_commits:,} commits in window</span>
    </div>
    <div class="metric-cell">
      <span class="metric-lbl">Active Since Oct 26</span>
      <span class="metric-val accent">{active_in_window}</span>
      <span class="metric-sub">{active_in_window/total_repos*100:.1f}% active in window</span>
    </div>
    <div class="metric-cell">
      <span class="metric-lbl">20+ Commits</span>
      <span class="metric-val">{high_velocity}</span>
      <span class="metric-sub">{high_velocity/total_repos*100:.1f}% high commit cadence</span>
    </div>
    <div class="metric-cell">
      <span class="metric-lbl">Automated Tests</span>
      <span class="metric-val">{test_count}</span>
      <span class="metric-sub">{test_count/total_repos*100:.1f}% include test suites</span>
    </div>
    <div class="metric-cell">
      <span class="metric-lbl">Dockerized</span>
      <span class="metric-val">{docker_count}</span>
      <span class="metric-sub">{docker_count/total_repos*100:.1f}% include Dockerfile</span>
    </div>
    <div class="metric-cell">
      <span class="metric-lbl">Live Deployments</span>
      <span class="metric-val accent">{live_deployments}</span>
      <span class="metric-sub">{video_demos} with video demos</span>
    </div>
  </section>

  <!-- Full-Width 2-Column Overview Grid -->
  <section class="overview-grid">
    <!-- Left Column: Projects by Category -->
    <div class="panel">
      <div style="display:flex; flex-direction:column; height:100%;">
        <div class="panel-header">
          <span class="panel-title">Projects by Category</span>
          <span class="panel-subtitle">Click any category to filter directory</span>
        </div>
        <div class="cat-list" id="category-overview-list" style="flex:1; justify-content:space-between;">
          {''.join(category_rows_html)}
        </div>
      </div>
    </div>

    <!-- Right Column: Track Split & Repository Signals -->
    <div class="panel">
      <div>
        <div class="panel-header">
          <span class="panel-title">Track Split &amp; Repository Signals</span>
          <span class="panel-subtitle">Across all {total_repos} submissions</span>
        </div>

        <div class="track-split-box">
          <div class="track-split-header">
            <span>Hackathon Track Distribution</span>
            <span>{track_world} vs {track_frontier} repos</span>
          </div>
          <div class="track-bar-combined">
            <div class="track-seg-t1" style="width: {track_world_pct:.1f}%;"></div>
            <div class="track-seg-t2" style="width: {track_frontier_pct:.1f}%;"></div>
          </div>
          <div class="track-legend">
            <button type="button" class="track-legend-btn" data-track-card="Track 1">
              <div class="tl-top">
                <span><span class="tl-dot" style="background:#64748b;"></span>Track 1</span>
                <span>{track_world} ({track_world_pct:.1f}%)</span>
              </div>
              <div class="tl-sub">Build for Your World</div>
            </button>
            <button type="button" class="track-legend-btn" data-track-card="Track 2">
              <div class="tl-top">
                <span><span class="tl-dot" style="background:#4fdbc8;"></span>Track 2</span>
                <span>{track_frontier} ({track_frontier_pct:.1f}%)</span>
              </div>
              <div class="tl-sub">Push the Frontier</div>
            </button>
          </div>
        </div>

        <div class="sig-list" id="signal-overview-list">
          {''.join(signal_rows_html)}
        </div>
      </div>
    </div>
  </section>

  <!-- Second Full-Width 2-Column Overview Grid: Activity Over Time & Meta AI Stack -->
  <section class="overview-grid" id="activity-and-stack">
    <!-- Left Column: Activity & Demo Velocity Over Time -->
    <div class="panel">
      <div style="display:flex; flex-direction:column; height:100%;">
        <div class="panel-header">
          <span class="panel-title">Activity &amp; Demo Velocity Over Time</span>
          <span class="panel-subtitle">4h snapshots since Oct 29</span>
        </div>

        <div class="ts-kpis">
          <div class="ts-kpi">
            <span class="ts-kpi-lbl">Tracked Repos</span>
            <span class="ts-kpi-val">{total_repos}</span><span class="ts-kpi-delta">+{ts_repo_gain}</span>
          </div>
          <div class="ts-kpi">
            <span class="ts-kpi-lbl">Total Commits</span>
            <span class="ts-kpi-val">{total_commits:,}</span><span class="ts-kpi-delta">+{ts_commit_gain:,}</span>
          </div>
          <div class="ts-kpi">
            <span class="ts-kpi-lbl">Live Apps</span>
            <span class="ts-kpi-val">{live_deployments}</span><span class="ts-kpi-delta">+{ts_live_gain}</span>
          </div>
          <div class="ts-kpi">
            <span class="ts-kpi-lbl">Video Demos</span>
            <span class="ts-kpi-val">{video_demos}</span><span class="ts-kpi-delta">+{ts_video_gain}</span>
          </div>
        </div>

        <div class="ts-chart-box">
          <div class="ts-axis-hdr">
            <span style="color:#4fdbc8;">&#9679; Cumulative Commits<span class="hide-mobile"> (left axis)</span></span>
            <span style="display:inline-flex; gap:12px; align-items:center;">
              <span style="color:#818cf8;">&#9679; Live Apps</span>
              <span style="color:#f59e0b;">&#9679; Video Demos<span class="hide-mobile"> (right)</span></span>
              <span style="color:#fb7185;" title="Submission deadline &amp; judging start: Nov 5, 2026 02:00 UTC (Nov 4, 6:00 PM PST)">&#9478; Judging Start</span>
            </span>
          </div>
          {timeseries_svg_html}
        </div>

        <div class="ts-footer">
          <div class="ts-rate">Baseline: Oct 29 08:49 UTC ({first_ts.get('total_repos', 681)} repos)</div>
          <div class="ts-rate">Latest 4h window: <strong>+{last_4h_commits:,} commits</strong> &middot; <strong>+{last_4h_repos} repos</strong></div>
        </div>
      </div>
    </div>

    <!-- Right Column: Meta AI Model & Stack Adoption -->
    <div class="panel">
      <div style="display:flex; flex-direction:column; height:100%;">
        <div class="panel-header">
          <span class="panel-title">Meta AI Models &amp; Stack</span>
          <span class="panel-subtitle">Click any stack to filter directory</span>
        </div>
        <div class="cat-list" id="model-overview-list" style="flex:1; justify-content:space-between;">
          {''.join(model_bars_html)}
        </div>
      </div>
    </div>
  </section>

  <!-- Unified Interactive Project Directory -->
  <section class="directory-section" id="directory">
    <div class="dir-header">
      <h2 id="dir-heading">Repository Directory</h2>
      <div class="dir-status" id="dir-status-text">Showing top 50 of {total_repos} repositories</div>
    </div>

    <div class="index-guide-bar">
      <div class="index-guide-main">
        <span class="index-guide-title">Missing your repository?</span>
        <span>Add topic</span>
        <button type="button" class="copy-tag" data-copy="meta-hackathon-2026" title="Click to copy topic"><code>meta-hackathon-2026</code><span class="copy-hint">copy</span></button>
        <span>or</span>
        <button type="button" class="copy-tag" data-copy="meta-ai-hackathon" title="Click to copy topic"><code>meta-ai-hackathon</code><span class="copy-hint">copy</span></button>
        <span>or description</span>
        <button type="button" class="copy-tag" data-copy="Meta Global AI Hackathon 2026" title="Click to copy phrase"><code>"Meta Global AI Hackathon 2026"</code><span class="copy-hint">copy</span></button>
      </div>
      <div class="index-guide-meta">Multi-repo workspaces supported &middot; Indexing stopped</div>
    </div>

    <div class="controls-bar">
      <div class="controls-row-top">
        <div class="search-wrap">
          <input id="repo-search" type="text" class="search-input" aria-label="Search repositories or GitHub usernames" placeholder="Search {total_repos} repositories or GitHub usernames..." autocomplete="off" />
          <span class="kbd-hint" aria-hidden="true">/</span>
        </div>

        <div class="seg-tabs" id="track-tabs" role="group" aria-label="Filter by hackathon track">
          <button type="button" class="seg-tab active" data-track="">All ({total_repos})</button>
          <button type="button" class="seg-tab" data-track="Track 1">Track 1 ({track_world})</button>
          <button type="button" class="seg-tab" data-track="Track 2">Track 2 ({track_frontier})</button>
        </div>

        <select id="category-select" class="select-ctrl" aria-label="Filter by category">
          <option value="">All Categories ({total_repos})</option>
          {category_options_html}
        </select>

        <select id="sort-select" class="select-ctrl" aria-label="Sort repositories">
          <option value="score">Sort: Rubric Score</option>
          <option value="video_score">Sort: Video Audit Score</option>
          <option value="commits">Sort: Commits in Window</option>
          <option value="prs">Sort: Pull Requests</option>
          <option value="stars">Sort: GitHub Stars</option>
          <option value="newest">Sort: Recently Created</option>
        </select>
      </div>

      <div class="controls-row-bottom">
        <div class="filter-chips" id="signal-chips">
          <span class="chips-label">Filter by signal:</span>
          <button type="button" class="chip-btn" data-chip="active">Active Oct 26+ ({active_in_window})</button>
          <button type="button" class="chip-btn" data-chip="clean">Clean-Slate ({clean_slate_count})</button>
          <button type="button" class="chip-btn" data-chip="prs">Uses PRs ({pr_workflow_count})</button>
          <button type="button" class="chip-btn" data-chip="live">Live App ({live_deployments})</button>
          <button type="button" class="chip-btn" data-chip="video">Video ({video_demos})</button>
          <button type="button" class="chip-btn" data-chip="docker">Docker ({docker_count})</button>
          <button type="button" class="chip-btn" data-chip="tests">Tests ({test_count})</button>
          <button type="button" class="chip-btn" data-chip="weights">Fine-Tuned Weights ({open_weights_count})</button>
        </div>
        <button type="button" class="reset-btn" id="reset-filters-btn">Reset all filters</button>
      </div>
    </div>

    <div class="table-wrap" role="region" aria-labelledby="dir-heading" tabindex="0">
      <table class="dir-table" id="directory-table">
        <thead>
          <tr>
            <th class="col-rank">#</th>
            <th class="col-repo">Repository</th>
            <th class="col-cat">Track &amp; Category</th>
            <th class="col-num" title="Unofficial automated GitHub telemetry score (0–10). Hover any score pill for exact breakdown or click '?' to view formula.">Auto Score<a href="#methodology" class="th-info-link" onclick="const d=document.getElementById('rubric-details');if(d)d.open=true;" title="How we calculate automated repo scores">?</a></th>
            <th class="col-num" title="Commits since October 26, 2026 (amber badge indicates pre-hackathon commits)">Commits</th>
            <th class="col-num" title="Merged / total GitHub Pull Requests">PRs</th>
            <th class="col-sig">Live App</th>
            <th class="col-sig" title="Multimodal video audit score (0.00–2.50) via yt-dlp, ffprobe, SAM 3.1 &amp; Muse Spark 1.3. Hover any video score pill for breakdown or click '?' for formula.">Video<a href="#video-methodology" class="th-info-link" onclick="const d=document.getElementById('video-rubric-details');if(d)d.open=true;" title="How we calculate video audit scores">?</a></th>
          </tr>
        </thead>
        <tbody id="directory-tbody">
          {build_initial_directory_rows(projects_sorted, limit=50)}
        </tbody>
      </table>

      <div class="table-footer">
        <span id="table-footer-count">Showing 1&ndash;50 of {total_repos} repositories</span>
        <div class="page-btns">
          <button type="button" class="page-btn" id="btn-show-more">Show +100 more</button>
          <button type="button" class="page-btn" id="btn-show-all">Show all {total_repos}</button>
        </div>
      </div>
    </div>
  </section>

  <!-- Scoring Methodology -->
  <section class="methodology-section" id="methodology">
    <div class="dir-header">
      <h2>Automated Telemetry Scoring Methodology (Unofficial)</h2>
      <span class="dir-status">Static GitHub heuristic weights (0&ndash;10 scale) &middot; Not official judging</span>
    </div>
    <div class="methodology-grid">
      <div class="method-card">
        <div class="method-top">
          <span class="method-title">Impact</span>
          <span class="method-weight">30% (3.0 pts)</span>
        </div>
        <p class="method-desc">Evaluates problem specificity, canonical domain &amp; track alignment, quantitative evaluation/benchmark evidence, Docker packaging, and architecture scope.</p>
      </div>
      <div class="method-card">
        <div class="method-top">
          <span class="method-title">Meta AI Tooling</span>
          <span class="method-weight">25% (2.5 pts)</span>
        </div>
        <p class="method-desc">Measures verified Meta Model API &amp; Muse Spark usage, multi-model pipelines (SAM 3.1, Muse Wonder/Image/Voice/Code), and fine-tuned open weights (Muse Glimmer / Muse Spark Open).</p>
      </div>
      <div class="method-card">
        <div class="method-top">
          <span class="method-title">Technical Depth</span>
          <span class="method-weight">20% (2.0 pts)</span>
        </div>
        <p class="method-desc">Checks incremental commit cadence since October 26, modular source tree structure, automated test &amp; evaluation suites, CI workflows, and PR review discipline.</p>
      </div>
      <div class="method-card">
        <div class="method-top">
          <span class="method-title">Demo Completeness</span>
          <span class="method-weight">25% (2.5 pts)</span>
        </div>
        <p class="method-desc">Verifies 3-minute video walkthroughs, reproducible local setup instructions (Quickstart / <code>.env.example</code> / Docker), live web deployments, and visual documentation.</p>
      </div>
    </div>

    <details class="rubric-details" id="rubric-details" open>
      <summary class="rubric-summary">
        <span>Exact Point-by-Point Automated Formula, Self-Audit Disclosure &amp; Changelog</span>
        <span class="rubric-toggle-wrap"><span>Toggle</span><span class="rubric-chevron">&#9662;</span></span>
      </summary>
      <div class="rubric-body">
        <div class="rubric-col">
          <h3>1. Impact <span>Max 3.0 pts (30%)</span></h3>
          <ul class="rubric-list">
            <li><span>Base active hackathon repository</span><span class="rubric-pts">+1.0</span></li>
            <li><span>Official Track alignment (Track 1: Build for Your World &amp; Track 2: Push the Frontier equalized)</span><span class="rubric-pts">+0.4</span></li>
            <li><span>Canonical domain specificity (Security/Infra, Robotics, Agents, Healthcare: +0.4 &middot; Vision/Audio/Edu/Legal/Finance: +0.3 &middot; General: +0.2)</span><span class="rubric-pts">+0.2 to +0.4</span></li>
            <li><span>Quantitative evaluation &amp; benchmark suite (<code>eval/</code>, <code>benchmarks/</code>, F1 / latency / accuracy metrics)</span><span class="rubric-pts">+0.3</span></li>
            <li><span>Production containerization (<code>Dockerfile</code> / <code>compose.yaml</code>)</span><span class="rubric-pts">+0.4</span></li>
            <li><span>Multi-module repository scope (&gt;10 root tree entries)</span><span class="rubric-pts">+0.2</span></li>
            <li><span>Comprehensive problem &amp; architecture formulation (README &gt;5 KB)</span><span class="rubric-pts">+0.3</span></li>
          </ul>
        </div>
        <div class="rubric-col">
          <h3>2. Meta AI Tooling <span>Max 2.5 pts (25%)</span></h3>
          <ul class="rubric-list">
            <li><span>Base repository</span><span class="rubric-pts">+0.5</span></li>
            <li><span>Verified Meta Model API / SDK integration (<code>dev.meta.ai</code>)</span><span class="rubric-pts">+0.5</span></li>
            <li><span>Muse Spark reasoning integration (<code>muse-spark</code>)</span><span class="rubric-pts">+0.3</span></li>
            <li><span>Multimodal Meta models (<code>SAM 3.1</code>, <code>Muse Wonder</code>, <code>Muse Image</code>, <code>Muse Voice</code>)</span><span class="rubric-pts">+0.3</span></li>
            <li><span>Multi-model pipeline bonus (3+ distinct Meta model families combined)</span><span class="rubric-pts">+0.2</span></li>
            <li><span>Official inference partner (Baseten, Fireworks, Modal, Together &mdash; detected in deps, README, or <code>.env.example</code>)</span><span class="rubric-pts">+0.2</span></li>
            <li><span>Open-weights fine-tuning / distillation (<code>Muse Glimmer 30B</code> / <code>Muse Spark Open</code> / LoRA / QLoRA)</span><span class="rubric-pts">+0.5</span></li>
            <li><span>Published open-weight model/dataset on Hugging Face Hub</span><span class="rubric-pts">+0.3</span></li>
            <li><span>Non-Meta proprietary runtime SDKs with zero Meta models</span><span class="rubric-pts neg">&minus;0.6</span></li>
          </ul>
        </div>
        <div class="rubric-col">
          <h3>3. Technical Depth <span>Max 2.0 pts (20%)</span></h3>
          <ul class="rubric-list">
            <li><span>Base repository</span><span class="rubric-pts">+0.3</span></li>
            <li><span>Incremental commit cadence since Oct 26 (50+ commits: +0.6 &middot; 15+: +0.4 &middot; 5+: +0.2 &middot; 0: &minus;0.3)</span><span class="rubric-pts">+0.2 to +0.6</span></li>
            <li><span>Automated test suite (<code>tests/</code>, <code>spec/</code>)</span><span class="rubric-pts">+0.3</span></li>
            <li><span>Modular source architecture (<code>src/</code>, <code>app/</code>, <code>packages/</code>, <code>services/</code>)</span><span class="rubric-pts">+0.3</span></li>
            <li><span>Agent orchestration or evaluation harness</span><span class="rubric-pts">+0.2</span></li>
            <li><span>Automated CI workflows (<code>.github/workflows</code>)</span><span class="rubric-pts">+0.2</span></li>
            <li><span>Pull request review discipline (3+ merged PRs or 5+ PRs with CI)</span><span class="rubric-pts">+0.2</span></li>
            <li><span>Pre-existing codebase where pre-Oct 26 commits exceed hackathon commits</span><span class="rubric-pts neg">&minus;0.3 to &minus;0.5</span></li>
          </ul>
        </div>
        <div class="rubric-col">
          <h3>4. Demo Completeness <span>Max 2.5 pts (25%)</span></h3>
          <ul class="rubric-list">
            <li><span>Base repository</span><span class="rubric-pts">+0.4</span></li>
            <li><span>Verified 3-minute video walkthrough (YouTube, Loom, Vimeo, or <code>.mp4</code>/<code>.webm</code>)</span><span class="rubric-pts">+1.1</span></li>
            <li><span>Reproducible local setup instructions for judges (Quickstart, <code>.env.example</code>, <code>Makefile</code>, Docker)</span><span class="rubric-pts">+0.4</span></li>
            <li><span>Live hosted working deployment URL</span><span class="rubric-pts">+0.4</span></li>
            <li><span>Visual walkthrough, screenshots &amp; architecture diagrams (README &gt;6 KB)</span><span class="rubric-pts">+0.2</span></li>
            <li><span>Cap if neither video walkthrough nor live deployment is present</span><span class="rubric-pts">Max 1.0 / 2.5</span></li>
          </ul>
        </div>
        <div class="rubric-note">
          <strong>Self-Audit Disclosure &amp; Formula Integrity:</strong> This directory is maintained by <a href="https://watt-mind.com" target="_blank" rel="noopener" style="color:#4fdbc8;">Watt Mind</a> (builders of <a href="https://github.com/watt-mind/pii-guard" target="_blank" rel="noopener" style="color:#4fdbc8;"><code>watt-mind/pii-guard</code></a>). Because we designed our own repository around this exact engineering checklist, it naturally achieves the maximum automated score (10.0). Every repository&rsquo;s total score is strictly the exact arithmetic sum of its 4 pillars (<code>Impact + Meta AI Tooling + Technical Depth + Demo Completeness</code>). <em>Nov 5 Fix: Equalized the +0.4 Track Alignment weight across both Track 1 (Build for Your World) and Track 2 (Push the Frontier) based on Discord community feedback so both tracks share an identical 3.0/3.0 Impact ceiling. Nov 2 Fix: Removed an experimental keyword-based anti-project multiplier (0.4&times;) that previously caused false-positive rank drops and pillar-sum mismatches on 59 repositories whose READMEs contained compliance disclaimers.</em>
        </div>
      </div>
    </details>

    <!-- Multimodal Video Audit Methodology -->
    <div id="video-methodology" style="margin-top: 28px;">
      <div class="dir-header">
        <h2>Multimodal Video Audit Methodology (SAM 3.1 + Muse Spark 1.3)</h2>
        <span class="dir-status">Deterministic 6-criterion video rubric (0.00&ndash;2.50 scale) &middot; {video_demos} video repos audited</span>
      </div>
      <div class="methodology-grid" style="grid-template-columns: repeat(3, 1fr);">
        <div class="method-card">
          <div class="method-top">
            <span class="method-title">1. Stream &amp; Stopwatch Telemetry</span>
            <span class="method-weight">yt-dlp + ffprobe</span>
          </div>
          <p class="method-desc">Downloads each linked demo video (YouTube, Vimeo, Loom, or raw <code>.mp4</code>), flags placeholder or deleted URLs (<code>YOUR_VIDEO_ID</code>), measures exact duration against the 3:00 (<code>180s</code>) cutoff, and runs <code>ffmpeg volumedetect</code> on the 3:00 <code>16kHz</code> mono audio stream.</p>
        </div>
        <div class="method-card">
          <div class="method-top">
            <span class="method-title">2. 20 Keyframes + SAM 3.1</span>
            <span class="method-weight">Scene + UI Grounding</span>
          </div>
          <p class="method-desc">Extracts <strong>20 hybrid keyframes</strong> per video (<code>ffmpeg select='gt(scene,0.18)'</code> visual transitions + mandatory <code>2s, 8s, 15s</code> opening provenance anchors + uniform grid fill) and segments interactive UI controls via Meta&rsquo;s <strong><code>sam-3.1</code></strong> model.</p>
        </div>
        <div class="method-card">
          <div class="method-top">
            <span class="method-title">3. Muse Spark 1.3 Rubric</span>
            <span class="method-weight">2.50 pts Max</span>
          </div>
          <p class="method-desc">Evaluates all 20 keyframes + the 3:00 <code>.mp3</code> audio track in a single <strong><code>muse-spark-1.3</code></strong> multimodal pass and scores 6 verifiable criteria with zero black-box weighting.</p>
        </div>
      </div>

      <details class="rubric-details" id="video-rubric-details" open>
        <summary class="rubric-summary">
          <span>Exact 6-Criterion Video Scoring Formula (2.50 pts Max) &amp; Video Self-Audit Disclosure</span>
          <span class="rubric-toggle-wrap"><span>Toggle</span><span class="rubric-chevron">&#9662;</span></span>
        </summary>
        <div class="rubric-body">
          <div class="rubric-col">
            <h3>1. Stopwatch &amp; Playability <span>Max 0.30 pts (12%)</span></h3>
            <ul class="rubric-list">
              <li><span>Playable video within 3:00 stopwatch limit (<code>30s &le; duration &le; 185s</code>)</span><span class="rubric-pts">+0.30</span></li>
              <li><span>Playable video overrunning 3:00 limit (<code>&gt;185s</code>; only first 3:00 is evaluated)</span><span class="rubric-pts">+0.15</span></li>
              <li><span>Playable micro-clip under 30 seconds or broken primary host with GitHub raw fallback</span><span class="rubric-pts">+0.10 to +0.15</span></li>
              <li><span>Unplayable, private, or placeholder URL (e.g. <code>youtu.be/YOUR_VIDEO_ID</code>)</span><span class="rubric-pts neg">0.00</span></li>
            </ul>
            <h3 style="margin-top:14px;">2. Opening Provenance (0:00&ndash;0:20) <span>Max 0.30 pts (12%)</span></h3>
            <ul class="rubric-list">
              <li><span>1-line hackathon provenance statement shown on-screen or spoken in <code>0:00&ndash;0:20</code></span><span class="rubric-pts">+0.30</span></li>
              <li><span>Provenance stated later in the video (after <code>0:20</code>)</span><span class="rubric-pts">+0.15</span></li>
              <li><span>No hackathon provenance statement shown or spoken in video</span><span class="rubric-pts neg">0.00</span></li>
            </ul>
            <h3 style="margin-top:14px;">3. Live Product vs. Slideware <span>Max 0.80 pts (32%)</span></h3>
            <ul class="rubric-list">
              <li><span>Real working product demo with <code>&ge;75%</code> live UI/CLI footage (verified with <code>sam-3.1</code> UI boxes)</span><span class="rubric-pts">+0.80</span></li>
              <li><span>Working product demo with <code>50%&ndash;74%</code> live UI/CLI footage</span><span class="rubric-pts">+0.55</span></li>
              <li><span>Mostly slides/pitch deck with brief product glimpse (<code>20%&ndash;49%</code> live footage)</span><span class="rubric-pts">+0.25</span></li>
              <li><span>Static slideware, mockups, or talking head only (<code>&lt;20%</code> live product footage)</span><span class="rubric-pts neg">0.00</span></li>
            </ul>
          </div>
          <div class="rubric-col">
            <h3>4. Visible Meta AI Execution <span>Max 0.50 pts (20%)</span></h3>
            <ul class="rubric-list">
              <li><span>Live Meta AI model calls, logs, or outputs visibly demonstrated on screen</span><span class="rubric-pts">+0.25</span></li>
              <li><span>At least 1 specific Meta model named/shown in video (<code>Muse Spark</code>, <code>SAM 3.1</code>, <code>Llama</code>, etc.)</span><span class="rubric-pts">+0.15</span></li>
              <li><span>Multi-model Meta orchestration (2+ distinct Meta models shown working together)</span><span class="rubric-pts">+0.10</span></li>
            </ul>
            <h3 style="margin-top:14px;">5. Quantifiable Benchmarks (&lt;3:00) <span>Max 0.35 pts (14%)</span></h3>
            <ul class="rubric-list">
              <li><span>2+ concrete metrics (latency ms, F1/accuracy %, throughput) shown before <code>3:00</code></span><span class="rubric-pts">+0.35</span></li>
              <li><span>1 concrete quantitative metric shown before <code>3:00</code></span><span class="rubric-pts">+0.20</span></li>
              <li><span>No quantitative benchmarks shown before the <code>3:00</code> cutoff</span><span class="rubric-pts neg">0.00</span></li>
            </ul>
            <h3 style="margin-top:14px;">6. Audio &amp; Caption Clarity <span>Max 0.25 pts (10%)</span></h3>
            <ul class="rubric-list">
              <li><span>Audible English voiceover (<code>mean_volume &gt; &minus;55 dB</code>) + burned-in captions</span><span class="rubric-pts">+0.25</span></li>
              <li><span>Clear English voiceover without captions <em>or</em> burned-in captions with background music</span><span class="rubric-pts">+0.15</span></li>
              <li><span>Silent screen recording with burned-in captions/text callouts</span><span class="rubric-pts">+0.10</span></li>
              <li><span>Silent screen recording with no captions</span><span class="rubric-pts">+0.05</span></li>
            </ul>
          </div>
          <div class="rubric-note">
            <strong>Video Self-Audit Disclosure:</strong> Every public demo video is evaluated through the exact same automated <code>yt-dlp + ffprobe + SAM 3.1 + Muse Spark 1.3</code> pipeline and scored deterministically across the 6 criteria above. Currently, <strong>{video_perfect_count} repositories</strong> (including <code>watt-mind/pii-guard</code> and {video_other_perfect_count} competitor submissions) satisfy all 6 criteria for a <code>2.50 / 2.50</code> video score, while <strong>{video_dead_count} repositories</strong> with placeholder, private, or deleted video URLs receive <code>0.00 &#9888;</code>. Hover or click any video score pill in the table to inspect its extracted metrics, keyframes, and rubric ledger.
          </div>
        </div>
      </details>
    </div>
  </section>

</main>

<footer>
  <div class="footer-inner">
    <div>
      Unofficial community tracker maintained by <a href="https://watt-mind.com" target="_blank" rel="noopener">Watt Mind</a> (not affiliated with Meta or Cerebral Valley) &middot; <a href="#methodology" onclick="const d=document.getElementById('rubric-details');if(d)d.open=true;">Repo Scoring Formula</a> &middot; <a href="#video-methodology" onclick="const d=document.getElementById('video-rubric-details');if(d)d.open=true;">Video Audit Formula</a> &middot; <a href="/meta-hackathon-2026/checklist">Submission Checklist</a> &middot; Raw data: <a href="/meta-hackathon-2026/projects.json">projects.json</a> &amp; <a href="/meta-hackathon-2026/projects.csv">projects.csv</a>
    </div>
    <div>
      Indexing stopped (Final post-submission snapshot)
    </div>
  </div>
</footer>

<div id="readme-floating-tooltip" role="tooltip" aria-hidden="true"></div>

<script>
(function() {{
  const INITIAL_DATA = {compact_json_str};
  let projects = INITIAL_DATA.slice();
  const projectByName = new Map(projects.map(p => [p.n, p]));

  const state = {{
    query: '',
    track: '',
    category: '',
    model: '',
    sort: 'score',
    signals: new Set(),
    limit: 50
  }};

  const searchInput = document.getElementById('repo-search');
  const categorySelect = document.getElementById('category-select');
  const sortSelect = document.getElementById('sort-select');
  const trackTabs = document.querySelectorAll('#track-tabs .seg-tab');
  const trackCards = document.querySelectorAll('[data-track-card]');
  const catOverviewBtns = document.querySelectorAll('#category-overview-list .cat-filter-row');
  const modelOverviewBtns = document.querySelectorAll('#model-overview-list .model-filter-row');
  const sigOverviewRows = document.querySelectorAll('#signal-overview-list [data-signal]');
  const chipBtns = document.querySelectorAll('#signal-chips .chip-btn');
  const resetBtn = document.getElementById('reset-filters-btn');
  const tbody = document.getElementById('directory-tbody');
  const statusText = document.getElementById('dir-status-text');
  const footerCount = document.getElementById('table-footer-count');
  const btnMore = document.getElementById('btn-show-more');
  const btnAll = document.getElementById('btn-show-all');

  // Optional live hydration from /meta-hackathon-2026/projects.json if newer deltas exist
  fetch('/meta-hackathon-2026/projects.json')
    .then(r => r.ok ? r.json() : null)
    .then(liveData => {{
      if (!Array.isArray(liveData) || !liveData.length) return;
      const byName = new Map(liveData.map(x => [x.full_name, x]));
      projects.forEach(item => {{
        const fresh = byName.get(item.n);
        if (fresh) {{
          item.r = fresh.rank ?? item.r;
          item.s = fresh.score_total ?? item.s;
          item.cm = fresh.commits_in_window ?? item.cm;
          item.cb = fresh.commits_before_window ?? item.cb;
          item.pm = fresh.prs_merged ?? item.pm;
          item.pt = fresh.prs_total ?? item.pt;
          item.cd = fresh.commits_delta ?? item.cd;
          item.rd = fresh.rank_delta ?? item.rd;
          item.st_cnt = fresh.stars ?? item.st_cnt;
        }}
      }});
      render();
    }})
    .catch(() => {{}});

  function formatLive(p) {{
    if (!p.lv) return '<span class="cell-dash">&mdash;</span>';
    const u = (p.lu && p.lu[0]) ? p.lu[0].trim() : '';
    if (u.startsWith('http://') || u.startsWith('https://')) {{
      return `<a href="${{u}}" target="_blank" rel="noopener" class="sig-link">Live &#8599;</a>`;
    }}
    if (u.includes('/') || (u.split('.').length - 1) >= 2) {{
      return `<a href="https://${{u}}" target="_blank" rel="noopener" class="sig-link">Live &#8599;</a>`;
    }}
    if (u) {{
      const host = u.replace(/\\.(app|run|dev|io|com)$/i, '');
      return `<span class="sig-check" title="Referenced host: ${{u}}">&#10003; <span class="sig-host">${{host}}</span></span>`;
    }}
    return '<span class="sig-check">&#10003;</span>';
  }}

  function formatVideo(p) {{
    if (!p.vd) return '<span class="cell-dash">&mdash;</span>';
    const u = (p.vu && p.vu[0]) ? p.vu[0].trim() : '';
    let linkHtml = '<span class="sig-check">&#10003;</span>';
    if (u.startsWith('http://') || u.startsWith('https://')) {{
      linkHtml = `<a href="${{u}}" target="_blank" rel="noopener" class="sig-link">Video &#8599;</a>`;
    }} else if (u.includes('/')) {{
      linkHtml = `<a href="https://${{u}}" target="_blank" rel="noopener" class="sig-link">Video &#8599;</a>`;
    }}
    if (p.va) {{
      if (p.va.st === 'ok') {{
        const vs = Number(p.va.vs || 0);
        const vCls = vs >= 2.0 ? 'vid-score-pill high' : (vs >= 1.3 ? 'vid-score-pill mid' : 'vid-score-pill low');
        return `<div class="vid-cell-wrap">${{linkHtml}}<span class="${{vCls}}" data-video-repo="${{p.n}}" tabindex="0" role="button" aria-label="Video score breakdown for ${{p.n}}">${{vs.toFixed(2)}}</span></div>`;
      }} else if (p.va.st === 'dead') {{
        return `<div class="vid-cell-wrap">${{linkHtml}}<span class="vid-score-pill dead" data-video-repo="${{p.n}}" tabindex="0" role="button" aria-label="Unplayable or placeholder video link for ${{p.n}}">0.00 &#9888;</span></div>`;
      }}
    }}
    return linkHtml;
  }}

  function syncUIControls() {{
    trackTabs.forEach(btn => {{
      btn.classList.toggle('active', btn.dataset.track === state.track);
    }});
    trackCards.forEach(btn => {{
      btn.classList.toggle('active', btn.dataset.trackCard === state.track);
    }});
    catOverviewBtns.forEach(btn => {{
      btn.classList.toggle('active', btn.dataset.category === state.category);
    }});
    modelOverviewBtns.forEach(btn => {{
      btn.classList.toggle('active', btn.dataset.model === state.model);
    }});
    categorySelect.value = state.category;
    chipBtns.forEach(btn => {{
      btn.classList.toggle('active', state.signals.has(btn.dataset.chip));
    }});
    sigOverviewRows.forEach(row => {{
      row.classList.toggle('active', state.signals.has(row.dataset.signal));
    }});
    const hasFilters = Boolean(state.query || state.track || state.category || state.model || state.signals.size > 0 || state.sort !== 'score');
    resetBtn.style.display = hasFilters ? 'inline-block' : 'none';
  }}

  const partnerSpecList = [
    ['baseten', 'Baseten'],
    ['fireworks', 'Fireworks'],
    ['modal', 'Modal'],
    ['together', 'Together']
  ];

  function render() {{
    syncUIControls();
    const q = state.query.toLowerCase();

    const filtered = projects.filter(p => {{
      if (q && !p.n.toLowerCase().includes(q) && !p.c.toLowerCase().includes(q) && !(p.lr && p.lr.toLowerCase().includes(q)) && !(p.sm_txt && p.sm_txt.toLowerCase().includes(q)) && !(p.rs && p.rs.toLowerCase().includes(q)) && !(p.ms && p.ms.some(m => m.includes(q)))) return false;
      if (state.track && p.t !== state.track) return false;
      if (state.category && p.c !== state.category) return false;
      if (state.model && !(p.ms && p.ms.includes(state.model))) return false;
      if (state.signals.has('active') && p.cm <= 0) return false;
      if (state.signals.has('clean') && p.pre) return false;
      if (state.signals.has('prs') && (p.pm || p.pt || 0) <= 0) return false;
      if (state.signals.has('velocity') && p.cm < 20) return false;
      if (state.signals.has('live') && !p.lv) return false;
      if (state.signals.has('video') && !p.vd) return false;
      if (state.signals.has('docker') && !p.dk) return false;
      if (state.signals.has('tests') && !p.ts) return false;
      if (state.signals.has('weights') && !p.ow) return false;
      return true;
    }});

    filtered.sort((a, b) => {{
      if (state.sort === 'video_score') {{
        const va = a.va ? (a.va.st === 'ok' ? Number(a.va.vs || 0) : -0.5) : -1;
        const vb = b.va ? (b.va.st === 'ok' ? Number(b.va.vs || 0) : -0.5) : -1;
        return (vb - va) || (b.s - a.s) || (b.cm - a.cm);
      }}
      if (state.sort === 'commits') return (b.cm - a.cm) || (b.s - a.s);
      if (state.sort === 'prs') return ((b.pm || b.pt || 0) - (a.pm || a.pt || 0)) || (b.s - a.s);
      if (state.sort === 'stars') return (b.st_cnt - a.st_cnt) || (b.s - a.s);
      if (state.sort === 'newest') return (b.cr || '').localeCompare(a.cr || '');
      return (b.s - a.s) || (b.cm - a.cm) || (b.st_cnt - a.st_cnt);
    }});

    const visible = filtered.slice(0, state.limit);
    const totalMatched = filtered.length;

    statusText.textContent = totalMatched === projects.length
      ? `Showing ${{visible.length}} of ${{totalMatched}} repositories`
      : `Matched ${{totalMatched}} repositories (showing ${{visible.length}})`;

    footerCount.textContent = totalMatched === 0
      ? 'No matching repositories'
      : `Showing 1\u2013${{visible.length}} of ${{totalMatched}} repositories`;

    btnMore.style.display = visible.length < totalMatched ? 'inline-block' : 'none';
    btnAll.style.display = visible.length < totalMatched ? 'inline-block' : 'none';
    btnAll.textContent = `Show all ${{totalMatched}}`;

    if (visible.length === 0) {{
      tbody.innerHTML = `<tr>
        <td colspan="8" class="empty-state-cell">
          <strong>No matching repositories found.</strong><br/>
          Try clearing your search query or resetting the active track, category, or signal filters above.
        </td>
      </tr>`;
      return;
    }}

    tbody.innerHTML = visible.map(p => {{
      const parts = p.n.split('/');
      const owner = parts.length === 2 ? parts[0] + '/' : '';
      const name = parts.length === 2 ? parts[1] : p.n;
      const stars = p.st_cnt > 0 ? `<span class="repo-stars" title="${{p.st_cnt}} GitHub stars">&#9733; ${{p.st_cnt}}</span>` : '';
      const mrBadge = (p.mr && p.mr > 1) ? `<span class="multi-repo-badge" title="${{p.mt || ''}}">${{p.mr}} repos</span>` : '';
      const trk = p.t === 'Track 2'
        ? '<span class="trk-tag t2" title="Track 2: Push the Frontier">T2</span>'
        : '<span class="trk-tag t1" title="Track 1: Build for Your World">T1</span>';
      const sCls = p.s >= 7.0 ? 'score-pill high' : (p.s >= 5.5 ? 'score-pill mid' : 'score-pill');
      const sTip = `Impact: ${{p.si}}/3.0 \u00b7 Meta AI: ${{p.sm}}/2.5 \u00b7 Tech: ${{p.st}}/2.0 \u00b7 Demo: ${{p.sd}}/2.5`;
      const cDelta = p.cd > 0 ? `<span class="delta-up">+${{p.cd}}</span>` : '';
      const crDate = (p.cr || '').slice(0, 10);
      let preHtml = '';
      if (p.cb > 0) {{
        preHtml = `<span class="pre-badge" title="${{p.cb}} commits before Oct 26, 2026 (repo created ${{crDate}})">${{p.cb}} pre</span>`;
      }} else if (p.pre) {{
        preHtml = `<span class="pre-badge" title="Repository created before Oct 26, 2026 (${{crDate}})">pre-Oct 26</span>`;
      }}
      const prVal = p.pm > 0 ? p.pm : (p.pt || 0);
      const prHtml = prVal > 0
        ? `<span class="prs-num" title="${{p.pm || 0}} merged / ${{p.pt || 0}} total pull requests">${{prVal}}</span>`
        : '<span class="cell-dash">&mdash;</span>';

      let rDelta = '';
      if (p.rd > 0) rDelta = `<span class="rank-delta up" title="Moved up ${{p.rd}}">&#9650;${{p.rd}}</span>`;
      else if (p.rd < 0) rDelta = `<span class="rank-delta down" title="Moved down ${{Math.abs(p.rd)}}">&#9660;${{Math.abs(p.rd)}}</span>`;

      const pPills = (p.ms && p.ms.length)
        ? partnerSpecList.filter(([k]) => p.ms.includes(k)).map(([k, lbl]) => `<button type="button" class="partner-tag pt-${{k}}${{state.model === k ? ' active' : ''}}" data-partner="${{k}}" title="Partner Inference: ${{lbl}} (click to filter directory)">${{lbl}}</button>`).join('')
        : '';
      const partnerHtml = pPills ? `<span class="partner-tags-wrap">${{pPills}}</span>` : '';

      return `<tr>
        <td class="col-rank"><span class="rank-num">${{p.r}}</span>${{rDelta}}</td>
        <td class="col-repo" data-repo="${{p.n}}">
          <a href="${{p.u}}" target="_blank" rel="noopener" class="repo-link"><span class="repo-owner">${{owner}}</span><span class="repo-name">${{name}}</span></a>${{mrBadge}}${{stars}}${{partnerHtml}}
        </td>
        <td class="col-cat">
          <div class="cat-cell-wrap">${{trk}}<span class="cat-label">${{p.c}}</span></div>
        </td>
        <td class="col-num"><span class="${{sCls}}" data-score-repo="${{p.n}}" tabindex="0" role="button" aria-label="Score breakdown for ${{p.n}}">${{p.s.toFixed(1)}}</span></td>
        <td class="col-num"><span class="commits-num">${{p.cm}}</span>${{cDelta}}${{preHtml}}</td>
        <td class="col-num">${{prHtml}}</td>
        <td class="col-sig">${{formatLive(p)}}</td>
        <td class="col-sig">${{formatVideo(p)}}</td>
      </tr>`;
    }}).join('');
  }}

  searchInput.addEventListener('input', e => {{
    state.query = e.target.value.trim();
    state.limit = 50;
    render();
  }});

  window.addEventListener('keydown', e => {{
    if (e.key === '/' && document.activeElement !== searchInput) {{
      e.preventDefault();
      searchInput.focus();
    }}
  }});

  trackTabs.forEach(btn => {{
    btn.addEventListener('click', () => {{
      state.track = btn.dataset.track;
      state.limit = 50;
      render();
    }});
  }});

  trackCards.forEach(btn => {{
    btn.addEventListener('click', () => {{
      const t = btn.dataset.trackCard;
      state.track = state.track === t ? '' : t;
      state.limit = 50;
      render();
    }});
  }});

  catOverviewBtns.forEach(btn => {{
    btn.addEventListener('click', () => {{
      const c = btn.dataset.category;
      state.category = state.category === c ? '' : c;
      state.limit = 50;
      render();
    }});
  }});

  modelOverviewBtns.forEach(btn => {{
    btn.addEventListener('click', () => {{
      const m = btn.dataset.model;
      state.model = state.model === m ? '' : m;
      state.limit = 50;
      render();
    }});
  }});

  categorySelect.addEventListener('change', e => {{
    state.category = e.target.value;
    state.limit = 50;
    render();
  }});

  sortSelect.addEventListener('change', e => {{
    state.sort = e.target.value;
    render();
  }});

  function toggleSignal(sig) {{
    if (!sig) return;
    if (state.signals.has(sig)) state.signals.delete(sig);
    else state.signals.add(sig);
    state.limit = 50;
    render();
  }}

  chipBtns.forEach(btn => {{
    btn.addEventListener('click', () => toggleSignal(btn.dataset.chip));
  }});

  sigOverviewRows.forEach(row => {{
    row.addEventListener('click', () => toggleSignal(row.dataset.signal));
  }});

  resetBtn.addEventListener('click', () => {{
    state.query = '';
    state.track = '';
    state.category = '';
    state.model = '';
    state.sort = 'score';
    state.signals.clear();
    state.limit = 50;
    searchInput.value = '';
    sortSelect.value = 'score';
    render();
  }});

  btnMore.addEventListener('click', () => {{
    state.limit += 100;
    render();
  }});

  btnAll.addEventListener('click', () => {{
    state.limit = 9999;
    render();
  }});

  document.querySelectorAll('.copy-tag').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const text = btn.getAttribute('data-copy') || '';
      if (!text) return;
      navigator.clipboard.writeText(text).then(() => {{
        const hint = btn.querySelector('.copy-hint');
        btn.classList.add('copied');
        if (hint) hint.textContent = 'copied!';
        setTimeout(() => {{
          btn.classList.remove('copied');
          if (hint) hint.textContent = 'copy';
        }}, 1600);
      }}).catch(() => {{}});
    }});
  }});

  const tooltipEl = document.getElementById('readme-floating-tooltip');
  let activeTipRepo = null;
  let activeTipMode = null;
  let hideTipTimer = null;
  let lastTipShownAt = 0;
  let lastTipScrollY = 0;

  function escapeHtml(str) {{
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }}

  function positionFloatingTooltip(anchorEl) {{
    const rect = anchorEl.getBoundingClientRect();
    const tipRect = tooltipEl.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    const fitsBelow = (rect.bottom + 8 + tipRect.height) <= (vh - 12);
    const fitsAbove = (rect.top - 8 - tipRect.height) >= 12;

    let left = rect.left + 8;
    let top = rect.bottom + 6;

    if (rect.left > vw * 0.5) {{
      left = Math.max(12, rect.right - tipRect.width);
    }}
    if (left + tipRect.width > vw - 12) {{
      left = Math.max(12, vw - tipRect.width - 12);
    }}

    if (fitsBelow) {{
      top = rect.bottom + 6;
    }} else if (fitsAbove) {{
      top = rect.top - tipRect.height - 6;
    }} else {{
      // Anchor is near vertical middle and tooltip is tall: place to the left or right of the pill so it never covers the trigger
      if (rect.left - tipRect.width - 12 >= 12) {{
        left = rect.left - tipRect.width - 12;
      }} else if (rect.right + 12 + tipRect.width <= vw - 12) {{
        left = rect.right + 12;
      }}
      top = Math.max(12, Math.min(rect.top - Math.round(tipRect.height * 0.35), vh - tipRect.height - 12));
    }}

    tooltipEl.style.left = `${{Math.round(left)}}px`;
    tooltipEl.style.top = `${{Math.round(top)}}px`;
    lastTipShownAt = Date.now();
    lastTipScrollY = window.scrollY;
  }}

  function showReadmeTooltip(anchorEl, repoName) {{
    const p = projectByName.get(repoName);
    if (!p || (!p.rs && !p.sm_txt)) return;
    if (hideTipTimer) {{
      clearTimeout(hideTipTimer);
      hideTipTimer = null;
    }}
    activeTipRepo = repoName;
    activeTipMode = 'readme';
    tooltipEl.classList.remove('mode-video');
    const hook = p.sm_txt || '';
    const body = (p.rs && p.rs !== hook) ? p.rs : (p.rs || hook);
    const showHook = Boolean(hook && body && hook !== body);
    const partnerTagsArr = (p.ms && p.ms.length)
      ? partnerSpecList.filter(([k]) => p.ms.includes(k)).map(([k, lbl]) => `<span class="rt-tag pt-${{k}}">&#9889; ${{lbl}}</span>`)
      : [];
    const techTagsArr = (p.th && p.th.length)
      ? p.th.map(t => `<span class="rt-tag">${{escapeHtml(t)}}</span>`)
      : [];
    const allTags = partnerTagsArr.concat(techTagsArr);
    const tagsHtml = allTags.length
      ? `<div class="rt-tags">${{allTags.join('')}}</div>`
      : '';
    const trkBadge = p.t === 'Track 2'
      ? '<span class="trk-tag t2">T2</span>'
      : '<span class="trk-tag t1">T1</span>';

    tooltipEl.innerHTML = `
      <div class="rt-hdr">
        <span class="rt-repo">#${{p.r}} ${{escapeHtml(p.n)}}</span>
        <div class="rt-meta">${{trkBadge}}<span class="score-pill ${{p.s >= 7.0 ? 'high' : 'mid'}}">${{p.s.toFixed(1)}}</span></div>
      </div>
      ${{showHook ? `<div class="rt-hook">${{escapeHtml(hook)}}</div>` : ''}}
      <div class="rt-body">${{escapeHtml(body)}}</div>
      ${{tagsHtml}}
      <div class="rt-ftr">
        <span>${{p.cm}} commits &middot; ${{escapeHtml(p.c)}}</span>
        <span>Muse Spark 1.3 Summary</span>
      </div>
    `;
    tooltipEl.classList.add('visible');
    tooltipEl.setAttribute('aria-hidden', 'false');
    positionFloatingTooltip(anchorEl);
  }}

  function showScoreTooltip(anchorEl, repoName) {{
    const p = projectByName.get(repoName);
    if (!p) return;
    if (hideTipTimer) {{
      clearTimeout(hideTipTimer);
      hideTipTimer = null;
    }}
    activeTipRepo = repoName;
    activeTipMode = 'score';
    tooltipEl.classList.remove('mode-video');
    const sb = p.sb || {{}};
    const pillars = [
      {{ key: 'impact', label: '1. Impact & Alignment', val: p.si || 0, max: 3.0, color: '#4fdbc8' }},
      {{ key: 'meta', label: '2. Meta AI Tooling', val: p.sm || 0, max: 2.5, color: '#38bdf8' }},
      {{ key: 'tech', label: '3. Technical Depth', val: p.st || 0, max: 2.0, color: '#818cf8' }},
      {{ key: 'demo', label: '4. Demo Completeness', val: p.sd || 0, max: 2.5, color: '#f59e0b' }}
    ];
    const trkBadge = p.t === 'Track 2'
      ? '<span class="trk-tag t2">T2</span>'
      : '<span class="trk-tag t1">T1</span>';

    const pillarsHtml = pillars.map(pil => {{
      const pct = Math.min(100, Math.max(4, (pil.val / pil.max) * 100));
      const items = sb[pil.key] || [];
      const itemsHtml = items.map(it => {{
        const pts = String(it[1] || '');
        const negCls = pts.startsWith('-') ? ' neg' : '';
        return `<div class="sb-item"><span>${{escapeHtml(it[0])}}</span><span class="sb-pts${{negCls}}">${{escapeHtml(pts)}}</span></div>`;
      }}).join('');
      return `
        <div class="sb-pillar">
          <div class="sb-pillar-hdr">
            <span class="sb-pillar-name">${{pil.label}}</span>
            <span class="sb-pillar-val">${{pil.val.toFixed(1)}} / ${{pil.max.toFixed(1)}}</span>
          </div>
          <div class="sb-bar-bg"><div class="sb-bar-fg" style="width:${{pct.toFixed(1)}}%;background:${{pil.color}};"></div></div>
          <div class="sb-items">${{itemsHtml}}</div>
        </div>
      `;
    }}).join('');

    tooltipEl.innerHTML = `
      <div class="rt-hdr">
        <span class="rt-repo">#${{p.r}} ${{escapeHtml(p.n)}}</span>
        <div class="rt-meta">${{trkBadge}}<span class="score-pill ${{p.s >= 7.0 ? 'high' : 'mid'}}">${{p.s.toFixed(1)}} / 10</span></div>
      </div>
      <div class="sb-grid">${{pillarsHtml}}</div>
      <div class="rt-ftr">
        <span>Unofficial Auto-Heuristic &middot; <a href="#methodology" style="color:#4fdbc8;text-decoration:none;" onclick="const d=document.getElementById('rubric-details');if(d)d.open=true;">How we calculate &darr;</a></span>
        <span>Total: ${{p.s.toFixed(1)}} / 10.0</span>
      </div>
    `;
    tooltipEl.classList.add('visible');
    tooltipEl.setAttribute('aria-hidden', 'false');
    positionFloatingTooltip(anchorEl);
  }}

  function formatDurationMMSS(sec) {{
    const s = Math.max(0, Math.round(Number(sec || 0)));
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${{m}}:${{rem < 10 ? '0' : ''}}${{rem}}`;
  }}

  function formatNarrationLabel(nar, cap) {{
    if (nar === 'human_voice') return cap ? 'Human Voice + CC' : 'Human Voiceover';
    if (nar === 'ai_voiceover' || nar === 'clear_english_voiceover') return cap ? 'Voiceover + CC' : 'English Voiceover';
    if (nar === 'captions_and_music') return 'Music + Burned CC';
    if (nar === 'silent_screen_recording') return cap ? 'Silent + CC' : 'Silent Screen';
    return cap ? 'Burned-in CC' : 'Audio Track';
  }}

  function showVideoTooltip(anchorEl, repoName) {{
    const p = projectByName.get(repoName);
    if (!p || !p.va) return;
    if (hideTipTimer) {{
      clearTimeout(hideTipTimer);
      hideTipTimer = null;
    }}
    activeTipRepo = repoName;
    activeTipMode = 'video';
    tooltipEl.classList.add('mode-video');
    const va = p.va;
    const trkBadge = p.t === 'Track 2'
      ? '<span class="trk-tag t2">T2</span>'
      : '<span class="trk-tag t1">T1</span>';

    if (va.st === 'dead') {{
      tooltipEl.innerHTML = `
        <div class="rt-hdr">
          <span class="rt-repo">#${{p.r}} ${{escapeHtml(p.n)}}</span>
          <div class="rt-meta">${{trkBadge}}<span class="vid-score-pill dead">0.00 / 2.50 &#9888;</span></div>
        </div>
        <div class="sb-grid">
          <div class="sb-pillar" style="border-color:rgba(248,113,113,0.35);background:rgba(248,113,113,0.06);">
            <div class="sb-pillar-hdr">
              <span class="sb-pillar-name" style="color:#f87171;">Unplayable / Placeholder Video Link</span>
              <span class="sb-pillar-val" style="color:#f87171;">0.00 / 2.50</span>
            </div>
            <div class="sb-items">
              <div class="sb-item"><span>${{escapeHtml(va.err || 'Video URL could not be downloaded or played via yt-dlp / ffprobe.')}}</span></div>
              ${{va.url ? `<div class="sb-item"><span style="color:#94a3b8;word-break:break-all;">URL: ${{escapeHtml(va.url)}}</span></div>` : ''}}
            </div>
          </div>
        </div>
        <div class="rt-ftr">
          <span>yt-dlp + ffprobe Verification</span>
          <span>Video Score: 0.00 / 2.50</span>
        </div>
      `;
      tooltipEl.classList.add('visible');
      tooltipEl.setAttribute('aria-hidden', 'false');
      positionFloatingTooltip(anchorEl);
      return;
    }}

    const vs = Number(va.vs || 0);
    const vCls = vs >= 2.0 ? 'vid-score-pill high' : (vs >= 1.3 ? 'vid-score-pill mid' : 'vid-score-pill low');
    const cVals = va.c || [0, 0, 0, 0, 0, 0];

    const durMMSS = formatDurationMMSS(va.dur);
    const durStatus = va.w3m
      ? '<span style="color:#4fdbc8;">&le;3:00 &#10003;</span>'
      : `<span style="color:#fbbf24;">+${{Math.round(va.ovr || 0)}}s &#9888;</span>`;
    const dbStr = (va.db !== null && va.db !== undefined) ? `${{Number(va.db).toFixed(1)}} dB` : 'No audio';
    const narLabel = formatNarrationLabel(va.nar, va.cap);
    const isOpeningProv = (va.ptm === 'opening_20s' || va.ptm === '0_00_to_0_20');
    const isLaterProv = (va.ptm === 'later_in_video' || va.ptm === 'after_0_20');
    const provStatus = isOpeningProv
      ? '<span style="color:#4fdbc8;">0:00&ndash;0:20 &#10003;</span>'
      : (isLaterProv ? '<span style="color:#fbbf24;">After 0:20 &#9888;</span>' : '<span style="color:#f87171;">Missing &#10005;</span>');

    const kpiStripHtml = `
      <div class="vt-kpi-strip">
        <div class="vt-kpi-tile">
          <span class="vt-kpi-lbl">Stopwatch</span>
          <span class="vt-kpi-val">${{durMMSS}} ${{durStatus}}</span>
          <span class="vt-kpi-sub">${{va.res || 'Playable MP4'}}</span>
        </div>
        <div class="vt-kpi-tile">
          <span class="vt-kpi-lbl">Live Product</span>
          <span class="vt-kpi-val">${{va.pct || 0}}% UI/CLI</span>
          <span class="vt-kpi-sub">${{va.sam || 0}} SAM 3.1 boxes</span>
        </div>
        <div class="vt-kpi-tile">
          <span class="vt-kpi-lbl">Audio &amp; CC</span>
          <span class="vt-kpi-val">${{narLabel}}</span>
          <span class="vt-kpi-sub">Vol: ${{dbStr}}</span>
        </div>
        <div class="vt-kpi-tile">
          <span class="vt-kpi-lbl">Provenance</span>
          <span class="vt-kpi-val">${{provStatus}}</span>
          <span class="vt-kpi-sub">${{isOpeningProv ? 'In first 20s' : (isLaterProv ? 'Stated later' : 'No opening line')}}</span>
        </div>
      </div>
    `;

    const c1Sub = va.w3m
      ? `Playable (${{va.dur}}s \u2264 180s limit)`
      : `Overruns 3:00 by +${{va.ovr || Math.round(va.dur - 180)}}s (${{va.dur}}s total)`;
    const c2Sub = isOpeningProv
      ? (va.pev && va.pev !== 'None shown' ? `"${{va.pev}}"` : 'Stated in opening 0:00\u20130:20')
      : (isLaterProv ? (va.pev && va.pev !== 'None shown' ? `After 0:20: "${{va.pev}}"` : 'Stated after 0:20 opening window') : 'No 1-line hackathon provenance in 0:00\u20130:20');
    const c3Sub = `${{va.pct || 0}}% real UI/CLI footage · ${{va.sam || 0}} SAM UI boxes${{va.ui && va.ui[0] ? ' · ' + va.ui[0] : ''}}`;
    const c4Sub = va.lcall
      ? `Live Meta calls shown · ${{(va.mod || []).length}} model(s) visible`
      : ((va.mod || []).length ? `Named ${{(va.mod || []).length}} model(s), no live trace shown` : 'No Meta AI execution shown in video');
    const c5Sub = (va.bch || []).length > 0
      ? `${{(va.bch || []).length}} metric(s) shown before 3:00 cutoff`
      : 'No concrete latency/accuracy numbers <3:00';
    const c6Sub = `${{narLabel}} (${{dbStr}})`;

    const criteria = [
      {{ label: '1. Stopwatch Limit', val: Number(cVals[0] || 0), max: 0.30, color: '#4fdbc8', sub: c1Sub }},
      {{ label: '2. Opening Provenance', val: Number(cVals[1] || 0), max: 0.30, color: '#38bdf8', sub: c2Sub }},
      {{ label: '3. Live Product vs. Slides', val: Number(cVals[2] || 0), max: 0.80, color: '#2dd4bf', sub: c3Sub }},
      {{ label: '4. Meta AI Execution', val: Number(cVals[3] || 0), max: 0.50, color: '#818cf8', sub: c4Sub }},
      {{ label: '5. Benchmarks (<3:00)', val: Number(cVals[4] || 0), max: 0.35, color: '#f59e0b', sub: c5Sub }},
      {{ label: '6. Audio & Captions', val: Number(cVals[5] || 0), max: 0.25, color: '#a78bfa', sub: c6Sub }}
    ];

    const criteriaHtml = criteria.map(cr => {{
      const pct = Math.min(100, Math.max(4, (cr.val / cr.max) * 100));
      const ptsCls = cr.val <= 0 ? 'zero' : (cr.val < cr.max ? 'mid' : '');
      const cardCls = cr.val <= 0 ? 'vt-crit-card zero' : (cr.val < cr.max ? 'vt-crit-card mid' : 'vt-crit-card');
      return `
        <div class="${{cardCls}}">
          <div class="vt-crit-hdr">
            <span class="vt-crit-name">${{cr.label}}</span>
            <span class="vt-crit-pts ${{ptsCls}}">+${{cr.val.toFixed(2)}}/${{cr.max.toFixed(2)}}</span>
          </div>
          <div class="sb-bar-bg" style="margin-bottom:2px;height:3px;"><div class="sb-bar-fg" style="width:${{pct.toFixed(1)}}%;background:${{cr.color}};"></div></div>
          <div class="vt-crit-sub">${{escapeHtml(cr.sub)}}</div>
        </div>
      `;
    }}).join('');

    const modelsLine = (va.mod && va.mod.length)
      ? `<div class="vt-proof-line"><span class="vt-proof-lbl">Models in Video:</span>${{va.mod.map(m => `<span class="vt-chip-model">${{escapeHtml(m)}}</span>`).join('')}}</div>`
      : '';
    const benchLine = (va.bch && va.bch.length)
      ? `<div class="vt-proof-line"><span class="vt-proof-lbl">On-Screen Metrics:</span>${{va.bch.slice(0, 3).map(b => `<span class="vt-chip-bench" title="${{escapeHtml(b)}}">${{escapeHtml(b)}}</span>`).join('')}}</div>`
      : '';
    const proofHtml = (modelsLine || benchLine)
      ? `<div class="vt-proof-row">${{modelsLine}}${{benchLine}}</div>`
      : '';

    const notesHtml = (va.str || va.wk || va.mev) ? `
      <div class="vt-note-box">
        ${{va.mev && va.mev !== 'None' ? `<div class="vt-note-row"><strong style="color:#38bdf8;">&#9679; Meta Execution Proof:</strong> ${{escapeHtml(va.mev)}}</div>` : ''}}
        ${{va.str ? `<div class="vt-note-row"><strong style="color:#4fdbc8;">+ Strengths:</strong> ${{escapeHtml(va.str)}}</div>` : ''}}
        ${{va.wk ? `<div class="vt-note-row"><strong style="color:#fbbf24;">! Watchouts:</strong> ${{escapeHtml(va.wk)}}</div>` : ''}}
      </div>
    ` : '';

    tooltipEl.innerHTML = `
      <div class="rt-hdr">
        <span class="rt-repo">#${{p.r}} ${{escapeHtml(p.n)}}</span>
        <div class="rt-meta">${{trkBadge}}<span class="${{vCls}}">${{vs.toFixed(2)}} / 2.50</span></div>
      </div>
      ${{kpiStripHtml}}
      <div class="vt-rubric-grid">${{criteriaHtml}}</div>
      ${{proofHtml}}
      ${{notesHtml}}
      <div class="rt-ftr">
        <span>SAM 3.1 + Muse Spark 1.3 &middot; <a href="#video-methodology" style="color:#4fdbc8;text-decoration:none;" onclick="const d=document.getElementById('video-rubric-details');if(d)d.open=true;">How we score videos &darr;</a></span>
        <span>Video Audit: ${{vs.toFixed(2)}} / 2.50</span>
      </div>
    `;
    tooltipEl.classList.add('visible');
    tooltipEl.setAttribute('aria-hidden', 'false');
    positionFloatingTooltip(anchorEl);
  }}

  function hideReadmeTooltip(immediate) {{
    if (hideTipTimer) clearTimeout(hideTipTimer);
    if (immediate) {{
      tooltipEl.classList.remove('visible');
      tooltipEl.setAttribute('aria-hidden', 'true');
      activeTipRepo = null;
      activeTipMode = null;
      return;
    }}
    hideTipTimer = setTimeout(() => {{
      tooltipEl.classList.remove('visible');
      tooltipEl.setAttribute('aria-hidden', 'true');
      activeTipRepo = null;
      activeTipMode = null;
    }}, 130);
  }}

  tooltipEl.addEventListener('mouseenter', () => {{
    if (hideTipTimer) {{
      clearTimeout(hideTipTimer);
      hideTipTimer = null;
    }}
  }});

  tooltipEl.addEventListener('mouseleave', () => {{
    hideReadmeTooltip(false);
  }});

  tbody.addEventListener('mouseover', e => {{
    const vidPill = e.target.closest('.vid-score-pill[data-video-repo]');
    if (vidPill) {{
      showVideoTooltip(vidPill, vidPill.dataset.videoRepo);
      return;
    }}
    const scorePill = e.target.closest('.score-pill[data-score-repo]');
    if (scorePill) {{
      showScoreTooltip(scorePill, scorePill.dataset.scoreRepo);
      return;
    }}
    const cell = e.target.closest('.col-repo');
    if (!cell || !cell.dataset.repo) return;
    showReadmeTooltip(cell, cell.dataset.repo);
  }});

  tbody.addEventListener('mouseout', e => {{
    const vidPill = e.target.closest('.vid-score-pill[data-video-repo]');
    if (vidPill) {{
      const rel = e.relatedTarget;
      if (rel && vidPill.contains(rel)) return;
      hideReadmeTooltip(false);
      return;
    }}
    const scorePill = e.target.closest('.score-pill[data-score-repo]');
    if (scorePill) {{
      const rel = e.relatedTarget;
      if (rel && scorePill.contains(rel)) return;
      hideReadmeTooltip(false);
      return;
    }}
    const cell = e.target.closest('.col-repo');
    if (!cell) return;
    const rel = e.relatedTarget;
    if (rel && cell.contains(rel)) return;
    hideReadmeTooltip(false);
  }});

  tbody.addEventListener('click', e => {{
    const vidPill = e.target.closest('.vid-score-pill[data-video-repo]');
    if (vidPill) {{
      e.preventDefault();
      e.stopPropagation();
      const repo = vidPill.dataset.videoRepo;
      if (activeTipRepo === repo && activeTipMode === 'video' && tooltipEl.classList.contains('visible')) {{
        hideReadmeTooltip(true);
      }} else {{
        showVideoTooltip(vidPill, repo);
      }}
      return;
    }}
    const scorePill = e.target.closest('.score-pill[data-score-repo]');
    if (scorePill) {{
      e.preventDefault();
      e.stopPropagation();
      const repo = scorePill.dataset.scoreRepo;
      if (activeTipRepo === repo && activeTipMode === 'score' && tooltipEl.classList.contains('visible')) {{
        hideReadmeTooltip(true);
      }} else {{
        showScoreTooltip(scorePill, repo);
      }}
      return;
    }}
    const partnerBtn = e.target.closest('.partner-tag[data-partner]');
    if (partnerBtn) {{
      e.preventDefault();
      e.stopPropagation();
      const pk = partnerBtn.dataset.partner;
      state.model = state.model === pk ? '' : pk;
      state.limit = 50;
      hideReadmeTooltip(true);
      render();
    }}
  }});

  window.addEventListener('scroll', () => {{
    if (activeTipRepo && Math.abs(window.scrollY - lastTipScrollY) > 8 && (Date.now() - lastTipShownAt > 120)) {{
      hideReadmeTooltip(true);
    }}
  }}, {{ passive: true }});

  window.addEventListener('keydown', e => {{
    if (e.key === 'Escape' && activeTipRepo) hideReadmeTooltip(true);
  }});
}})();
</script>

</body>
</html>
"""

with open('meta_hackathon_competitor_analysis_report.html', 'w') as f:
    f.write(public_html)

print("Generated Public Project Directory (meta_hackathon_competitor_analysis_report.html)!")
