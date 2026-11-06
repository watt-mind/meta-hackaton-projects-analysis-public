import json
import os
import re
import time
import uuid
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

INVENTORY_FILE = 'projects_inventory.json'
AUDIT_FILE = 'audit_results_raw.json'
ENRICHMENTS_FILE = 'llm_enrichments.json'
OPENCODE_GO_URL = 'https://opencode.ai/zen/go/v1/responses'
META_API_URL = 'https://api.meta.ai/v1/responses'
DEFAULT_MODEL = 'muse-spark-1.3-contributor'

CANONICAL_DOMAINS = [
    "Multimodal Vision & Video (SAM / Vision)",
    "Autonomous Agents & Workflow Automation",
    "Developer Tooling, Infra & Security",
    "Healthcare, Civic Tech & Sustainability",
    "Voice, Speech & Audio AI",
    "Gaming, Entertainment & Creative Media",
    "Education & Knowledge Systems",
    "Business, Sales & Commerce",
    "Finance, Crypto & Web3",
    "Robotics, IoT & Manufacturing",
    "Legal & Compliance",
    "General & Emerging Applications",
]


def load_opencode_go_key():
    key = os.environ.get("OPENCODE_API_KEY")
    if key:
        return key.strip()
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("OPENCODE_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def load_meta_api_key():
    key = os.environ.get("META_API_KEY") or os.environ.get("MODEL_API_KEY")
    if key:
        return key.strip()
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("META_API_KEY=") or line.startswith("MODEL_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def call_muse_spark(prompt_text, oc_key=None, meta_key=None, model=DEFAULT_MODEL):
    payload = {
        "model": model,
        "reasoning": {"effort": "low"},
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt_text,
                    }
                ],
            }
        ],
        "stream": False,
    }

    if oc_key:
        headers = {
            "Authorization": f"Bearer {oc_key}",
            "Content-Type": "application/json",
            "x-opencode-session": f"ses_{uuid.uuid4().hex}",
            "x-opencode-request": f"req_{uuid.uuid4().hex}",
            "User-Agent": "opencode/1.0",
        }
        resp = requests.post(OPENCODE_GO_URL, headers=headers, json=payload, timeout=55)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("text"):
                            return c["text"]

    if meta_key:
        headers = {
            "Authorization": f"Bearer {meta_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(META_API_URL, headers=headers, json=payload, timeout=55)
        if resp.status_code != 200 and model != "muse-wonder-1.0":
            payload["model"] = "muse-wonder-1.0"
            payload.pop("reasoning", None)
            resp = requests.post(META_API_URL, headers=headers, json=payload, timeout=55)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("text"):
                        return c["text"]
    return ""


def extract_json_array(text):
    text = text.strip()
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    return json.loads(text)


def enrich_new_and_updated_repos(max_batches=80, max_workers=8):
    oc_key = load_opencode_go_key()
    meta_key = load_meta_api_key()
    if not oc_key and not meta_key:
        print("Warning: Neither OPENCODE_API_KEY nor META_API_KEY found; skipping LLM semantic enrichment.")
        return

    if not os.path.exists(INVENTORY_FILE):
        return

    with open(INVENTORY_FILE) as f:
        inventory = json.load(f)

    audit_map = {}
    if os.path.exists(AUDIT_FILE):
        with open(AUDIT_FILE) as f:
            audit_map = json.load(f)

    enrichments = {}
    if os.path.exists(ENRICHMENTS_FILE):
        try:
            with open(ENRICHMENTS_FILE) as f:
                enrichments = json.load(f)
        except Exception:
            enrichments = {}

    # Find repos that need LLM classification or README tooltip summary:
    to_enrich = []
    for p in inventory:
        fn = p["full_name"]
        audit = audit_map.get(fn, {})
        if audit.get("status") == "unavailable_or_deleted" or audit.get("merged_into"):
            continue
        readme_bytes = audit.get("readme_bytes", 0)
        readme_excerpt = (audit.get("readme_excerpt") or "").strip()
        desc = (p.get("description") or "").strip()
        if not readme_excerpt and not desc:
            continue

        cached = enrichments.get(fn)
        needs_enrichment = (
            not p.get("track")
            or not p.get("domain")
            or cached is None
            or not cached.get("readme_summary")
            or (readme_bytes > 500 and abs(readme_bytes - cached.get("readme_bytes", 0)) > 500)
        )
        if needs_enrichment:
            priority = 0 if (not cached or not cached.get("readme_summary")) else 1
            commits = audit.get("commits_in_window", 0)
            to_enrich.append((priority, -commits, p, audit))

    to_enrich.sort(key=lambda x: (x[0], x[1]))
    batch_size = 10
    candidates = [(p, audit) for _, _, p, audit in to_enrich[: max_batches * batch_size]]

    inv_by_name = {p["full_name"]: p for p in inventory}

    if candidates:
        provider_label = "OpenCode Go (muse-spark-1.3-contributor)" if oc_key else "Meta API (muse-spark-1.3-contributor)"
        batches = [candidates[i : i + batch_size] for i in range(0, len(candidates), batch_size)]
        print(f"Running {provider_label} README summarization & enrichment on {len(candidates)} repositories ({len(batches)} batches)...")

        def run_batch(b_idx, batch):
            items_payload = []
            for p, audit in batch:
                items_payload.append({
                    "full_name": p["full_name"],
                    "description": (p.get("description") or "")[:300],
                    "tree_entries": (audit.get("tree_entries") or [])[:15],
                    "readme_excerpt": (audit.get("readme_excerpt") or "")[:1000],
                })

            prompt = f"""You are analyzing repositories in the Meta Global AI Developer Hackathon 2026.
For each repository below, return a JSON array of objects with exact keys:
- "full_name": exact repo full_name
- "track": either "Push the Frontier" (for developer tools, security/privacy gateways, agent evaluation/verification frameworks, model fine-tuning/infra, robotics/embodied AI) OR "Build for Your World" (for consumer apps, industry/vertical workflows, multimodal vision/audio apps, healthcare, education, civic tech, gaming)
- "domain": MUST be one of {json.dumps(CANONICAL_DOMAINS)}
- "summary": a crisp plain-English 1-sentence hook (max 105 chars, no hype/buzzwords) of what the repository builds
- "readme_summary": 2-3 concise factual sentences explaining what the project does, its technical stack/architecture, and how it uses Meta AI / Muse models based on the README and file tree (max 300 chars, plain engineering tone)
- "tech_highlights": array of up to 3 short technical/model tags (max 28 chars each, e.g. ["SAM 3.1 Vision", "Muse Spark 1.3", "FastAPI + Next.js"])

Repositories to analyze:
{json.dumps(items_payload, indent=2)}

Return ONLY a valid JSON array, with no markdown code fences or extra commentary."""

            raw_text = call_muse_spark(prompt, oc_key=oc_key, meta_key=meta_key)
            return b_idx, batch, extract_json_array(raw_text)

        completed_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(run_batch, idx + 1, b): idx + 1 for idx, b in enumerate(batches)}
            for fut in as_completed(futures):
                b_idx = futures[fut]
                try:
                    _, batch, parsed = fut.result()
                    for res_item in parsed:
                        fn = res_item.get("full_name")
                        if not fn or fn not in inv_by_name:
                            continue
                        trk = res_item.get("track", "Build for Your World")
                        trk = "Push the Frontier" if "Push the Frontier" in trk else "Build for Your World"
                        dom = res_item.get("domain", "General & Emerging Applications")
                        if dom not in CANONICAL_DOMAINS:
                            dom = "General & Emerging Applications"
                        summary = (res_item.get("summary") or "").strip()
                        readme_summary = (res_item.get("readme_summary") or summary).strip()
                        tech_highlights = [str(t).strip()[:32] for t in (res_item.get("tech_highlights") or []) if str(t).strip()][:3]

                        enrichments[fn] = {
                            "track": trk,
                            "domain": dom,
                            "summary": summary,
                            "readme_summary": readme_summary,
                            "tech_highlights": tech_highlights,
                            "readme_bytes": audit_map.get(fn, {}).get("readme_bytes", 0),
                            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        }
                    completed_count += 1
                    if completed_count % 5 == 0 or completed_count == len(batches):
                        print(f"  Completed {completed_count}/{len(batches)} batches ({len(enrichments)} total cached)")
                        with open(ENRICHMENTS_FILE, "w") as f:
                            json.dump(enrichments, f, indent=2)
                except Exception as e:
                    print(f"  Warning on LLM batch {b_idx}: {e}")

    # Apply all cached enrichments to inventory
    for fn, enr in enrichments.items():
        if fn in inv_by_name:
            if enr.get("track"):
                inv_by_name[fn]["track"] = enr["track"]
            if enr.get("domain"):
                inv_by_name[fn]["domain"] = enr["domain"]
            if enr.get("summary"):
                inv_by_name[fn]["summary"] = enr["summary"]
            if enr.get("readme_summary"):
                inv_by_name[fn]["readme_summary"] = enr["readme_summary"]
            if enr.get("tech_highlights"):
                inv_by_name[fn]["tech_highlights"] = enr["tech_highlights"]

    with open(ENRICHMENTS_FILE, "w") as f:
        json.dump(enrichments, f, indent=2)

    with open(INVENTORY_FILE, "w") as f:
        json.dump(inventory, f, indent=2)

    print(f"Saved {len(enrichments)} LLM enrichments to {ENRICHMENTS_FILE} and updated {INVENTORY_FILE}.")


if __name__ == "__main__":
    enrich_new_and_updated_repos(max_batches=120, max_workers=10)
