import json
import os
import re
import sys
import time
import subprocess
import urllib.parse

print("=== 1. DISCOVERY: SEARCHING GITHUB FOR NEW HACKATHON REPOSITORIES ===")

QUERIES = [
    'topic:meta-hackathon-2026',
    'topic:meta-ai-hackathon',
    'topic:meta-ai-developer-hackathon',
    '"Meta Global AI Hackathon" in:name,description,readme',
    '"Meta Global AI Developer Hackathon" in:name,description,readme',
    '"Meta AI Developer Hackathon" in:name,description,readme pushed:>=2026-10-25',
    '"Meta AI Global Hackathon" in:name,description,readme pushed:>=2026-10-25',
    '"Muse Spark" in:readme created:>=2026-10-25',
    '"Muse Wonder" in:readme created:>=2026-10-25',
    '"Muse Glimmer" in:readme created:>=2026-10-25',
    '"SAM 3.1" in:readme created:>=2026-10-25',
    '"dev.meta.ai" in:readme created:>=2026-10-25',
    '"meta-model-api" in:readme created:>=2026-10-25',
    'meta hackathon 2026 created:>=2026-10-25',
    'meta ai developer hackathon pushed:>=2026-10-25',
    'meta hackathon 2026 pushed:>=2026-10-25',
    'meta ai hackathon 2026 pushed:>=2026-10-25',
    '"meta ai hackathon" pushed:>=2026-10-25',
    'cerebral valley meta pushed:>=2026-10-25'
]

FALSE_POSITIVE_REPOS = {
    'MassvHalo/Leeside',
    'minteeqahmed-png/ContextOS',
    'bme3412/ghost-operator-meta',
    '0xalkinun/LeatEngine',
    'yingfengke/agent-news-briefing',
    'halo-sw/homeless-society-sim',
    'abelxmendoza/hackathon-day-2-agents-101-legal-agent-workshop',
    'mzaks/ent-lang',
    'riteshyaaa/medfusion-ai',
}
FALSE_POSITIVE_LOWER = {r.lower() for r in FALSE_POSITIVE_REPOS}

SEED_REPOS = [
    'watt-mind/pii-guard',
    'MatiDegli/oversight',
    'Marwichmisi/NIATOLIP',
    'TsilavinaZh/RecupBuild',
    'arinde/shopThread',
    'ta-amps/agora-public-overview-architecture-setup-and-contribution',
    'ta-amps/eranos-public-marketplace-for-public-good-token-burn',
    'ta-amps/tessera-infrastructure-work-and-storage-engine',
    'ta-amps/herma-infrastructure-shim-for-intelligent-agents',
    'ta-amps/seed-packs-library-of-nouns-and-verbs',
    'ta-amps/ta-amps-hackathon',
    'mdbaasim/agent-workflow-security',
    'Kewlkiid/deskwright',
]

MULTI_REPO_GROUPS = {
    'ta-amps/agora-public-overview-architecture-setup-and-contribution': [
        'ta-amps/eranos-public-marketplace-for-public-good-token-burn',
        'ta-amps/tessera-infrastructure-work-and-storage-engine',
        'ta-amps/herma-infrastructure-shim-for-intelligent-agents',
        'ta-amps/seed-packs-library-of-nouns-and-verbs',
        'ta-amps/ta-amps-hackathon',
    ]
}

# Load existing audited inventory
AUDITED_FILE = 'projects_inventory_audited.json'
RAW_AUDIT_FILE = 'audit_results_raw.json'
INVENTORY_FILE = 'projects_inventory.json'

existing_by_name = {}
if os.path.exists(INVENTORY_FILE):
    with open(INVENTORY_FILE) as f:
        for p in json.load(f):
            fn = p['full_name']
            if fn.lower() not in FALSE_POSITIVE_LOWER and fn.split('/')[0].lower() != fn.split('/')[-1].lower():
                existing_by_name[fn] = p
if os.path.exists(AUDITED_FILE):
    with open(AUDITED_FILE) as f:
        for p in json.load(f):
            fn = p['full_name']
            if fn.lower() not in FALSE_POSITIVE_LOWER and fn.split('/')[0].lower() != fn.split('/')[-1].lower():
                existing_by_name[fn] = {**existing_by_name.get(fn, {}), **p}
print(f"Loaded {len(existing_by_name)} previously tracked repositories.")

found_items = {}

