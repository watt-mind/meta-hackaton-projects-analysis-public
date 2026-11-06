#!/usr/bin/env python3
"""
Meta Global AI Developer Hackathon 2026 — Video Intelligence & Transparent Rubric Auditor
Uses:
  - yt-dlp + ffmpeg + ffprobe for ingestion, 3:00 stopwatch cutoff enforcement, scene-change + grid keyframe extraction, and audio volumedetect
  - Meta SAM 3.1 (`sam-3.1`) on `POST /v1/responses` for visual UI / control / chart / presenter grounding
  - Meta Muse Spark 1.3 (`muse-spark-1.3`) on `POST /v1/responses` + `POST /v1/files` for multimodal video + audio evidence extraction
  - Deterministic Python rubric calculator (`compute_transparent_video_score`) for 100% transparent, itemized scoring
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

AUDITED_INVENTORY_FILE = "projects_inventory_audited.json"
VIDEO_CACHE_DIR = "video_cache"
VIDEO_AUDIT_OUTPUT = "video_audit_results.json"
BENCHMARK_OUTPUT = "video_benchmark_comparison.json"
COST_REPORT_OUTPUT = "video_cost_report_top20.json"

META_BASE_URL = "https://api.meta.ai/v1"

# Official Meta Model API Pricing (https://dev.meta.ai/docs/pricing-rate-limits)
PRICING = {
    "muse_spark_standard": {"input_per_1m": 1.25, "cached_per_1m": 0.15, "output_per_1m": 4.25},
    "muse_spark_contributor": {"input_per_1m": 0.10, "cached_per_1m": 0.002, "output_per_1m": 0.20},
    "sam_3_1_per_image": 0.0025,  # $2.50 per 1,000 images
    "sam_3_1_per_video_frame": 0.0002,  # $0.20 per 1,000 frames
}


def compute_api_cost(usage: dict, sam_image_calls: int = 16) -> dict:
    in_tok = int(usage.get("input_tokens", 0))
    cached_tok = int((usage.get("input_tokens_details") or {}).get("cached_tokens", 0))
    uncached_in = max(0, in_tok - cached_tok)
    out_tok = int(usage.get("output_tokens", 0))
    reas_tok = int((usage.get("output_tokens_details") or {}).get("reasoning_tokens", 0))

    std = PRICING["muse_spark_standard"]
    con = PRICING["muse_spark_contributor"]

    spark_std_usd = (uncached_in * std["input_per_1m"] + cached_tok * std["cached_per_1m"] + out_tok * std["output_per_1m"]) / 1_000_000
    spark_con_usd = (uncached_in * con["input_per_1m"] + cached_tok * con["cached_per_1m"] + out_tok * con["output_per_1m"]) / 1_000_000
    sam_usd = sam_image_calls * PRICING["sam_3_1_per_image"]

    return {
        "input_tokens": in_tok,
        "cached_tokens": cached_tok,
        "output_tokens": out_tok,
        "reasoning_tokens": reas_tok,
        "total_tokens": in_tok + out_tok,
        "sam_3_1_image_calls": sam_image_calls,
        "spark_cost_usd_contributor": round(spark_con_usd, 5),
        "spark_cost_usd_standard": round(spark_std_usd, 5),
        "sam_3_1_cost_usd": round(sam_usd, 5),
        "total_cost_usd_contributor": round(spark_con_usd + sam_usd, 5),
        "total_cost_usd_standard": round(spark_std_usd + sam_usd, 5),
    }


def load_meta_api_key():
    for env_var in ("META_API_KEY", "MODEL_API_KEY"):
        val = os.environ.get(env_var)
        if val:
            return val.strip()
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("META_API_KEY=") or line.startswith("MODEL_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def slugify_repo(full_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "__", full_name)


def normalize_video_identity(url: str) -> str:
    """Normalize video URL to a canonical identity so URL updates (e.g. new YouTube upload) invalidate stale cache."""
    if not url:
        return ""
    u = url.strip().rstrip("/")
    m_yt = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|embed/))([A-Za-z0-9_-]{6,})", u)
    if m_yt:
        return f"yt:{m_yt.group(1)}"
    m_vm = re.search(r"vimeo\.com/(?:video/)?(\d+)", u)
    if m_vm:
        return f"vimeo:{m_vm.group(1)}"
    m_lm = re.search(r"loom\.com/share/([A-Za-z0-9]+)", u)
    if m_lm:
        return f"loom:{m_lm.group(1)}"
    return u.lower()


def pick_best_video_url(full_name: str, urls: list[str]) -> tuple[str, list[str]]:
    """Select the primary downloadable video URL and fallback candidates."""
    notes = []
    if not urls:
        return "", notes

    if full_name.startswith("ta-amps/"):
        raw_mp4 = "https://raw.githubusercontent.com/ta-amps/agora-public-overview-architecture-setup-and-contribution/main/site/video/2026-10-31/full-v6/eranos-3m.mp4"
        notes.append("Primary worker .mp4 URL (agora.ta-amps.workers.dev/.../eranos-3m.mp4) returned HTTP 404; resolved from GitHub raw site/video/2026-10-31/full-v6/eranos-3m.mp4")
        return raw_mp4, notes

    for u in urls:
        m_vimeo = re.search(r"vimeo\.com/(\d+)", u)
        if m_vimeo and "player.vimeo.com" not in u:
            return f"https://player.vimeo.com/video/{m_vimeo.group(1)}", notes
        if any(k in u.lower() for k in ("youtu.be/", "youtube.com/watch", "vimeo.com/", "loom.com/share/")):
            return u, notes
    for u in urls:
        if u.lower().endswith((".mp4", ".webm", ".mov")):
            return u, notes
    return urls[0], notes


def assemble_html_film_fallback(full_name: str, film_url: str, target_mp4: str) -> tuple[bool, str]:
    """If a project only provides an interactive HTML /film/ page (e.g. ohistudio/fursight), assemble its embedded .mp4 clips."""
    try:
        r = requests.get(film_url, timeout=15)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code} fetching {film_url}"
        clip_names = list(dict.fromkeys(re.findall(r'([A-Za-z0-9_.-]+\.mp4)', r.text)))
        if not clip_names:
            return False, "No embedded .mp4 clips found in HTML /film/ page"

        base_url = film_url.rstrip("/") + "/clips/"
        work_dir = os.path.join(VIDEO_CACHE_DIR, slugify_repo(full_name) + "_clips")
        os.makedirs(work_dir, exist_ok=True)
        downloaded_clips = []
        for idx, cname in enumerate(clip_names[:10]):
            c_url = base_url + cname
            c_path = os.path.join(work_dir, f"part_{idx:02d}.mp4")
            if not os.path.exists(c_path) or os.path.getsize(c_path) < 1000:
                cr = requests.get(c_url, timeout=20)
                if cr.status_code == 200 and len(cr.content) > 1000:
                    with open(c_path, "wb") as f:
                        f.write(cr.content)
            if os.path.exists(c_path) and os.path.getsize(c_path) > 1000:
                norm_path = os.path.join(work_dir, f"norm_{idx:02d}.mp4")
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", c_path,
                        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1",
                        "-r", "24", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                        "-an", norm_path,
                    ],
                    capture_output=True,
                )
                if os.path.exists(norm_path):
                    downloaded_clips.append(norm_path)

        if not downloaded_clips:
            return False, "Could not download embedded clips from /film/ page"

        concat_txt = os.path.join(work_dir, "concat.txt")
        with open(concat_txt, "w") as f:
            for p in downloaded_clips:
                f.write(f"file '{os.path.abspath(p)}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", target_mp4],
            capture_output=True,
        )
        return os.path.exists(target_mp4) and os.path.getsize(target_mp4) > 1000, f"Assembled {len(downloaded_clips)} sub-clips from interactive HTML /film/ page"
    except Exception as e:
        return False, str(e)


def download_video(full_name: str, urls: list[str], force_refresh: bool = False) -> dict:
    """Download video into video_cache/ and inspect metadata with ffprobe + volumedetect."""
    import shutil
    os.makedirs(VIDEO_CACHE_DIR, exist_ok=True)
    slug = slugify_repo(full_name)
    target_mp4 = os.path.join(VIDEO_CACHE_DIR, f"{slug}.mp4")
    url_sidecar = os.path.join(VIDEO_CACHE_DIR, f"{slug}.url")
    slice_dir = os.path.join(VIDEO_CACHE_DIR, slug)
    primary_url, url_notes = pick_best_video_url(full_name, urls)
    norm_primary = normalize_video_identity(primary_url)

    cached_norm = ""
    if os.path.exists(url_sidecar):
        try:
            with open(url_sidecar) as uf:
                cached_norm = uf.read().strip()
        except Exception:
            cached_norm = ""

    if force_refresh or (cached_norm and norm_primary and cached_norm != norm_primary):
        if os.path.exists(target_mp4):
            os.remove(target_mp4)
        if os.path.exists(slice_dir):
            shutil.rmtree(slice_dir, ignore_errors=True)

    if not os.path.exists(target_mp4) or os.path.getsize(target_mp4) < 5000:
        if os.path.exists(slice_dir):
            shutil.rmtree(slice_dir, ignore_errors=True)
        if primary_url.endswith("/film/") or primary_url.endswith("/film"):
            ok, msg = assemble_html_film_fallback(full_name, primary_url, target_mp4)
            if msg:
                url_notes.append(msg)
        else:
            cmd = [
                "yt-dlp",
                "--no-playlist",
                "--referer", "https://vimeo.com/",
                "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "--merge-output-format", "mp4",
                "-o", target_mp4,
                primary_url,
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if res.returncode != 0 or not os.path.exists(target_mp4):
                for alt_u in urls:
                    if alt_u == primary_url:
                        continue
                    if alt_u.endswith("/film/") or alt_u.endswith("/film"):
                        ok, msg = assemble_html_film_fallback(full_name, alt_u, target_mp4)
                        if ok:
                            primary_url = alt_u
                            url_notes.append(msg)
                            break
                    else:
                        res2 = subprocess.run(
                            [
                                "yt-dlp", "--no-playlist",
                                "--referer", "https://vimeo.com/",
                                "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                                "--merge-output-format", "mp4",
                                "-o", target_mp4, alt_u,
                            ],
                            capture_output=True, text=True, timeout=180,
                        )
                        if res2.returncode == 0 and os.path.exists(target_mp4):
                            primary_url = alt_u
                            break

    if not os.path.exists(target_mp4) or os.path.getsize(target_mp4) < 5000:
        return {
            "ok": False,
            "primary_url": primary_url,
            "error": "Video download failed or URL unreachable",
            "notes": url_notes,
        }

    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size:stream=codec_type,width,height",
        "-of", "json", target_mp4,
    ]
    pr = subprocess.run(probe_cmd, capture_output=True, text=True)
    probe_data = json.loads(pr.stdout) if pr.returncode == 0 and pr.stdout else {}
    fmt = probe_data.get("format", {})
    streams = probe_data.get("streams", [])
    duration_s = round(float(fmt.get("duration", 0.0)), 2)
    size_bytes = int(fmt.get("size", os.path.getsize(target_mp4)))
    has_audio_stream = any(s.get("codec_type") == "audio" for s in streams)
    width = next((s.get("width") for s in streams if s.get("codec_type") == "video"), 0)
    height = next((s.get("height") for s in streams if s.get("codec_type") == "video"), 0)

    mean_volume_db = -91.0
    if has_audio_stream:
        vd = subprocess.run(
            ["ffmpeg", "-i", target_mp4, "-to", "00:03:00", "-vn", "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True,
        )
        m_vol = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", vd.stderr)
        if m_vol:
            mean_volume_db = float(m_vol.group(1))

    try:
        with open(url_sidecar, "w") as uf:
            uf.write(normalize_video_identity(primary_url))
    except Exception:
        pass

    return {
        "ok": True,
        "local_path": target_mp4,
        "primary_url": primary_url,
        "duration_s": duration_s,
        "within_3m_limit": duration_s <= 185.0,
        "overrun_seconds": round(max(0.0, duration_s - 180.0), 2),
        "size_mb": round(size_bytes / (1024 * 1024), 2),
        "width": width,
        "height": height,
        "has_audio_stream": has_audio_stream,
        "mean_volume_db": mean_volume_db,
        "has_audible_track": has_audio_stream and mean_volume_db > -55.0,
        "notes": url_notes,
    }


def detect_scene_timestamps(video_path: str, capped_dur: float, target_count: int = 20) -> list[float]:
    """
    Combine ffmpeg scene-change detection (`select='gt(scene,0.18)',showinfo`) with a guaranteed
    uniform timeline grid (dense in 0-20s for provenance and 135-180s for benchmarks) to yield
    exactly `target_count` (20) well-spaced keyframe timestamps across [1.5s .. capped_dur - 1.5s].
    """
    scene_ts = []
    try:
        res = subprocess.run(
            [
                "ffmpeg", "-i", video_path, "-to", str(capped_dur),
                "-vf", "select='gt(scene,0.18)',showinfo",
                "-f", "null", "-",
            ],
            capture_output=True, text=True, timeout=45,
        )
        for m in re.finditer(r"pts_time:([\d.]+)", res.stderr):
            t = round(float(m.group(1)), 1)
            if 1.5 <= t <= capped_dur - 1.0:
                scene_ts.append(t)
    except Exception:
        pass

    # Mandatory anchor timestamps (opening 0-20s provenance + uniform intervals + closing benchmarks)
    anchors = [2.0, 6.5, 11.5, 16.5, 22.0]
    step = max(3.5, (capped_dur - 22.0) / max(1, target_count - len(anchors)))
    for i in range(1, target_count - len(anchors) + 1):
        t = round(min(capped_dur - 1.2, 19.0 + i * step), 1)
        anchors.append(t)

    # Merge scene changes first (shifted +0.8s after cut so transition settles), then fill from anchors
    selected = []
    min_gap = max(2.5, capped_dur / (target_count * 1.6))

    # Always include 4 opening provenance frames (2.0s, 6.5s, 11.5s, 16.5s) for opening provenance check
    for opening_t in [2.0, 6.5, 11.5, 16.5]:
        if opening_t < capped_dur - 1.0:
            selected.append(opening_t)

    for st in scene_ts:
        settled = round(min(capped_dur - 1.0, st + 0.6), 1)
        if all(abs(settled - x) >= min_gap for x in selected):
            selected.append(settled)
        if len(selected) >= target_count:
            break

    # Fill remaining slots from uniform anchors
    for a in anchors:
        if len(selected) >= target_count:
            break
        if all(abs(a - x) >= min_gap * 0.75 for x in selected):
            selected.append(a)

    # If still under target_count, fill largest gaps
    selected.sort()
    while len(selected) < target_count and len(selected) >= 2:
        max_gap = 0.0
        best_mid = None
        for i in range(len(selected) - 1):
            g = selected[i + 1] - selected[i]
            if g > max_gap:
                max_gap = g
                best_mid = round((selected[i] + selected[i + 1]) / 2.0, 1)
        if best_mid is None or max_gap < 1.0:
            break
        selected.append(best_mid)
        selected.sort()

    return sorted(selected[:target_count])


def prepare_media_slices(full_name: str, video_path: str, duration_s: float, num_keyframes: int = 20) -> dict:
    """
    Create both:
      1. 4 Spliced video beat clips (capped at 180s stopwatch cutoff) for Method A.
      2. 20 Hybrid Scene + Grid Keyframes + 3:00 MP3 audio track for Upgraded Method B & SAM 3.1 grounding.
    """
    slug = slugify_repo(full_name)
    work_dir = os.path.join(VIDEO_CACHE_DIR, slug)
    os.makedirs(work_dir, exist_ok=True)

    capped_dur = min(duration_s, 180.0)
    beat_windows = [
        ("beat1_hook_0_20", 0, min(20, capped_dur), "0:00-0:20 (Opening Hook & Provenance)"),
        ("beat2_demo_20_80", 20, min(80, capped_dur), "0:20-1:20 (Core Live Product Demo)"),
        ("beat3_meta_80_135", 80, min(135, capped_dur), "1:20-2:15 (Meta AI Tooling & Orchestration)"),
        ("beat4_eval_135_180", 135, capped_dur, "2:15-3:00 (Benchmarks & Closing before 3:00 cutoff)"),
    ]

    spliced_clips = []
    for name, start_s, end_s, label in beat_windows:
        if end_s <= start_s + 1:
            continue
        clip_len = round(end_s - start_s, 2)
        out_clip = os.path.join(work_dir, f"{name}.mp4")
        if not os.path.exists(out_clip) or os.path.getsize(out_clip) < 1000:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", str(start_s),
                    "-t", str(clip_len),
                    "-i", video_path,
                    "-vf", "scale=-2:480",
                    "-r", "8",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
                    "-c:a", "aac", "-b:a", "48k",
                    out_clip,
                ],
                capture_output=True,
            )
        if os.path.exists(out_clip) and os.path.getsize(out_clip) > 1000:
            spliced_clips.append({
                "name": name,
                "label": label,
                "start_s": start_s,
                "end_s": end_s,
                "path": out_clip,
                "bytes": os.path.getsize(out_clip),
            })

    # Extract 20 hybrid scene + grid keyframes
    ts_list = detect_scene_timestamps(video_path, capped_dur, target_count=num_keyframes)
    keyframes = []
    for idx, ts in enumerate(ts_list):
        f_path = os.path.join(work_dir, f"kf20_{idx:02d}_{int(ts*10):04d}ds.jpg")
        if not os.path.exists(f_path) or os.path.getsize(f_path) < 500:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", str(ts),
                    "-i", video_path,
                    "-vf", "scale=-2:540",
                    "-frames:v", "1",
                    "-q:v", "4",
                    f_path,
                ],
                capture_output=True,
            )
        if os.path.exists(f_path) and os.path.getsize(f_path) > 500:
            keyframes.append({"index": idx, "timestamp_s": ts, "path": f_path, "bytes": os.path.getsize(f_path)})

    # Extract 3:00 MP3 audio track
    audio_mp3 = os.path.join(work_dir, "audio_capped_180s.mp3")
    if not os.path.exists(audio_mp3) or os.path.getsize(audio_mp3) < 500:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", video_path,
                "-to", "00:03:00",
                "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k",
                audio_mp3,
            ],
            capture_output=True,
        )

    return {
        "work_dir": work_dir,
        "spliced_clips": spliced_clips,
        "keyframes": keyframes,
        "audio_mp3": audio_mp3 if (os.path.exists(audio_mp3) and os.path.getsize(audio_mp3) > 500) else None,
    }


def parse_sam_boxes(text: str) -> list[dict]:
    """Parse `<|box;x1=...;y1=...;x2=...;y2=...;w=...;h=|>` tokens from SAM 3.1 output."""
    boxes = []
    for m in re.finditer(r"<\|box;x1=(\d+);y1=(\d+);x2=(\d+);y2=(\d+);w=(\d+);h=(\d+)\|>", text or ""):
        x1, y1, x2, y2, w, h = map(int, m.groups())
        area_ratio = ((x2 - x1) * (y2 - y1)) / max(1, w * h)
        boxes.append({
            "x1": x1, "y1": y1, "x2": x2, "y2": y2, "w": w, "h": h,
            "area_ratio": round(max(0.0, min(1.0, area_ratio)), 4),
        })
    return boxes


def run_sam31_grounding(keyframes: list[dict], api_key: str) -> dict:
    """
    Run Meta's SAM 3.1 (`sam-3.1`) on 4 representative keyframes across the video
    to ground concrete UI surfaces:
      - "button" (interactive UI buttons/controls)
      - "browser window" (live web/desktop windows)
      - "chart" (benchmarks / evaluation plots / tables)
      - "person" (human presenter on camera / webcam PiP)
    """
    t0 = time.time()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    step = max(1, len(keyframes) // 4)
    sampled = [keyframes[i] for i in range(min(2, len(keyframes) - 1), len(keyframes), step)][:4]
    prompts = ["button", "browser window", "chart", "person"]

    tasks = []
    for kf in sampled:
        with open(kf["path"], "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        for noun in prompts:
            tasks.append((kf["timestamp_s"], noun, b64))

    detections = {p: [] for p in prompts}
    total_boxes = 0

    def call_one(ts, noun, b64_img):
        resp = requests.post(
            f"{META_BASE_URL}/responses",
            headers=headers,
            json={
                "model": "sam-3.1",
                "input": [{
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": noun},
                        {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64_img}"},
                    ],
                }],
                "stream": False,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return ts, noun, []
        data = resp.json()
        out_txt = ""
        for item in data.get("output", []):
            for c in item.get("content", []):
                if c.get("text"):
                    out_txt += c["text"]
        return ts, noun, parse_sam_boxes(out_txt)

    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = [pool.submit(call_one, ts, noun, b64) for ts, noun, b64 in tasks]
        for fut in as_completed(futs):
            try:
                ts, noun, boxes = fut.result()
                if boxes:
                    total_boxes += len(boxes)
                    max_area = max(b["area_ratio"] for b in boxes)
                    detections[noun].append({"timestamp_s": ts, "count": len(boxes), "max_area_ratio": max_area})
            except Exception:
                pass

    n_frames = max(1, len(sampled))
    ui_frames = len({d["timestamp_s"] for d in detections["button"] + detections["browser window"]})
    return {
        "model": "sam-3.1",
        "frames_sampled": len(sampled),
        "latency_s": round(time.time() - t0, 2),
        "total_boxes_detected": total_boxes,
        "interactive_ui_frame_ratio": round(ui_frames / n_frames, 2),
        "button_control_count": sum(d["count"] for d in detections["button"]),
        "browser_ui_frame_ratio": round(len(detections["browser window"]) / n_frames, 2),
        "chart_benchmark_frame_ratio": round(len(detections["chart"]) / n_frames, 2),
        "human_presenter_frame_ratio": round(len(detections["person"]) / n_frames, 2),
        "detections_by_concept": detections,
    }


def compute_transparent_video_score(video_meta: dict, sam_grounding: dict, llm_facts: dict) -> dict:
    """
    Deterministic, 100% transparent 6-criterion video rubric calculator (max 2.50 pts).
    Every point awarded or withheld is logged in `breakdown` with verifiable evidence.
    """
    if not video_meta.get("ok"):
        return {
            "total_score": 0.0,
            "c1_stopwatch_compliance": 0.0,
            "c2_opening_provenance": 0.0,
            "c3_live_product_authenticity": 0.0,
            "c4_meta_model_execution": 0.0,
            "c5_quantifiable_benchmarks": 0.0,
            "c6_audio_and_caption_clarity": 0.0,
            "breakdown": [["Unplayable or unreachable video URL", "+0.00 / 2.50"]],
        }

    breakdown = []

    # 1. Playable Video & 3:00 Stopwatch Compliance (max 0.30)
    dur = float(video_meta.get("duration_s", 0.0))
    notes = video_meta.get("notes") or []
    has_404_primary = any("404" in n for n in notes)
    if has_404_primary:
        c1 = 0.15
        breakdown.append([f"Primary video link HTTP 404 (resolved from repo raw fallback, {dur:.1f}s)", "+0.15 / 0.30"])
    elif 30.0 <= dur <= 185.0:
        c1 = 0.30
        breakdown.append([f"Playable video within 3:00 stopwatch limit ({dur:.1f}s)", "+0.30 / 0.30"])
    elif dur > 185.0:
        c1 = 0.15
        breakdown.append([f"Exceeds 3:00 stopwatch cutoff ({dur:.1f}s; +{dur-180:.1f}s truncated by judges)", "+0.15 / 0.30"])
    else:
        c1 = 0.15
        breakdown.append([f"Short clip / interactive web page assembly ({dur:.1f}s)", "+0.15 / 0.30"])

    # 2. Mandatory Opening 1-Line Provenance Statement (max 0.30)
    prov_status = llm_facts.get("provenance_timing") or ("opening_20s" if llm_facts.get("provenance_stated_in_opening") else "missing")
    if prov_status == "opening_20s" or llm_facts.get("provenance_stated_in_opening"):
        c2 = 0.30
        ev_q = (llm_facts.get("provenance_evidence") or "Stated in 0:00-0:20")[:90]
        breakdown.append([f"Opening provenance stated in first 20s ({ev_q})", "+0.30 / 0.30"])
    elif prov_status == "later_in_video":
        c2 = 0.15
        ev_q = (llm_facts.get("provenance_evidence") or "Stated after 0:20")[:90]
        breakdown.append([f"Provenance stated after 0:20 opening window ({ev_q})", "+0.15 / 0.30"])
    else:
        c2 = 0.00
        breakdown.append(["Missing mandatory opening 1-line hackathon provenance statement", "+0.00 / 0.30"])

    # 3. Real Working Product Footage vs. Slideware (max 0.80)
    pct = int(llm_facts.get("product_footage_pct_estimate", 0))
    sam_boxes = int(sam_grounding.get("total_boxes_detected", 0))
    is_real = bool(llm_facts.get("is_real_working_product_demo", False))
    if is_real and pct >= 75:
        c3 = 0.80
        breakdown.append([f"Real working product demo ({pct}% live UI/CLI footage, {sam_boxes} SAM 3.1 UI boxes)", "+0.80 / 0.80"])
    elif is_real and pct >= 50:
        c3 = 0.55
        breakdown.append([f"Mixed live demo & slides ({pct}% live UI/CLI footage, {sam_boxes} SAM 3.1 UI boxes)", "+0.55 / 0.80"])
    elif pct >= 20:
        c3 = 0.25
        breakdown.append([f"Slide-heavy presentation ({pct}% live product footage, {sam_boxes} SAM 3.1 UI boxes)", "+0.25 / 0.80"])
    else:
        c3 = 0.00
        breakdown.append([f"Static slideware / no live working UI shown ({pct}% live footage, {sam_boxes} SAM 3.1 boxes)", "+0.00 / 0.80"])

    # 4. Visible Live Meta Model Execution & Multi-Model Orchestration (max 0.50)
    models = llm_facts.get("visible_meta_models_in_video") or []
    live_calls = bool(llm_facts.get("live_meta_calls_shown", False))
    c4 = 0.0
    if live_calls:
        c4 += 0.25
    if len(models) >= 1:
        c4 += 0.15
    if len(models) >= 2:
        c4 += 0.10
    c4 = round(c4, 2)
    models_str = ", ".join(models[:4]) if models else "none"
    breakdown.append([
        f"Meta AI model visibility (live_calls={live_calls}, {len(models)} models: {models_str})",
        f"+{c4:.2f} / 0.50",
    ])

    # 5. Quantifiable Benchmarks & Verification Before 3:00 (max 0.35)
    metrics = llm_facts.get("extracted_benchmark_metrics") or []
    has_bench = bool(llm_facts.get("benchmarks_shown_before_3m", False)) and len(metrics) > 0
    if has_bench and len(metrics) >= 2:
        c5 = 0.35
        breakdown.append([f"Quantifiable benchmarks shown before 3:00 ({len(metrics)} metrics extracted)", "+0.35 / 0.35"])
    elif has_bench or len(metrics) == 1:
        c5 = 0.20
        breakdown.append([f"Partial benchmark/verification metric shown ({len(metrics)} metric)", "+0.20 / 0.35"])
    else:
        c5 = 0.00
        breakdown.append(["No quantitative benchmarks shown on screen before 3:00", "+0.00 / 0.35"])

    # 6. Audio Walkthrough & Caption Clarity (max 0.25)
    audible = bool(video_meta.get("has_audible_track", False))
    vol_db = float(video_meta.get("mean_volume_db", -91.0))
    narr = llm_facts.get("narration_type", "silent")
    has_caps = bool(llm_facts.get("has_burned_in_captions", True))
    if audible and narr in ("human_voice", "ai_voiceover") and has_caps:
        c6 = 0.25
        breakdown.append([f"Clear English voiceover ({narr}, {vol_db:.1f} dB) + on-screen captions/labels", "+0.25 / 0.25"])
    elif (audible and narr in ("human_voice", "ai_voiceover")) or (has_caps and narr == "captions_and_music"):
        c6 = 0.15
        breakdown.append([f"Understandable walkthrough ({narr}, {vol_db:.1f} dB, captions={has_caps})", "+0.15 / 0.25"])
    else:
        c6 = 0.05
        breakdown.append([f"Silent or low-clarity audio track ({narr}, {vol_db:.1f} dB)", "+0.05 / 0.25"])

    total = round(c1 + c2 + c3 + c4 + c5 + c6, 2)
    return {
        "total_score": total,
        "c1_stopwatch_compliance": round(c1, 2),
        "c2_opening_provenance": round(c2, 2),
        "c3_live_product_authenticity": round(c3, 2),
        "c4_meta_model_execution": round(c4, 2),
        "c5_quantifiable_benchmarks": round(c5, 2),
        "c6_audio_and_caption_clarity": round(c6, 2),
        "breakdown": breakdown,
    }


RUBRIC_PROMPT_TEMPLATE = """You are an official Stage 1 & Stage 2 Judge for the Meta Global AI Developer Hackathon 2026 evaluating the 3-minute demo video for repository `{full_name}` (Track: `{track}`).
Repository README summary for context: {readme_summary}

