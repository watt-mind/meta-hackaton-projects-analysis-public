import json
import os
import subprocess
import time
from datetime import datetime, timezone

HISTORY_DIR = 'history'
SNAPSHOTS_DIR = os.path.join(HISTORY_DIR, 'snapshots')
TIMESERIES_FILE = os.path.join(HISTORY_DIR, 'timeseries.json')
AUDITED_FILE = 'projects_inventory_audited.json'

os.makedirs(SNAPSHOTS_DIR, exist_ok=True)


def summarize_projects(projects, timestamp_iso):
    total_repos = len(projects)
    active_in_window = sum(1 for p in projects if p.get('commits_in_window', 0) > 0)
    high_velocity = sum(1 for p in projects if p.get('commits_in_window', 0) >= 20)
    total_commits = sum(p.get('commits_in_window', 0) for p in projects)
    video_demos = sum(1 for p in projects if p.get('has_video_demo'))
    live_deployments = sum(1 for p in projects if p.get('has_live_deploy'))
    docker_count = sum(1 for p in projects if p.get('has_docker'))
    test_count = sum(1 for p in projects if p.get('has_tests'))
    track_frontier = sum(1 for p in projects if 'Push the Frontier' in p.get('track', ''))
    track_world = sum(1 for p in projects if 'Build for Your World' in p.get('track', ''))

    top10 = [
        {
            "rank": p.get("rank"),
            "full_name": p.get("full_name"),
            "score_total": p.get("score_total"),
            "commits_in_window": p.get("commits_in_window"),
        }
        for p in sorted(projects, key=lambda x: x.get('rank', 9999))[:10]
    ]

    return {
        "timestamp": timestamp_iso,
        "total_repos": total_repos,
        "active_in_window": active_in_window,
        "high_velocity": high_velocity,
        "total_commits": total_commits,
        "video_demos": video_demos,
        "live_deployments": live_deployments,
        "docker_count": docker_count,
        "test_count": test_count,
        "track_frontier": track_frontier,
        "track_world": track_world,
        "top10": top10,
    }


def compact_snapshot(projects, timestamp_iso):
    return {
        "timestamp": timestamp_iso,
        "projects": {
            p["full_name"]: {
                "rank": p.get("rank"),
                "score_total": p.get("score_total"),
                "commits_in_window": p.get("commits_in_window", 0),
                "commits_before_window": p.get("commits_before_window", 0),
                "prs_merged": p.get("prs_merged", 0),
                "prs_total": p.get("prs_total", 0),
                "stars": p.get("stars", 0),
                "has_video_demo": p.get("has_video_demo", False),
                "has_live_deploy": p.get("has_live_deploy", False),
                "has_docker": p.get("has_docker", False),
                "has_tests": p.get("has_tests", False),
                "track": p.get("track", ""),
                "domain": p.get("domain", ""),
            }
            for p in projects
        },
    }


def backfill_from_git():
    """Backfills earlier git commits of projects_inventory_audited.json if snapshots dir is empty."""
    existing = sorted(f for f in os.listdir(SNAPSHOTS_DIR) if f.endswith('.json'))
    if existing:
        return

    git_commits = [
        ("18fb878", "2026-10-29T08:49:00Z", "2026-10-29T08-49-00Z.json"),
        ("7fbc522", "2026-10-29T14:52:00Z", "2026-10-29T14-52-00Z.json"),
    ]
    timeseries = []
    for sha, ts_iso, fname in git_commits:
        try:
            res = subprocess.run(
                ["git", "show", f"{sha}:{AUDITED_FILE}"],
                capture_output=True,
                text=True,
                check=True,
            )
            projs = json.loads(res.stdout)
            snap = compact_snapshot(projs, ts_iso)
            with open(os.path.join(SNAPSHOTS_DIR, fname), "w") as f:
                json.dump(snap, f, indent=2)
            timeseries.append(summarize_projects(projs, ts_iso))
            print(f"Backfilled snapshot {fname} ({len(projs)} repos) from commit {sha}")
        except Exception as e:
            print(f"Skipping backfill for {sha}: {e}")

    if timeseries:
        with open(TIMESERIES_FILE, "w") as f:
            json.dump(timeseries, f, indent=2)