for q in QUERIES:
    enc_q = urllib.parse.quote_plus(q)
    print(f"Searching query: '{q}'...")
    for page in range(1, 4):
        cmd = ['gh', 'api', f'search/repositories?q={enc_q}&sort=updated&order=desc&per_page=100&page={page}']
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Warning on query '{q}' page {page}:", res.stderr[:120])
            break
        try:
            data = json.loads(res.stdout)
            items = data.get('items', [])
            if not items:
                break
            for item in items:
                name = item['full_name']
                owner_part, repo_part = name.split('/', 1)
                if owner_part.lower() == repo_part.lower() or name.lower() in FALSE_POSITIVE_LOWER:
                    continue
                if 'in:readme' in q and item.get('stargazers_count', 0) > 50:
                    continue
                c_at = item.get('created_at') or ''
                p_at = item.get('pushed_at') or item.get('updated_at') or ''
                # Ignore stale repositories from older hackathons (created before Oct 25 and not pushed since Oct 26)
                if c_at and c_at < '2026-10-25T00:00:00Z' and p_at and p_at < '2026-10-26T00:00:00Z':
                    continue
                if name not in found_items:
                    found_items[name] = item
            time.sleep(0.15)
        except Exception as e:
            print("Parse error:", e)
            break

# Ensure all explicit seed repos are present in found_items
for seed_name in SEED_REPOS:
    if seed_name not in found_items:
        if seed_name in existing_by_name:
            found_items[seed_name] = existing_by_name[seed_name]
        else:
            print(f"Fetching explicit seed repository: {seed_name}...")
            res = subprocess.run(['gh', 'api', f'repos/{seed_name}'], capture_output=True, text=True)
            if res.returncode == 0:
                try:
                    found_items[seed_name] = json.loads(res.stdout)
                except Exception as e:
                    print(f"Warning parsing seed repo {seed_name}:", e)

# Ingest untagged hackathon repositories discovered from Discord crawl
DISCORD_DISCOVERED_FILE = 'discord_discovered_repos.json'
if os.path.exists(DISCORD_DISCOVERED_FILE):
    print("Ingesting untagged hackathon repositories discovered from Discord crawl...")
    with open(DISCORD_DISCOVERED_FILE) as f:
        discord_repos = json.load(f)
    EXCLUDE_TOOLS = {
        'firecrawl/firecrawl', 'apify/crawlee', 'spider-rs/spider',
        'outline/outline', 'freqtrade/freqtrade', 'block/buzz',
        'heygen-com/hyperframes', 'kyutai-labs/pocket-tts', 'remotion-dev/remotion',
        'watt-mind/factory', 'GitFrog1111/OpenWhip', 'lyramakesmusic/neuron-explorer',
        'sting8k/pi-vcc', 'timmyy123/LLM-Hub', 'flarelink-in/NullGraph', 'Leonxlnx/cinetic',
        'withnative/native', 'nyosegawa/speech.cpp', 'sinanuozdemir/ai-experiments',
        'TsilavinaZh/TsilavinaZH', 'NishantDas0079/NishantDas0079', 'pbakaus/impeccable',
        'nextlevelbuilder/ui-ux-pro-max-skill', 'earendil-works/pi',
        'constellation-works/orbit', 'Juanpacol/SEPHIROTH', 'mzaks/ent-lang',
        'riteshyaaa/medfusion-ai', 'checocadena/oneapi-agent-toolkit', 'UMDSmith/HexCast',
        'halo-sw/homeless-society-sim', 'CopilotKit/generative-ui'
    }
    added_discord = 0
    for r in discord_repos:
        name = r['full_name']
        if name in EXCLUDE_TOOLS or r.get('stars', 0) > 50:
            continue
        c_at = r.get('created_at') or ''
        ch_lower = (r.get('discord_channel') or '').lower()
        if c_at and c_at < '2026-10-20' and 'intros' in ch_lower:
            continue
        if r.get('pushed_at', '') >= '2026-10-25' or c_at >= '2026-10-25':
            if name not in found_items:
                found_items[name] = {
                    'full_name': name,
                    'name': name.split('/')[-1],
                    'html_url': r.get('html_url', f"https://github.com/{name}"),
                    'description': r.get('description') or '',
                    'stargazers_count': r.get('stars', 0),
                    'forks_count': r.get('forks', 0),
                    'created_at': r.get('created_at'),
                    'updated_at': r.get('pushed_at'),
                    'inferred_track': r.get('inferred_track'),
                    'video_links': r.get('video_links') or r.get('videos') or []
                }
                added_discord += 1
            else:
                if r.get('video_links') or r.get('videos'):
                    found_items[name]['video_links'] = r.get('video_links') or r.get('videos')
    print(f"Added {added_discord} untagged Discord-discovered repositories to found_items.")