Official Judging Rules from Organizers (Cerebral Valley & Meta):
1. Hard 3:00 Stopwatch Cutoff: Judges stop watching at 3:00.
2. Mandatory Opening 1-Line Provenance: Within the first 10-20 seconds, the video must state what existed before the hackathon vs. what was built during the Oct 26 - Nov 4 hackathon window.
3. Real Product Execution vs. Slideware: At least 75-80% of the runtime should be real working product footage (UI, CLI, live traces, hardware, benchmarks), not static slide decks or raw IDE code scrolling.
4. Visible Live Meta Model Calls: Must show and explain where and how Meta models (`Muse Spark 1.3`, `Muse Spark Open`, `Muse Glimmer`, `Muse Wonder`, `Muse Image`, `Muse Voice Transcribe`, `SAM 3.1`, `Llama`, etc.) are used at runtime.
5. Quantifiable Benchmarks: Concrete numbers (latency, accuracy/F1, pass rate, test suite, etc.) shown on screen before 3:00.

Analyze the provided video media carefully (both visual frames/screen content and spoken narration/on-screen captions) and return ONLY a valid JSON object (no markdown fences) with these exact keys:
{{
  "provenance_stated_in_opening": boolean,
  "provenance_timing": "opening_20s" | "later_in_video" | "missing",
  "provenance_evidence": "verbatim quote or on-screen text stating hackathon provenance (with timestamp), or 'None shown'",
  "is_real_working_product_demo": boolean,
  "product_footage_pct_estimate": integer (0 to 100, percentage of video showing real working UI/CLI/hardware/traces vs static slides),
  "live_ui_surfaces_seen": ["list concrete live surfaces seen, e.g. 'Web dashboard at guard.watt-mind.com', 'Terminal CLI test runner', 'MuJoCo physics simulator'"],
  "narration_type": "human_voice" | "ai_voiceover" | "captions_and_music" | "silent",
  "has_burned_in_captions": boolean,
  "visible_meta_models_in_video": ["list of Meta models explicitly shown or named in the video"],
  "live_meta_calls_shown": boolean,
  "meta_call_evidence": "1 sentence describing where/how live Meta model execution or telemetry is shown on screen",
  "benchmarks_shown_before_3m": boolean,
  "extracted_benchmark_metrics": ["up to 5 concrete metrics/numbers shown on screen or spoken, e.g. '98.4% recall', '43ms NER latency'"],
  "bonus_prize_flags": ["subset of: 'Best Build on Meta Open Weight Models', 'Best Agentic Use-Case', 'Best Creative Build' warranted by video evidence"],
  "beat_by_beat_summary": {{
    "0_00_to_0_20_hook": "1-sentence summary of what is shown and said in 0:00-0:20",
    "0_20_to_1_20_core_demo": "1-sentence summary of 0:20-1:20",
    "1_20_to_2_15_meta_architecture": "1-sentence summary of 1:20-2:15",
    "2_15_to_3_00_benchmarks_closing": "1-sentence summary of 2:15-3:00"
  }},
  "judge_strengths": "1 concise sentence on what the video does best",
  "judge_weaknesses_or_risks": "1 concise sentence on any missing rules (e.g. missing opening provenance, >3:00 cutoff risk, silent audio, slide-heavy)"
}}"""


def extract_json_object(text: str) -> dict:
    text = (text or "").strip()
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        return json.loads(m.group(0))
    return json.loads(text)


def upload_file_to_meta(file_path: str, mime_type: str, api_key: str) -> str:
    headers = {"Authorization": f"Bearer {api_key}"}
    with open(file_path, "rb") as f:
        r = requests.post(
            f"{META_BASE_URL}/files",
            headers=headers,
            files={"file": (os.path.basename(file_path), f, mime_type)},
            data={"purpose": "user_data"},
            timeout=90,
        )
    r.raise_for_status()
    return r.json()["id"]


def evaluate_method_a_spliced_video(project: dict, slices: dict, video_meta: dict, sam_res: dict, api_key: str) -> dict:
    """
    Method A: Upload the 4 spliced .mp4 beat clips to `/v1/files` and evaluate with `muse-spark-1.3`.
    """
    t0 = time.time()
    t_up0 = time.time()
    uploaded_clips = []
    total_upload_bytes = 0

    for clip in slices["spliced_clips"]:
        fid = upload_file_to_meta(clip["path"], "video/mp4", api_key)
        uploaded_clips.append((clip, fid))
        total_upload_bytes += clip["bytes"]
    upload_latency_s = round(time.time() - t_up0, 2)

    content_blocks = []
    for clip, fid in uploaded_clips:
        content_blocks.append({"type": "input_text", "text": f"=== Video Segment: {clip['label']} ==="})
        content_blocks.append({"type": "input_file", "file_id": fid})

    prompt = RUBRIC_PROMPT_TEMPLATE.format(
        full_name=project["full_name"],
        track=project.get("track", ""),
        readme_summary=(project.get("readme_summary") or project.get("summary") or "")[:300],
    )
    content_blocks.append({"type": "input_text", "text": prompt})

    t_inf0 = time.time()
    resp = requests.post(
        f"{META_BASE_URL}/responses",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "muse-spark-1.3",
            "reasoning": {"effort": "low"},
            "input": [{"type": "message", "role": "user", "content": content_blocks}],
            "stream": False,
        },
        timeout=150,
    )
    resp.raise_for_status()
    inf_latency_s = round(time.time() - t_inf0, 2)
    data = resp.json()

    raw_text = ""
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("text"):
                    raw_text += c["text"]

    parsed = extract_json_object(raw_text)
    transparent_score = compute_transparent_video_score(video_meta, sam_res, parsed)
    parsed["transparent_rubric"] = transparent_score
    usage = data.get("usage", {})
    return {
        "method": "Method A: Spliced .mp4 Video Upload (4 beats -> /v1/files -> muse-spark-1.3)",
        "upload_bytes": total_upload_bytes,
        "upload_latency_s": upload_latency_s,
        "inference_latency_s": inf_latency_s,
        "total_latency_s": round(time.time() - t0, 2),
        "usage": usage,
        "audit": parsed,
    }


def evaluate_method_b_keyframes_plus_audio(project: dict, slices: dict, video_meta: dict, sam_res: dict, api_key: str) -> dict:
    """
    Upgraded Method B: Send 20 hybrid scene-change + interval keyframes (inline base64 JPEG)
    + uploaded 3:00 MP3 audio track to `muse-spark-1.3`.
    """
    t0 = time.time()
    t_up0 = time.time()
    content_blocks = []
    total_payload_bytes = 0

    if video_meta.get("has_audible_track") and slices.get("audio_mp3"):
        audio_fid = upload_file_to_meta(slices["audio_mp3"], "audio/mpeg", api_key)
        total_payload_bytes += os.path.getsize(slices["audio_mp3"])
        content_blocks.append({"type": "input_text", "text": "=== Full 3:00 Audio Track (Listen for narration & provenance) ==="})
        content_blocks.append({"type": "input_file", "file_id": audio_fid})
    upload_latency_s = round(time.time() - t_up0, 2)

    for kf in slices["keyframes"]:
        with open(kf["path"], "rb") as f:
            raw_b = f.read()
        total_payload_bytes += len(raw_b)
        b64 = base64.b64encode(raw_b).decode()
        content_blocks.append({"type": "input_text", "text": f"Keyframe #{kf['index']+1} at t={kf['timestamp_s']}s:"})
        content_blocks.append({"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"})

    prompt = RUBRIC_PROMPT_TEMPLATE.format(
        full_name=project["full_name"],
        track=project.get("track", ""),
        readme_summary=(project.get("readme_summary") or project.get("summary") or "")[:300],
    )
    content_blocks.append({"type": "input_text", "text": prompt})

    t_inf0 = time.time()
    model_used = "muse-spark-1.3-contributor"
    resp = requests.post(
        f"{META_BASE_URL}/responses",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model_used,
            "reasoning": {"effort": "low"},
            "input": [{"type": "message", "role": "user", "content": content_blocks}],
            "stream": False,
        },
        timeout=150,
    )
    if resp.status_code != 200:
        model_used = "muse-spark-1.3"
        resp = requests.post(
            f"{META_BASE_URL}/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model_used,
                "reasoning": {"effort": "low"},
                "input": [{"type": "message", "role": "user", "content": content_blocks}],
                "stream": False,
            },
            timeout=150,
        )
    resp.raise_for_status()
    inf_latency_s = round(time.time() - t_inf0, 2)
    data = resp.json()

    raw_text = ""
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("text"):
                    raw_text += c["text"]

    parsed = extract_json_object(raw_text)
    transparent_score = compute_transparent_video_score(video_meta, sam_res, parsed)
    parsed["transparent_rubric"] = transparent_score
    usage = data.get("usage", {})
    return {
        "method": f"Method B (Upgraded): {len(slices['keyframes'])} Scene+Grid Keyframes + 3:00 MP3 Audio -> {model_used}",
        "model_used": model_used,
        "upload_bytes": total_payload_bytes,
        "upload_latency_s": upload_latency_s,
        "inference_latency_s": inf_latency_s,
        "total_latency_s": round(time.time() - t0, 2),
        "usage": usage,
        "audit": parsed,
    }


def run_benchmark(projects: list[dict], api_key: str, count: int = 4):
    print(f"=== BENCHMARKING METHOD A (SPLICED VIDEO) vs UPGRADED METHOD B (20 KEYFRAMES + AUDIO) + SAM 3.1 ON TOP {count} VIDEOS ===")
    results = []
    for p in projects[:count]:
        fn = p["full_name"]
        print(f"\n-> [{p['rank']}] {fn} ({p.get('video_urls')})")
        dl = download_video(fn, p.get("video_urls", []))
        if not dl.get("ok"):
            print(f"   Download failed: {dl.get('error')}")
            continue
        print(f"   Downloaded: {dl['duration_s']}s ({dl['size_mb']} MB), audible={dl['has_audible_track']} ({dl['mean_volume_db']} dB)")
        slices = prepare_media_slices(fn, dl["local_path"], dl["duration_s"], num_keyframes=20)
        print(f"   Prepared {len(slices['spliced_clips'])} spliced clips and {len(slices['keyframes'])} hybrid scene+grid keyframes: {[k['timestamp_s'] for k in slices['keyframes']]}")

        sam_res = run_sam31_grounding(slices["keyframes"], api_key)
        print(f"   SAM 3.1 Grounding: {sam_res['total_boxes_detected']} boxes in {sam_res['latency_s']}s "
              f"(InteractiveUI={sam_res['interactive_ui_frame_ratio']}, Buttons={sam_res['button_control_count']}, "
              f"Chart={sam_res['chart_benchmark_frame_ratio']}, Presenter={sam_res['human_presenter_frame_ratio']})")

        res_a = evaluate_method_a_spliced_video(p, slices, dl, sam_res, api_key)
        sc_a = res_a["audit"]["transparent_rubric"]["total_score"]
        print(f"   Method A (Spliced Video):      {res_a['total_latency_s']:5.2f}s | "
              f"Tokens={res_a['usage'].get('total_tokens'):5d} | "
              f"TransparentScore={sc_a:.2f}/2.50 | "
              f"LiveUI={res_a['audit'].get('product_footage_pct_estimate')}% | "
              f"Metrics={res_a['audit'].get('extracted_benchmark_metrics')}")

        res_b = evaluate_method_b_keyframes_plus_audio(p, slices, dl, sam_res, api_key)
        sc_b = res_b["audit"]["transparent_rubric"]["total_score"]
        print(f"   Method B (20 Keyframes+Audio): {res_b['total_latency_s']:5.2f}s | "
              f"Tokens={res_b['usage'].get('total_tokens'):5d} | "
              f"TransparentScore={sc_b:.2f}/2.50 | "
              f"LiveUI={res_b['audit'].get('product_footage_pct_estimate')}% | "
              f"Metrics={res_b['audit'].get('extracted_benchmark_metrics')}")

        results.append({
            "full_name": fn,
            "rank": p["rank"],
            "video_metadata": dl,
            "keyframe_timestamps_s": [k["timestamp_s"] for k in slices["keyframes"]],
            "sam_3_1_grounding": sam_res,
            "method_a_spliced_video": res_a,
            "method_b_20_keyframes_audio": res_b,
        })

    with open(BENCHMARK_OUTPUT, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved head-to-head 20-keyframe benchmark comparison to {BENCHMARK_OUTPUT}")
    return results


def is_cached_video_current(p: dict, existing_cache: dict) -> bool:
    fn = p["full_name"]
    if fn not in existing_cache or existing_cache[fn].get("status") != "audited":
        return False
    rec = existing_cache[fn]
    cur_best, _ = pick_best_video_url(fn, p.get("video_urls", []))
    old_url = rec.get("video_metadata", {}).get("primary_url", "")
    if cur_best and old_url and normalize_video_identity(cur_best) != normalize_video_identity(old_url):
        return False
    # For direct .mp4/.webm URLs (not YouTube/Vimeo/Loom/Wikimedia), check if the remote file was replaced in-place via Content-Length
    if cur_best and not any(k in cur_best.lower() for k in ("youtu.be", "youtube.com", "loom.com", "vimeo.com", "wikimedia.org")) and not cur_best.endswith("/film/"):
        lp = rec.get("video_metadata", {}).get("local_path", "")
        if lp and os.path.exists(lp):
            try:
                r = requests.head(cur_best, allow_redirects=True, timeout=4)
                rem_sz = int(r.headers.get("Content-Length", 0))
                if rem_sz > 10000 and abs(rem_sz - os.path.getsize(lp)) > 1024:
                    return False
            except Exception:
                pass
    return True


def audit_single_project_video(p: dict, api_key: str, existing_cache: dict, force_recompute_rubric: bool = True, force_method_b: bool = False) -> tuple[str, dict]:
    fn = p["full_name"]
    url_changed = (fn in existing_cache and existing_cache[fn].get("status") == "audited" and not is_cached_video_current(p, existing_cache))
    if is_cached_video_current(p, existing_cache):
        rec = existing_cache[fn]
        method_used = rec.get("muse_spark_1_3_eval", {}).get("method_used", "")
        if not force_method_b or "Method B (Upgraded)" in method_used:
            if force_recompute_rubric:
                tr = compute_transparent_video_score(
                    rec["video_metadata"],
                    rec["sam_3_1_grounding"],
                    rec["muse_spark_1_3_eval"],
                )
                rec["muse_spark_1_3_eval"]["transparent_rubric"] = tr
                rec["muse_spark_1_3_eval"]["final_video_score"] = tr["total_score"]
                sam_calls = int(rec["sam_3_1_grounding"].get("frames_sampled", 4)) * 4
                rec["muse_spark_1_3_eval"]["cost_breakdown"] = compute_api_cost(rec["muse_spark_1_3_eval"].get("usage", {}), sam_calls)
            return fn, rec

    dl = download_video(fn, p.get("video_urls", []), force_refresh=url_changed)
    if not dl.get("ok"):
        return fn, {
            "full_name": fn,
            "rank": p["rank"],
            "status": "download_failed",
            "video_metadata": dl,
            "audited_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    slices = prepare_media_slices(fn, dl["local_path"], dl["duration_s"], num_keyframes=20)
    sam_res = run_sam31_grounding(slices["keyframes"], api_key)

    # Use Upgraded Method B (20 Scene+Grid Keyframes + 3:00 Audio), falling back to Method A if needed
    try:
        spark_res = evaluate_method_b_keyframes_plus_audio(p, slices, dl, sam_res, api_key)
    except Exception as e_b:
        print(f"  [Fallback to Method A on {fn} due to: {e_b}]")
        spark_res = evaluate_method_a_spliced_video(p, slices, dl, sam_res, api_key)

    audit_obj = spark_res["audit"]
    tr = audit_obj["transparent_rubric"]
    sam_calls = int(sam_res.get("frames_sampled", 4)) * 4
    cost_bd = compute_api_cost(spark_res["usage"], sam_calls)

    return fn, {
        "full_name": fn,
        "rank": p["rank"],
        "status": "audited",
        "video_metadata": dl,
        "sam_3_1_grounding": sam_res,
        "muse_spark_1_3_eval": {
            "method_used": spark_res["method"],
            "upload_bytes": spark_res.get("upload_bytes", 0),
            "upload_latency_s": spark_res.get("upload_latency_s", 0.0),
            "inference_latency_s": spark_res.get("inference_latency_s", 0.0),
            "total_latency_s": spark_res["total_latency_s"],
            "usage": spark_res["usage"],
            "cost_breakdown": cost_bd,
            "final_video_score": tr["total_score"],
            **audit_obj,
        },
        "audited_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze hackathon competitor demo videos with SAM 3.1 + Muse Spark 1.3")
    parser.add_argument("--benchmark", type=int, default=0, help="Run head-to-head Method A vs Upgraded Method B (20 keyframes) benchmark on N videos")
    parser.add_argument("--top", type=int, default=128, help="Run video audit on Top N projects with demo videos")
    parser.add_argument("--force-method-b", action="store_true", help="Force re-running Upgraded Method B (20 keyframes + audio) if cached with Method A")
    parser.add_argument("--workers", type=int, default=3, help="Concurrent evaluation workers")
    parser.add_argument("--download-workers", type=int, default=6, help="Concurrent video download workers")
    parser.add_argument("--verify", action="store_true", help="Verify output JSON integrity")
    args = parser.parse_args()

    if args.verify:
        assert os.path.exists(BENCHMARK_OUTPUT), f"Missing {BENCHMARK_OUTPUT}"
        assert os.path.exists(VIDEO_AUDIT_OUTPUT), f"Missing {VIDEO_AUDIT_OUTPUT}"
        with open(BENCHMARK_OUTPUT) as f:
            bm = json.load(f)
        with open(VIDEO_AUDIT_OUTPUT) as f:
            va = json.load(f)
        assert len(bm) >= 4, "Expected at least 4 benchmark records"
        assert len(va) >= 25, "Expected at least 25 audited videos"
        for k, v in va.items():
            if v.get("status") == "audited":
                assert "transparent_rubric" in v.get("muse_spark_1_3_eval", {}), f"Missing transparent_rubric on {k}"
        audited_cnt = sum(1 for v in va.values() if v.get("status") == "audited")
        failed_cnt = sum(1 for v in va.values() if v.get("status") != "audited")
        print(f"VERIFIED: {len(bm)} benchmarked videos, {len(va)} total tracked videos ({audited_cnt} audited, {failed_cnt} dead/private links) in {VIDEO_AUDIT_OUTPUT}.")
        return

    api_key = load_meta_api_key()
    if not api_key:
        print("ERROR: META_API_KEY not found.")
        sys.exit(1)

    with open(AUDITED_INVENTORY_FILE) as f:
        inventory = json.load(f)

    video_projects = [p for p in inventory if p.get("has_video_demo")]
    target_projects = video_projects[: args.top]

    existing_audits = {}
    if os.path.exists(VIDEO_AUDIT_OUTPUT):
        try:
            with open(VIDEO_AUDIT_OUTPUT) as f:
                existing_audits = json.load(f)
        except Exception:
            existing_audits = {}

    if args.benchmark > 0:
        bm_results = run_benchmark(target_projects, api_key, count=args.benchmark)
        for item in bm_results:
            fn = item["full_name"]
            dl = item["video_metadata"]
            spark_res = item["method_b_20_keyframes_audio"]
            audit_obj = spark_res["audit"]
            tr = audit_obj["transparent_rubric"]
            existing_audits[fn] = {
                "full_name": fn,
                "rank": item["rank"],
                "status": "audited",
                "video_metadata": dl,
                "sam_3_1_grounding": item["sam_3_1_grounding"],
                "muse_spark_1_3_eval": {
                    "method_used": spark_res["method"],
                    "total_latency_s": spark_res["total_latency_s"],
                    "usage": spark_res["usage"],
                    "final_video_score": tr["total_score"],
                    **audit_obj,
                },
                "audited_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        with open(VIDEO_AUDIT_OUTPUT, "w") as f:
            json.dump(existing_audits, f, indent=2)

    print(f"\n=== STAGE 1: PRE-DOWNLOADING ALL {len(target_projects)} VIDEOS ({args.download_workers} WORKERS) + STAGE 2: AUDITING WITH MUSE SPARK 1.3 CONTRIBUTOR ({args.workers} WORKERS) ===")

    import threading
    save_lock = threading.Lock()
    cost_rows = []

    # Start background pre-download pool for all uncached or URL-updated videos while evaluation runs
    to_download = [
        p for p in target_projects
        if not is_cached_video_current(p, existing_audits)
    ]
    dl_pool = ThreadPoolExecutor(max_workers=args.download_workers)
    dl_futures = {
        p["full_name"]: dl_pool.submit(
            download_video,
            p["full_name"],
            p.get("video_urls", []),
            p["full_name"] in existing_audits and existing_audits[p["full_name"]].get("status") == "audited",
        )
        for p in to_download
    }
    print(f"Queued {len(dl_futures)} uncached/updated videos for parallel download ({len(target_projects) - len(dl_futures)} already cached).")

    def process_one(idx, p):
        fn = p["full_name"]
        # Wait for pre-download if it was queued
        if fn in dl_futures:
            try:
                dl_futures[fn].result()
            except Exception:
                pass
        _, res_record = audit_single_project_video(
            p, api_key, existing_audits, force_recompute_rubric=True, force_method_b=args.force_method_b
        )
        with save_lock:
            existing_audits[fn] = res_record
            with open(VIDEO_AUDIT_OUTPUT, "w") as f:
                json.dump(existing_audits, f, indent=2)

            if res_record.get("status") == "audited":
                ev = res_record["muse_spark_1_3_eval"]
                tr = ev["transparent_rubric"]
                cb = ev.get("cost_breakdown") or compute_api_cost(ev.get("usage", {}), 16)
                ev["cost_breakdown"] = cb
                row = {
                    "index": idx,
                    "rank": p["rank"],
                    "full_name": fn,
                    "status": "audited",
                    "method_used": ev.get("method_used"),
                    "duration_s": res_record["video_metadata"].get("duration_s"),
                    "latency_s": ev.get("total_latency_s"),
                    "score": tr["total_score"],
                    **cb,
                }
                cost_rows.append(row)
                print(f"[{len(cost_rows):3d}/{len(target_projects)}] #{p['rank']:3d} {fn:42s} -> {tr['total_score']:.2f}/2.50 | "
                      f"Tokens:{cb['total_tokens']:6d} | "
                      f"Cost(Contrib):${cb['total_cost_usd_contributor']:.4f} | "
                      f"Time:{ev.get('total_latency_s', 0):5.1f}s")
            else:
                err_msg = res_record.get("video_metadata", {}).get("error", "download_failed")
                cost_rows.append({
                    "index": idx,
                    "rank": p["rank"],
                    "full_name": fn,
                    "status": "download_failed",
                    "error": err_msg,
                    "input_tokens": 0, "cached_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0,
                    "total_tokens": 0, "sam_3_1_image_calls": 0,
                    "spark_cost_usd_contributor": 0.0, "spark_cost_usd_standard": 0.0,
                    "sam_3_1_cost_usd": 0.0, "total_cost_usd_contributor": 0.0, "total_cost_usd_standard": 0.0,
                    "score": 0.0,
                })
                print(f"[{len(cost_rows):3d}/{len(target_projects)}] #{p['rank']:3d} {fn:42s} -> FAILED ({err_msg})")

    with ThreadPoolExecutor(max_workers=args.workers) as eval_pool:
        eval_futs = [eval_pool.submit(process_one, idx, p) for idx, p in enumerate(target_projects, 1)]
        for fut in as_completed(eval_futs):
            try:
                fut.result()
            except Exception as e:
                print(f"Worker exception: {e}")

    dl_pool.shutdown(wait=False)
    cost_rows.sort(key=lambda r: r["index"])

    with open(VIDEO_AUDIT_OUTPUT, "w") as f:
        json.dump(existing_audits, f, indent=2)

    tot_in = sum(r["input_tokens"] for r in cost_rows)
    tot_out = sum(r["output_tokens"] for r in cost_rows)
    tot_sam = sum(r["sam_3_1_image_calls"] for r in cost_rows)
    tot_con = round(sum(r["total_cost_usd_contributor"] for r in cost_rows), 4)
    tot_std = round(sum(r["total_cost_usd_standard"] for r in cost_rows), 4)
    tot_spark_con = round(sum(r["spark_cost_usd_contributor"] for r in cost_rows), 4)
    tot_spark_std = round(sum(r["spark_cost_usd_standard"] for r in cost_rows), 4)
    tot_sam_usd = round(sum(r["sam_3_1_cost_usd"] for r in cost_rows), 4)

    summary = {
        "videos_evaluated": len(cost_rows),
        "total_input_tokens": tot_in,
        "total_output_tokens": tot_out,
        "total_tokens": tot_in + tot_out,
        "avg_tokens_per_video": round((tot_in + tot_out) / max(1, len(cost_rows))),
        "total_sam_3_1_image_calls": tot_sam,
        "spark_cost_usd_contributor_mode": tot_spark_con,
        "spark_cost_usd_standard_mode": tot_spark_std,
        "sam_3_1_cost_usd": tot_sam_usd,
        "total_cost_usd_contributor_mode": tot_con,
        "total_cost_usd_standard_mode": tot_std,
        "avg_cost_per_video_contributor_usd": round(tot_con / max(1, len(cost_rows)), 5),
        "avg_cost_per_video_standard_usd": round(tot_std / max(1, len(cost_rows)), 5),
        "projected_128_videos_contributor_usd": round((tot_con / max(1, len(cost_rows))) * 128, 2),
        "projected_128_videos_standard_usd": round((tot_std / max(1, len(cost_rows))) * 128, 2),
        "per_video": cost_rows,
    }
    with open(COST_REPORT_OUTPUT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n=== 20-VIDEO COST SUMMARY ===")
    print(f"Total Tokens: {tot_in + tot_out:,} (avg {summary['avg_tokens_per_video']:,} tok/video) | SAM 3.1 Calls: {tot_sam}")
    print(f"Contributor Mode Total (20 videos): ${tot_con:.4f} (Spark: ${tot_spark_con:.4f} + SAM 3.1: ${tot_sam_usd:.4f}) -> ${summary['avg_cost_per_video_contributor_usd']:.4f}/video")
    print(f"Standard Mode Total    (20 videos): ${tot_std:.4f} (Spark: ${tot_spark_std:.4f} + SAM 3.1: ${tot_sam_usd:.4f}) -> ${summary['avg_cost_per_video_standard_usd']:.4f}/video")
    print(f"Projected All 128 Videos: ${summary['projected_128_videos_contributor_usd']:.2f} (Contributor) | ${summary['projected_128_videos_standard_usd']:.2f} (Standard)")


if __name__ == "__main__":
    main()