def record_snapshot_and_compute_deltas():
    backfill_from_git()

    if not os.path.exists(AUDITED_FILE):
        print(f"Error: {AUDITED_FILE} not found.")
        return

    with open(AUDITED_FILE) as f:
        current_projects = json.load(f)

    # Load earliest baseline snapshot (or previous snapshot) to compute 24h / run deltas
    snap_files = sorted(f for f in os.listdir(SNAPSHOTS_DIR) if f.endswith('.json'))
    baseline_map = {}
    prev_map = {}

    if snap_files:
        with open(os.path.join(SNAPSHOTS_DIR, snap_files[0])) as f:
            baseline_map = json.load(f).get("projects", {})
        with open(os.path.join(SNAPSHOTS_DIR, snap_files[-1])) as f:
            prev_map = json.load(f).get("projects", {})

    # Enrich current_projects with deltas relative to baseline (today's start) and previous run
    for p in current_projects:
        name = p["full_name"]
        base_entry = baseline_map.get(name)
        prev_entry = prev_map.get(name)

        if base_entry is None and baseline_map:
            p["is_new"] = True
            p["commits_delta"] = p.get("commits_in_window", 0)
            p["rank_delta"] = 0
        elif base_entry is not None:
            p["is_new"] = False
            p["commits_delta"] = max(0, p.get("commits_in_window", 0) - base_entry.get("commits_in_window", 0))
            old_rank = base_entry.get("rank") or p.get("rank", 0)
            p["rank_delta"] = old_rank - p.get("rank", old_rank)
        else:
            p["is_new"] = False
            p["commits_delta"] = 0
            p["rank_delta"] = 0

        if prev_entry is not None:
            p["commits_delta_last_run"] = max(0, p.get("commits_in_window", 0) - prev_entry.get("commits_in_window", 0))
        else:
            p["commits_delta_last_run"] = p["commits_delta"]

    # Save enriched audited file
    with open(AUDITED_FILE, "w") as f:
        json.dump(current_projects, f, indent=2)

    now_dt = datetime.now(timezone.utc)
    ts_iso = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    fname = now_dt.strftime("%Y-%m-%dT%H-%M-%SZ.json")

    snap = compact_snapshot(current_projects, ts_iso)
    with open(os.path.join(SNAPSHOTS_DIR, fname), "w") as f:
        json.dump(snap, f, indent=2)

    timeseries = []
    if os.path.exists(TIMESERIES_FILE):
        try:
            with open(TIMESERIES_FILE) as f:
                timeseries = json.load(f)
        except Exception:
            timeseries = []

    # Avoid duplicate timestamps within the same 10-minute window and enforce monotonic cumulative totals
    summary = summarize_projects(current_projects, ts_iso)
    prev_summary = timeseries[-2] if (len(timeseries) >= 2 and timeseries[-1]["timestamp"][:15] == ts_iso[:15]) else (timeseries[-1] if timeseries else None)
    if prev_summary:
        for mono_key in ("total_repos", "active_in_window", "high_velocity", "total_commits", "video_demos", "live_deployments", "docker_count", "test_count"):
            summary[mono_key] = max(summary.get(mono_key, 0), prev_summary.get(mono_key, 0))
    if timeseries and timeseries[-1]["timestamp"][:15] == ts_iso[:15]:
        timeseries[-1] = summary
    else:
        timeseries.append(summary)

    with open(TIMESERIES_FILE, "w") as f:
        json.dump(timeseries, f, indent=2)

    new_count = sum(1 for p in current_projects if p.get("is_new"))
    active_delta = sum(1 for p in current_projects if p.get("commits_delta", 0) > 0)
    print(f"Recorded point-in-time snapshot {fname}: {len(current_projects)} repos ({new_count} new since baseline, {active_delta} with new commits).")


if __name__ == "__main__":
    record_snapshot_and_compute_deltas()