new_count = sum(1 for name in found_items if name not in existing_by_name)
print(f"Total discovered in crawl: {len(found_items)} repositories. ({new_count} brand new!)")

# Merge discovered into inventory and refresh metadata on existing ones
for name, item in found_items.items():
    if name not in existing_by_name:
        track = item.get('inferred_track')
        if not track or track == 'General':
            track = 'Push the Frontier' if any(k in (item.get('description') or '').lower() for k in ['robotics', 'hardware', 'security', 'privacy', 'frontier', 'material', 'physics', 'energy', 'verifiable', 'rule of two']) else 'Build for Your World'

        existing_by_name[name] = {
            'full_name': name,
            'name': item.get('name', name.split('/')[-1]),
            'owner': name.split('/')[0],
            'html_url': item.get('html_url', f"https://github.com/{name}"),
            'description': item.get('description') or '',
            'domain': 'Developer Tooling, Infra & Security' if any(k in (item.get('description') or '').lower() for k in ['tool', 'agent', 'infra', 'dev', 'api', 'code']) else 'General & Emerging Applications',
            'track': track,
            'stars': item.get('stargazers_count', 0),
            'forks': item.get('forks_count', 0),
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at'),
            'video_links': item.get('video_links', [])
        }
    else:
        if item.get('description'):
            existing_by_name[name]['description'] = item.get('description')
        if item.get('stargazers_count') is not None:
            existing_by_name[name]['stars'] = item.get('stargazers_count', 0)
        if item.get('updated_at'):
            existing_by_name[name]['updated_at'] = item.get('updated_at')
        if item.get('video_links'):
            existing_by_name[name]['video_links'] = item.get('video_links')

# Merge newly discovered Discord video URLs for tracked repositories
DISCORD_SUMMARY_FILE = 'discord_audit_summary.json'
EXPLICIT_DISCORD_VIDEOS = {
    'TsilavinaZh/RecupBuild': ['https://www.youtube.com/watch?v=sO_UkvMmugU'],
    'arinde/shopThread': ['https://youtu.be/R41-tiytYAU'],
    'phil10xs/vergefield-os': ['https://www.youtube.com/watch?v=aHLs56BK9LY'],
    'carlosfcosme/trust-proof-work': ['https://www.youtube.com/watch?v=LXloegum4Rc'],
    'starlord20/bucketwise': ['https://www.loom.com/share/1d965246b5e4492ea5329a3e7e98fe6d'],
    'aeroxy/paper-bro': ['https://www.youtube.com/watch?v=7egZZNXmRTQ', 'https://youtube.com/shorts/utHsTx-Orys'],
    'pagyemang-dotcom/meaning-check': ['https://youtu.be/5yTS6-LR2_c'],
    'agmonp/muse-life-graph': ['https://youtu.be/JX4o7B06awk'],
    'fahim-muntasir-niloy/krishibondhu-AI-meta-hackathon': ['https://youtu.be/23cUn40t4lE'],
    'hari431/underwriting-guideline-synthesizer': ['https://youtu.be/El9TkXUMIJg'],
    'athos-agent/athos': ['https://www.youtube.com/watch?v=eRrc1pUY5oU'],
    'louislafosse/jojo': ['https://youtu.be/t1AZFQDP-7E'],
    'tiempoespacio/GeoPrice': ['https://www.youtube.com/watch?v=eqKYygr2MWg'],
    'leonidasrocky123-cell/edited-agent': ['https://youtu.be/r85ZylOxQTs'],
    'EmirCobanOfficial/courtsense': ['https://youtu.be/aLUSjad3vto'],
    'JeanCyrilleD/nova2-meta-hackathon': ['https://youtu.be/XUFS6rvUn8o', 'https://youtu.be/TSjw5fsBKsM'],
    'ziffan/LexRAGLab-Meta2026Hackathon': ['https://www.youtube.com/watch?v=BMXQfIeGhqw'],
    'donovan-ratefison/Zotra': ['https://www.youtube.com/watch?v=FBQbIOHB1C8'],
    'sitrsh12/meta-ai-hackathon-Aahwan_IT_Group': ['https://www.youtube.com/watch?v=JlpBn9pfQHI'],
    'Neufal777/norba-travels-agent': ['https://youtu.be/aB1zQSqTdUs'],
    'momoikura/The-Polisher': ['https://youtu.be/owxcagxox9g'],
    'tsetse012/60-second-fire-check': ['https://youtu.be/kqjzhUy9dWA'],
    'aungsan-portfolio/meta-quant-auditor': ['https://www.youtube.com/watch?v=MrQomF8UIhY'],
    'athos-agent/athos-meta': ['https://youtu.be/z-h-IQQo1AQ'],
    'vmbr068/netmedic': ['https://youtu.be/_QdP5m4D6-Q'],
    'AKMaasif/Meta-Ai-Global-Hackathon-Ran-Sentinel-': ['https://www.youtube.com/watch?v=hcaJiB8FBA8', 'https://youtu.be/3wnNHKDH-lE'],
    'Manuekle/focus': ['https://www.youtube.com/watch?v=px1O2JH44tM'],
    'songynjae/pyosi-ai': ['https://youtu.be/HkD8FCpOZqw'],
    'EmilJaf/wellpilot': ['https://youtu.be/sfALFx8DpYM'],
}
existing_by_name.pop('halo-sw/homeless-society-sim', None)
if os.path.exists(DISCORD_SUMMARY_FILE):
    try:
        with open(DISCORD_SUMMARY_FILE) as f:
            ds_data = json.load(f)
        for lower_name, vinfo in (ds_data.get('new_videos_for_tracked') or {}).items():
            # Prepend newly discovered Discord videos so newer Discord posts supersede earlier drafts
            prev = EXPLICIT_DISCORD_VIDEOS.get(vinfo['full_name'], [])
            EXPLICIT_DISCORD_VIDEOS[vinfo['full_name']] = list(dict.fromkeys((vinfo.get('new_videos') or []) + prev))
    except Exception as e:
        print("Warning reading discord_audit_summary.json:", e)

if os.path.exists('discord_delta_run_report.json'):
    try:
        with open('discord_delta_run_report.json') as f:
            dd_data = json.load(f)
        for lower_name, rinfo in (dd_data.get('delta_repos') or {}).items():
            if rinfo.get('videos'):
                prev = EXPLICIT_DISCORD_VIDEOS.get(rinfo['full_name'], [])
                EXPLICIT_DISCORD_VIDEOS[rinfo['full_name']] = list(dict.fromkeys((rinfo.get('videos') or []) + prev))
    except Exception as e:
        print("Warning reading discord_delta_run_report.json:", e)

lower_to_canonical = {k.lower(): k for k in existing_by_name}
for repo_key, vids in EXPLICIT_DISCORD_VIDEOS.items():
    canon = lower_to_canonical.get(repo_key.lower())
    if canon and vids:
        cur_vids = list(existing_by_name[canon].get('video_links') or [])
        # Put latest Discord videos first, followed by any prior video_links
        merged_vids = list(dict.fromkeys(list(vids) + cur_vids))
        existing_by_name[canon]['video_links'] = merged_vids

all_repos_list = list(existing_by_name.values())
with open(INVENTORY_FILE, 'w') as f:
    json.dump(all_repos_list, f, indent=2)

print(f"Updated inventory saved: {len(all_repos_list)} total repositories.")

print("\n=== 2. AUDIT: RUNNING CODE & GIT FORENSICS (GRAPHQL BATCHES) ===")

raw_audit_data = {}
if os.path.exists(RAW_AUDIT_FILE):
    with open(RAW_AUDIT_FILE) as f:
        raw_audit_data = json.load(f)

# Priority: audit all new repos + audit top contenders + audit recently updated repos
BATCH_SIZE = 8

def build_graphql_batch(batch):
    parts = []
    for idx, p in enumerate(batch):
        owner, name = p['full_name'].split('/', 1)
        alias = f"r{idx}"
        part = f"""
  {alias}: repository(owner: "{owner}", name: "{name}") {{
    nameWithOwner
    createdAt
    pushedAt
    nameWithOwner
    diskUsage
    isFork
    forkCount
    stargazerCount
    description
    homepageUrl
    pullRequests {{
      totalCount
    }}
    mergedPullRequests: pullRequests(states: MERGED) {{
      totalCount
    }}
    primaryLanguage {{
      name
    }}
    defaultBranchRef {{
      name
      target {{
        ... on Commit {{
          history(since: "2026-10-26T00:00:00Z") {{
            totalCount
          }}
          preHistory: history(until: "2026-10-26T00:00:00Z") {{
            totalCount
          }}
        }}
      }}
    }}
    readme: object(expression: "HEAD:README.md") {{
      ... on Blob {{
        byteSize
        text
      }}
    }}
    readmeLower: object(expression: "HEAD:readme.md") {{
      ... on Blob {{
        byteSize
        text
      }}
    }}
    readmeTitle: object(expression: "HEAD:Readme.md") {{
      ... on Blob {{
        byteSize
        text
      }}
    }}
    readmeUpper: object(expression: "HEAD:README.MD") {{
      ... on Blob {{
        byteSize
        text
      }}
    }}
    readmeTxt: object(expression: "HEAD:README.txt") {{
      ... on Blob {{
        byteSize
        text
      }}
    }}
    pyproject: object(expression: "HEAD:pyproject.toml") {{
      ... on Blob {{
        text
      }}
    }}
    backendPyproject: object(expression: "HEAD:backend/pyproject.toml") {{
      ... on Blob {{
        text
      }}
    }}
    reqs: object(expression: "HEAD:requirements.txt") {{
      ... on Blob {{
        text
      }}
    }}
    backendReqs: object(expression: "HEAD:backend/requirements.txt") {{
      ... on Blob {{
        text
      }}
    }}
    pkg: object(expression: "HEAD:package.json") {{
      ... on Blob {{
        text
      }}
    }}
    frontendPkg: object(expression: "HEAD:frontend/package.json") {{
      ... on Blob {{
        text
      }}
    }}
    cargo: object(expression: "HEAD:Cargo.toml") {{
      ... on Blob {{
        text
      }}
    }}
    dockerfile: object(expression: "HEAD:Dockerfile") {{
      ... on Blob {{
        byteSize
      }}
    }}
    deployDockerfile: object(expression: "HEAD:deploy/fly/Dockerfile") {{
      ... on Blob {{
        byteSize
      }}
    }}
    compose: object(expression: "HEAD:compose.yaml") {{
      ... on Blob {{
        byteSize
      }}
    }}
    dockerCompose: object(expression: "HEAD:docker-compose.yml") {{
      ... on Blob {{
        byteSize
      }}
    }}
    videoTree: object(expression: "HEAD:site/video") {{
      ... on Tree {{
        entries {{
          name
          type
        }}
      }}
    }}
    tree: object(expression: "HEAD:") {{
      ... on Tree {{
        entries {{
          name
          type
        }}
      }}
    }}
  }}"""
        parts.append(part)

    query = "query {\n" + "\n".join(parts) + "\n}"
    return query

def execute_graphql(query):
    cmd = ['gh', 'api', 'graphql', '-f', f'query={query}']
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = res.stdout if res.stdout else res.stderr
    try:
        return json.loads(out)
    except Exception as e:
        return None

VIDEO_PATTERN = re.compile(r'https?://(?:(?:www\.)?(?:youtube\.com/watch\?v=[a-zA-Z0-9_-]+|youtu\.be/[a-zA-Z0-9_-]+|loom\.com/share/[a-zA-Z0-9_-]+|vimeo\.com/[0-9]+|streamable\.com/[a-zA-Z0-9_-]+|drive\.google\.com/file/d/[a-zA-Z0-9_-]+)|[^\s\)\]\">]+(?:\.mp4|\.webm|/film/?))', re.IGNORECASE)
LIVE_DEPLOY_PATTERN = re.compile(r'https?://[a-zA-Z0-9.-]+\.(?:vercel\.app|railway\.app|render\.com|hf\.space|fly\.dev|streamlit\.app|modal\.run|netlify\.app|pages\.dev|workers\.dev|github\.io|cloudflare\.com|onrender\.com)(?:/[^\s\)\]\">]*)?', re.IGNORECASE)

ANTI_PROJECT_PATTERNS = [
    (re.compile(r'\b(mental health|therapist|depression|anxiety advisor|skin blemish|medical advice|symptom checker|doctor ai)\b', re.IGNORECASE), "Banned Medical / Health Advisor"),
    (re.compile(r'\b(basic rag|simple rag|naive rag|rag chatbot)\b', re.IGNORECASE), "Banned Basic RAG"),
    (re.compile(r'\b(simple image analyzer|meme generator)\b', re.IGNORECASE), "Banned Simple Image Analyzer"),
    (re.compile(r'\b(job application screener|resume screener|resume ranker|applicant screener)\b', re.IGNORECASE), "Banned AI Job Screener"),
    (re.compile(r'\b(nutrition coach|diet coach|calorie counter|meal planner ai)\b', re.IGNORECASE), "Banned Nutrition Coach"),
    (re.compile(r'\b(personality analyzer|zodiac|horoscope)\b', re.IGNORECASE), "Banned Personality Analyzer"),
    (re.compile(r'\b(sports analyzer|sports coach|workout coach)\b', re.IGNORECASE), "Banned Sports Coach/Analyzer"),
    (re.compile(r'\b(election|political campaign|voter persuasion|weapon|warfare)\b', re.IGNORECASE), "Banned Political / Defense Policy")
]

# Re-audit ALL tracked repositories on every run so newly added videos, live URLs, Dockerfiles, tests, or commits are always caught
from concurrent.futures import ThreadPoolExecutor, as_completed
to_audit = list(all_repos_list)
print(f"Auditing all {len(to_audit)} tracked repositories for code, README, video, and live deploy updates...")

batches = [to_audit[i:i+BATCH_SIZE] for i in range(0, len(to_audit), BATCH_SIZE)]
batch_count = len(batches)

def fetch_batch(b_idx, batch):
    query = build_graphql_batch(batch)
    resp = execute_graphql(query)
    return b_idx, batch, (resp.get('data', {}) if resp else {})

done_batches = 0
with ThreadPoolExecutor(max_workers=5) as pool:
    futs = [pool.submit(fetch_batch, idx + 1, b) for idx, b in enumerate(batches)]
    for fut in as_completed(futs):
        b_idx, batch, data = fut.result()
        done_batches += 1

        for idx, p in enumerate(batch):
            full_name = p['full_name']
            alias = f"r{idx}"
            r_data = data.get(alias) if data else None

            if not r_data:
                if full_name not in raw_audit_data:
                    raw_audit_data[full_name] = {
                        "full_name": full_name,
                        "status": "unavailable_or_deleted",
                        "audited_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                continue

            target_obj = r_data.get('defaultBranchRef', {}).get('target', {}) if r_data.get('defaultBranchRef') else {}
            history = target_obj.get('history', {}) if target_obj else {}
            pre_history = target_obj.get('preHistory', {}) if target_obj else {}
            commits_in_window = history.get('totalCount', 0) if history else 0
            commits_before_window = pre_history.get('totalCount', 0) if pre_history else 0
            prs_total = (r_data.get('pullRequests') or {}).get('totalCount', 0)
            prs_merged = (r_data.get('mergedPullRequests') or {}).get('totalCount', 0)

            readme_obj = (
                r_data.get('readme')
                or r_data.get('readmeLower')
                or r_data.get('readmeTitle')
                or r_data.get('readmeUpper')
                or r_data.get('readmeTxt')
            )
            readme_text = readme_obj.get('text', '') if readme_obj else ''
            readme_bytes = readme_obj.get('byteSize', 0) if readme_obj else 0

            tree_entries = [e['name'] for e in (r_data.get('tree', {}).get('entries') or [])] if r_data.get('tree') else []

            has_docker = (
                r_data.get('dockerfile') is not None or
                r_data.get('deployDockerfile') is not None or
                r_data.get('compose') is not None or
                r_data.get('dockerCompose') is not None or
                'Dockerfile' in tree_entries or
                'compose.yaml' in tree_entries or
                'docker-compose.yml' in tree_entries
            )

            repo_pkg_prefix = full_name.split('/')[-1].split('-')[0].lower()
            has_tests = any('test' in e.lower() or 'spec' in e.lower() for e in tree_entries)
            has_src = any(e.lower() in ['src', 'app', 'backend', 'frontend', 'server', 'lib', 'packages', 'services', 'core', 'site', 'packs', 'scripts', repo_pkg_prefix] for e in tree_entries)
            has_ci = '.github' in tree_entries

            pyproject_text = "\n".join(filter(None, [
                r_data.get('pyproject', {}).get('text', '') if r_data.get('pyproject') else '',
                r_data.get('backendPyproject', {}).get('text', '') if r_data.get('backendPyproject') else '',
            ]))
            reqs_text = "\n".join(filter(None, [
                r_data.get('reqs', {}).get('text', '') if r_data.get('reqs') else '',
                r_data.get('backendReqs', {}).get('text', '') if r_data.get('backendReqs') else '',
            ]))
            pkg_text = "\n".join(filter(None, [
                r_data.get('pkg', {}).get('text', '') if r_data.get('pkg') else '',
                r_data.get('frontendPkg', {}).get('text', '') if r_data.get('frontendPkg') else '',
            ]))
            cargo_text = r_data.get('cargo', {}).get('text', '') if r_data.get('cargo') else ''

            all_dep_text = f"{pyproject_text}\n{reqs_text}\n{pkg_text}\n{cargo_text}".lower()

            is_meta_api_in_deps = any(k in all_dep_text for k in ['meta-model-api', 'dev.meta.ai', 'muse-spark', 'muse_spark', 'muse-wonder', 'muse-image', 'sam-3', 'sam3'])
            is_baseten_in_deps = 'baseten' in all_dep_text
            is_fireworks_in_deps = 'fireworks' in all_dep_text
            is_together_in_deps = 'together' in all_dep_text
            is_open_weights_tuning = any(k in all_dep_text for k in ['peft', 'unsloth', 'axolotl', 'transformers', 'vllm', 'sglang', 'deepspeed', 'torch'])
            is_competitor_in_deps = any(k in all_dep_text for k in ['anthropic', 'google-generativeai', 'google.genai', 'cohere'])
            is_agent_framework = any(k in all_dep_text for k in ['langgraph', 'langchain', 'crewai', 'autogen', 'llamaindex', 'pydantic-ai'])

            readme_lower = readme_text.lower()
            has_muse_spark = 'muse spark' in readme_lower or 'muse-spark' in readme_lower
            has_muse_wonder = 'muse wonder' in readme_lower or 'muse-wonder' in readme_lower
            has_muse_glimmer = 'muse glimmer' in readme_lower or 'muse-glimmer' in readme_lower
            has_muse_code = 'muse code' in readme_lower or 'muse-code' in readme_lower
            has_sam = 'sam 3' in readme_lower or 'sam-3' in readme_lower
            has_meta_api = 'dev.meta.ai' in readme_lower or 'meta model api' in readme_lower

            homepage_url = (r_data.get('homepageUrl') or '').strip()
            repo_desc = (r_data.get('description') or p.get('description') or '').strip()
            combined_surface_text = f"{readme_text}\n{repo_desc}\n{homepage_url}"

            def _is_valid_video_url(u):
                ul = u.lower()
                if any(bad in ul for bad in ['todo', 'xxxx', 'your_', 'your-', 'video_id', 'example.com', 'wikimedia.org', 'placeholder', 'watch?v=...', 'youtu.be/...']):
                    return False
                if ('youtu.be/' in ul or 'watch?v=' in ul) and len(u.split('/')[-1].split('v=')[-1].split('&')[0]) < 10:
                    return False
                return True

            video_matches = [u for u in dict.fromkeys(VIDEO_PATTERN.findall(combined_surface_text)) if _is_valid_video_url(u)]
            if r_data.get('videoTree') and homepage_url.startswith(('http://', 'https://')):
                film_url = homepage_url.rstrip('/') + '/film/'
                if film_url not in video_matches:
                    video_matches.insert(0, film_url)
            for dv in p.get('video_links', []):
                if dv not in video_matches and _is_valid_video_url(dv):
                    video_matches.append(dv)
            live_matches = list(dict.fromkeys(LIVE_DEPLOY_PATTERN.findall(combined_surface_text)))
            if homepage_url.startswith(('http://', 'https://')) and not any(d in homepage_url.lower() for d in ['github.com', 'youtube.com', 'youtu.be', 'loom.com', 'vimeo.com', 'localhost', '127.0.0.1']):
                if homepage_url not in live_matches:
                    live_matches.insert(0, homepage_url)

            anti_flag = None
            for pat, reason in ANTI_PROJECT_PATTERNS:
                if pat.search(readme_text) or pat.search(p.get('description') or ''):
                    anti_flag = reason
                    break

            created_at = r_data.get('createdAt', '')
            is_created_before_hackathon = bool((created_at and created_at < "2026-10-26T00:00:00Z") or commits_before_window > 0)

            raw_audit_data[full_name] = {
                "full_name": full_name,
                "renamed_to": r_data.get('nameWithOwner') if (r_data.get('nameWithOwner') and r_data.get('nameWithOwner') != full_name) else None,
                "status": "audited",
                "created_at": created_at,
                "pushed_at": r_data.get('pushedAt'),
                "disk_usage_kb": r_data.get('diskUsage'),
                "is_fork": r_data.get('isFork'),
                "fork_count": r_data.get('forkCount'),
                "stars": r_data.get('stargazerCount'),
                "commits_in_window": commits_in_window,
                "commits_before_window": commits_before_window,
                "prs_total": prs_total,
                "prs_merged": prs_merged,
                "is_created_before_hackathon": is_created_before_hackathon,
                "tree_entries_count": len(tree_entries),
                "tree_entries": tree_entries[:60],
                "readme_bytes": readme_bytes,
                "readme_excerpt": readme_text[:3000],
                "has_docker": has_docker,
                "has_tests": has_tests,
                "has_src": has_src,
                "has_ci": has_ci,
                "has_pyproject": bool(pyproject_text),
                "has_requirements": bool(reqs_text),
                "has_package_json": bool(pkg_text),
                "meta_api_in_deps": is_meta_api_in_deps,
                "baseten_in_deps": is_baseten_in_deps,
                "fireworks_in_deps": is_fireworks_in_deps,
                "together_in_deps": is_together_in_deps,
                "open_weights_tuning_in_deps": is_open_weights_tuning,
                "competitor_in_deps": is_competitor_in_deps,
                "agent_framework_in_deps": is_agent_framework,
                "readme_cites_muse_spark": has_muse_spark,
                "readme_cites_muse_wonder": has_muse_wonder,
                "readme_cites_muse_glimmer": has_muse_glimmer,
                "readme_cites_muse_code": has_muse_code,
                "readme_cites_sam": has_sam,
                "readme_cites_meta_api": has_meta_api,
                "video_demo_urls": video_matches,
                "has_video_demo": len(video_matches) > 0,
                "live_deploy_urls": live_matches,
                "has_live_deploy": len(live_matches) > 0,
                "anti_project_flag": anti_flag,
                "audited_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }

        if done_batches % 15 == 0 or done_batches == batch_count:
            with open(RAW_AUDIT_FILE, 'w') as f:
                json.dump(raw_audit_data, f, indent=2)
            print(f"Batch {done_batches}/{batch_count} processed ({len(raw_audit_data)} total cached).")

import process_audit_and_rescore
process_audit_and_rescore.aggregate_multi_repo_groups(raw_audit_data)
with open(RAW_AUDIT_FILE, 'w') as f:
    json.dump(raw_audit_data, f, indent=2)

import sys
print("\n=== 2.5. LLM SEMANTIC ENRICHMENT (MUSE SPARK 1.3 CONTRIBUTOR) ===")
subprocess.run([sys.executable, 'llm_enrich.py'], check=False)

print("\n=== 3. RESCORING, RANKING & POINT-IN-TIME SNAPSHOTS ===")
process_audit_and_rescore.rescore_all()
subprocess.run([sys.executable, 'record_history.py'], check=True)

print("\n=== 3.5. MULTIMODAL VIDEO AUDIT (SAM 3.1 + MUSE SPARK 1.3) ===")
subprocess.run([sys.executable, 'analyze_videos.py', '--top', '2000', '--workers', '6'], check=False)

print("\n=== 4. REBUILDING ARTIFACTS, OG IMAGE & MARKDOWN ===")
subprocess.run([sys.executable, 'generate_og_image.py'], check=True)
subprocess.run([sys.executable, 'generate_html_report.py'], check=True)
subprocess.run([sys.executable, 'generate_submission_checklist.py'], check=True)
subprocess.run([sys.executable, 'generate_markdown.py'], check=True)

print("\n=== 5. BUILDING & DEPLOYING TO CLOUDFLARE WORKER ===")
subprocess.run([sys.executable, 'build_worker.py'], check=True)
res = subprocess.run(['cd wattmind-artifacts && npx --yes wrangler deploy'], shell=True, capture_output=True, text=True)
print(res.stdout)
if res.returncode == 0:
    print("SUCCESS: Live report updated on https://artifacts.watt-mind.com/meta-hackathon-2026/!")
else:
    print("Deployment error:", res.stderr)
