import json
import os
import re

AUDIT_FILE = 'audit_results_raw.json'
INVENTORY_FILE = 'projects_inventory.json'
AUDITED_INVENTORY_FILE = 'projects_inventory_audited.json'
CSV_OUTPUT_FILE = 'projects_inventory_audited.csv'

MULTI_REPO_GROUPS = {
    'ta-amps/agora-public-overview-architecture-setup-and-contribution': [
        'ta-amps/eranos-public-marketplace-for-public-good-token-burn',
        'ta-amps/tessera-infrastructure-work-and-storage-engine',
        'ta-amps/herma-infrastructure-shim-for-intelligent-agents',
        'ta-amps/seed-packs-library-of-nouns-and-verbs',
        'ta-amps/ta-amps-hackathon',
    ],
    'omenking/meta-ai-field-notes': [
        'omenking/meta-costcenter',
        'omenking/meta-keyguard',
    ],
}

SUPERSEDED_REPOS = {
    'ta-amps/hackathon-context': 'ta-amps/ta-amps-hackathon',
    'martinmw13/lectoria': 'martinmw13/LectorIA-meta',
    'denmarkamanodaya/meta-hackathon-nimbxxxytes': 'denmarkamanodaya/meta-hackathon-nimbytes',
    'prohle/schedulegod-ai': 'prohle/schedulesolve-ai',
    'scoobydoobydrew/meta_ai_hackathon': 'scoobydoobydrew/cellproof',
    'seegongsik/whatif-camera': 'seegongsik/whats-ahead',
    'phil10xs/vergefield-os': 'phil10xs/vergecare-meta',
    'mrfentmen/meta-sentinel': 'mrfentmen/meta-os',
    'seanudeke/Nightshift': 'seanudeke/Expectrail',
    'calvinmilliken1994-spec/meta-hackathon-2026': 'calvinmilliken1994-spec/kinetext-metahackathon2026',
    'ahk1542001-wq/pageops-agent': 'ahk1542001-wq/PaCo',
    'Mishallic/Afterimage': 'Mishallic/piece-of-mind',
    'jccarrascov-sudo/pantallita': 'jccarrascov-sudo/edith',
    'jerovasgo/evidence-workbench': 'jerovasgo/genebark',
    'FX-DOVE/opie-ai-movie-studio': 'FX-DOVE/reelforge',
    'AnuranjanJain/MetaAI2026': 'AnuranjanJain/pocketroom',
    'mohiddin7/indexreel': 'mohiddin7/IndexReel',
    'Mashrokit-AI/offer-guard': 'Mashrokit-AI/matchpic',
    'jielle2453/roadside-guide': 'jielle2453/chitchat-tour',
    'Vaibhav-CD/SmartInk': 'Vaibhav-CD/SmartINK',
    'jerrydjin/backtothefuture': 'jerrydjin/malleable',
    'sensei-hq/snap-to-make': 'sensei-hq/katachi',
    'phantom007xy/photo-authenticity-checker': 'phantom007xy/ImageDETECTIVE',
    'ashrafi/MetaMuse': 'ashrafi/LifeSOS',
    'RohanJosephGeorge/Spatial_Memory_Geoguesser': 'RohanJosephGeorge/ReTracer_AI',
    'DavidFox998/soph-e-runway': 'DavidFox998/meta-runway',
    'danrave1234/oddhound-claude': 'danrave1234/oddhound',
    'mis8680-lab/packback': 'mis8680-lab/unscrewed',
    'wujotung9627-svg/mutation-forge': 'wujotung9627-svg/last-one-out',
    'Redaelm47/meta-motion-ads': 'Redaelm47/adistribution-system',
    'EonEmmanuel/meta-ai-hackathon': 'EonEmmanuel/Cadastra',
    'trivnvdev-41/SEO-UGC-Meta-Hackathon-2026': 'trivnvdev-41/saba-meta-hackathon-2026',
    'albertojbravo-art/shift-copilot': 'albertojbravo-art/Shift-Sight-Ops',
    'actions-marketplace-validations/ManasMehta1110_pinpoint': 'ManasMehta1110/pinpoint',
    '419to808-byte/the-podium-1-0': '419to808-byte/the-podium',
    'anshupriyan/enheduanna': 'anshupriyan/enheduanna-meta-submission',
    'bhoot-biswas/listsnap': 'bhoot-biswas/listsnap-app',
    'BU1lDR/ArthNiti': 'BU1lDR/ArthNiti-Meta_Hackathon',
    'buildwithdesi/vibeaudit-2-demo-app': 'buildwithdesi/vibeaudit-2',
    'EmirCobanOfficial/courtsense-site': 'EmirCobanOfficial/courtsense',
    'EvilMetaMonkey/dmc-meta-hackathon': 'EvilMetaMonkey/doc-meta-hackathon',
    'Gabyresina15/kinetix-ui': 'Gabyresina15/kinetix-os',
    'GautamPatil1/test-book-site': 'GautamPatil1/Booklith',
    'gino6178/meta_ai_hackathon': 'gino6178/serve-meta-hackathon',
    'Hedgeling/hedgeling-agent-platform': 'Hedgeling/hedgeling-meta-hackathon',
    'Hisernberg/meta-ai-hackathon-2026': 'Hisernberg/spanguard',
    'josephbolus/daas-meta-demo-video': 'josephbolus/devops-as-a-service',
    'jotika-meaw/tempu-tracker-client': 'jotika-meaw/tempu-tracker',
    'jotika-meaw/tempu-tracker-clean': 'jotika-meaw/tempu-tracker',
    'kaushishvineet/easylaunchad': 'kaushishvineet/easylaunch',
    'Kunal-Shahi/shipcube-data': 'Kunal-Shahi/shipcube',
    'mahamudulvisuals-debug/CoreAudit-12345': 'mahamudulvisuals-debug/CoreAudit',
    'mahamudulvisuals-debug/CoreAudit-': 'mahamudulvisuals-debug/CoreAudit',
    'NayilRArana/primordial-paradox-engine': 'NayilRArana/primordial-paradox',
    'NayilRArana/primordial-paradox-hackathon': 'NayilRArana/primordial-paradox',
    'newmachinesph/hoopscliniq-ai': 'newmachinesph/hoopscliniq-demo',
    'PearlLeeStudio/TheArtist': 'PearlLeeStudio/TheArtist-DAW',
    'PearlLeeStudio/TheArtist-Meta-Hackathon': 'PearlLeeStudio/TheArtist-DAW',
    'rajakumaranaap-rgb/makkal-ai': 'rajakumaranaap-rgb/makkal-agent-ai',
    'rick2x/hydrosight-meta': 'rick2x/hydrosight',
    'surfiniaburger/barred-muse': 'surfiniaburger/barred-hackathon-clean',
    'surfiniaburger/inert-silver': 'surfiniaburger/barred-hackathon-clean',
    'Techfrontiers/snapsell-ai': 'Techfrontiers/snapsell-ww',
    'vherediadepvops/prooflab-ai-meta-hackathon-2026': 'vherediadepvops/ProofLab-AI',
    'vibhortayal/meta-hackathon-research': 'vibhortayal/arya',
    'waleedmustafa971/forge-0-core': 'waleedmustafa971/forge-0-hackathon',
    'watt-mind/pii-guard-video': 'watt-mind/pii-guard',
    'YashRaj1240/spatialsentry0': 'YashRaj1240/spatialsentry',
}

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

def aggregate_multi_repo_groups(audited_map):
    # Also auto-discover same-owner multi-repo groups when a repo's README links to 2+ tracked sibling repos
    groups = {k: list(v) for k, v in MULTI_REPO_GROUPS.items()}
    all_assigned_siblings = {s for sibs in groups.values() for s in sibs}

    for full_name, audit in list(audited_map.items()):
        if full_name in groups or full_name in all_assigned_siblings:
            continue
        if '/' not in full_name:
            continue
        owner, repo = full_name.split('/', 1)
        excerpt = audit.get('readme_excerpt') or ''
        matches = set(re.findall(r'github\.com/' + re.escape(owner) + r'/([A-Za-z0-9_.-]+)', excerpt, re.I))
        siblings = []
        for m in sorted(matches):
            cand = f"{owner}/{m.rstrip('.')}"
            if cand.lower() != full_name.lower() and cand in audited_map and cand not in groups and cand not in all_assigned_siblings:
                siblings.append(cand)
        if len(siblings) >= 2:
            groups[full_name] = siblings
            all_assigned_siblings.update(siblings)

    for primary, siblings in groups.items():
        if primary not in audited_map:
            continue
        p_raw = audited_map[primary]
        # Preserve clean single-repo snapshot for idempotency across repeated rescore_all() calls
        if 'single_repo_snapshot' not in p_raw or p_raw.get('commits_in_window_single') != p_raw['single_repo_snapshot'].get('commits_in_window'):
            snap = {k: v for k, v in p_raw.items() if k not in ('single_repo_snapshot', 'is_multi_repo', 'repo_count', 'linked_repos')}
            p_raw['single_repo_snapshot'] = snap
        base_primary = dict(p_raw['single_repo_snapshot'])
        p_raw['commits_in_window_single'] = base_primary.get('commits_in_window', 0)

        members = [base_primary]
        linked_summary = [{
            "full_name": primary,
            "commits_in_window": base_primary.get("commits_in_window", 0),
            "prs_merged": base_primary.get("prs_merged", 0),
            "prs_total": base_primary.get("prs_total", 0),
            "has_tests": bool(base_primary.get("has_tests")),
            "has_docker": bool(base_primary.get("has_docker")),
        }]

        for sib in siblings:
            s_raw = audited_map.get(sib)
            if not s_raw or s_raw.get('status') == 'unavailable_or_deleted':
                continue
            s_RawClean = s_raw.get('single_repo_snapshot') or s_raw
            s_raw['merged_into'] = primary
            members.append(s_RawClean)
            linked_summary.append({
                "full_name": sib,
                "commits_in_window": s_RawClean.get("commits_in_window", 0),
                "prs_merged": s_RawClean.get("prs_merged", 0),
                "prs_total": s_RawClean.get("prs_total", 0),
                "has_tests": bool(s_RawClean.get("has_tests")),
                "has_docker": bool(s_RawClean.get("has_docker")),
            })

        if len(members) <= 1:
            continue

        # Aggregate numeric metrics across all repositories in the workspace
        for num_key in ('commits_in_window', 'commits_before_window', 'prs_total', 'prs_merged', 'disk_usage_kb', 'tree_entries_count', 'readme_bytes', 'stars', 'fork_count'):
            p_raw[num_key] = sum((m.get(num_key) or 0) for m in members)

        # Aggregate boolean engineering & Meta AI stack flags across the workspace
        for bool_key in (
            'has_docker', 'has_tests', 'has_src', 'has_ci',
            'has_pyproject', 'has_requirements', 'has_package_json',
            'meta_api_in_deps', 'baseten_in_deps', 'fireworks_in_deps', 'together_in_deps',
            'open_weights_tuning_in_deps', 'agent_framework_in_deps',
            'readme_cites_muse_spark', 'readme_cites_muse_wonder',
            'readme_cites_muse_glimmer', 'readme_cites_muse_code',
            'readme_cites_sam', 'readme_cites_meta_api'
        ):
            p_raw[bool_key] = any(bool(m.get(bool_key)) for m in members)

        # Combine video and live deployment URLs (deduplicated, preserving order)
        combined_videos = []
        combined_lives = []
        for m in members:
            for vu in (m.get('video_demo_urls') or []):
                if vu not in combined_videos:
                    combined_videos.append(vu)
            for lu in (m.get('live_deploy_urls') or []):
                if lu not in combined_lives:
                    combined_lives.append(lu)
        p_raw['video_demo_urls'] = combined_videos
        p_raw['has_video_demo'] = len(combined_videos) > 0
        p_raw['live_deploy_urls'] = combined_lives
        p_raw['has_live_deploy'] = len(combined_lives) > 0
        combined_readmes = []
        for idx_m, m in enumerate(members):
            r_name = (primary if idx_m == 0 else siblings[idx_m - 1]).split('/')[-1]
            ex = (m.get('readme_excerpt') or '').strip()
            if ex:
                combined_readmes.append(f"[{r_name}] {ex[:350]}")
        if combined_readmes:
            p_raw['readme_excerpt'] = "\n".join(combined_readmes)[:1600]
        p_raw['is_multi_repo'] = True
        p_raw['repo_count'] = len(members)
        p_raw['linked_repos'] = linked_summary

def rescore_all():
    if not os.path.exists(AUDIT_FILE):
        print(f"Error: {AUDIT_FILE} not found.")
        return

    with open(AUDIT_FILE) as f:
        audited_map = json.load(f)

    aggregate_multi_repo_groups(audited_map)
    with open(AUDIT_FILE, 'w') as f:
        json.dump(audited_map, f, indent=2)

    with open(INVENTORY_FILE) as f:
        inventory = json.load(f)

    inventory_by_name = {p['full_name']: p for p in inventory}

    scored_projects = []

    for full_name, audit in audited_map.items():
        if full_name.lower() in FALSE_POSITIVE_LOWER:
            continue
        if '/' in full_name:
            owner_p, repo_p = full_name.split('/', 1)
            if owner_p.lower() == repo_p.lower():
                continue
        if audit.get('merged_into') or full_name in SUPERSEDED_REPOS or (audit.get('renamed_to') and audit['renamed_to'] in audited_map):
            # Sibling repository already aggregated into its multi-repo primary entry or superseded by rename
            continue
        base_p = inventory_by_name.get(full_name, {})
        
        status = audit.get('status', 'audited')
        if status == 'unavailable_or_deleted':
            # Repo deleted, private or empty
            continue

        # Extract audited signals
        commits_in_window = audit.get('commits_in_window', 0)
        commits_before_window = audit.get('commits_before_window', 0)
        prs_total = audit.get('prs_total', 0)
        prs_merged = audit.get('prs_merged', 0)
        created_at = audit.get('created_at') or base_p.get('created_at') or ''
        is_preexisting = bool(audit.get('is_created_before_hackathon', False) or commits_before_window > 0 or (created_at and created_at < "2026-10-26T00:00:00Z"))

        # Filter out false positives:
        # 1. Repositories created/committed before Oct 26 with 0 commits during the hackathon window
        if commits_in_window == 0 and is_preexisting:
            continue
        # 2. Completely empty repositories with 0 commits and 0 files
        if commits_in_window == 0 and audit.get('tree_entries_count', 0) == 0:
            continue
        # 3. Long-standing pre-existing repositories (created before Oct 24) with >100 prior commits or no hackathon/Muse mention
        if created_at and created_at < "2026-10-24T00:00:00Z":
            comb_text = f"{base_p.get('description') or ''} {audit.get('readme_excerpt') or ''}".lower()
            has_hackathon_kw = any(k in comb_text for k in ['hackathon', 'muse', 'cerebral valley', 'dev.meta.ai'])
            if commits_before_window > 100 or not has_hackathon_kw:
                continue

        tree_count = audit.get('tree_entries_count', 0)
        has_docker = audit.get('has_docker', False)
        has_tests = audit.get('has_tests', False)
        has_src = audit.get('has_src', False)
        has_ci = audit.get('has_ci', False)
        readme_bytes = audit.get('readme_bytes', 0)

        # Meta tooling signals
        meta_api_in_deps = audit.get('meta_api_in_deps', False)
        baseten_in_deps = audit.get('baseten_in_deps', False)
        fireworks_in_deps = audit.get('fireworks_in_deps', False)
        together_in_deps = audit.get('together_in_deps', False)
        open_weights_tuning = audit.get('open_weights_tuning_in_deps', False)
        competitor_in_deps = audit.get('competitor_in_deps', False)
        agent_framework = audit.get('agent_framework_in_deps', False)

        readme_cites_muse_spark = audit.get('readme_cites_muse_spark', False)
        readme_cites_muse_wonder = audit.get('readme_cites_muse_wonder', False)
        readme_cites_muse_glimmer = audit.get('readme_cites_muse_glimmer', False)
        readme_cites_muse_code = audit.get('readme_cites_muse_code', False)
        readme_cites_sam = audit.get('readme_cites_sam', False)
        readme_cites_meta_api = audit.get('readme_cites_meta_api', False)

        def _valid_video(u):
            ul = u.lower()
            if any(bad in ul for bad in ['todo', 'xxxx', 'your_', 'your-', 'video_id', 'example.com', 'wikimedia.org', 'placeholder', 'watch?v=...', 'youtu.be/...']):
                return False
            if ('youtu.be/' in ul or 'watch?v=' in ul) and len(u.split('/')[-1].split('v=')[-1].split('&')[0]) < 10:
                return False
            return True

        video_urls = [u for u in (audit.get('video_demo_urls') or []) if _valid_video(u)]
        has_video_demo = len(video_urls) > 0
        has_live_deploy = audit.get('has_live_deploy', False)
        live_urls = audit.get('live_deploy_urls', [])

        # Incorporate verified deployment & model publication signals
        if full_name == 'watt-mind/pii-guard':
            has_live_deploy = True
            live_urls = ['https://guard.watt-mind.com/']
            huggingface_published = True
        else:
            huggingface_published = False

        raw_anti = audit.get('anti_project_flag') or base_p.get('anti_project_flag')
        if raw_anti and raw_anti != 'Clear':
            anti_project_flag = raw_anti
            is_disqualified = True
        else:
            anti_project_flag = 'Clear'
            is_disqualified = False

        # Check track (with explicit README/description override over LLM guess)
        track = base_p.get('track', 'Track 1: Build for Your World')
        domain = base_p.get('domain', 'General & Emerging Applications')

        readme_lower = (audit.get('readme_excerpt') or '').lower()
        desc_lower = (base_p.get('description') or '').lower()
        combined_text_lower = f"{readme_lower} {desc_lower}"
        has_explicit_ptf = 'push the frontier' in combined_text_lower or 'push-the-frontier' in combined_text_lower
        has_explicit_bfyw = 'build for your world' in combined_text_lower or 'build-for-your-world' in combined_text_lower
        if has_explicit_ptf and not has_explicit_bfyw:
            track = 'Push the Frontier'
        elif has_explicit_bfyw and not has_explicit_ptf:
            track = 'Build for Your World'
        tree_lower = [x.lower() for x in (audit.get('tree_entries') or [])]

        # Reproducible setup instructions signal (Judges run projects from repo setup instructions / .env.example / Makefile / Docker)
        has_setup_guide = (
            has_docker
            or any(k in tree_lower for k in ['.env.example', 'makefile', 'justfile', 'docker-compose.yml', 'compose.yaml'])
            or any(k in readme_lower for k in ['quickstart', 'getting started', 'setup', 'installation', 'npm install', 'pip install', 'uv sync', 'cargo run', 'make demo', 'docker compose', 'model_api_key', 'meta_api_key'])
        )

        # Quantitative evaluation / benchmark signal (Meta & CV guidance: "show the model working in your demo and back it up with benchmarks")
        has_eval_benchmarks = (
            any(k in tree_lower for k in ['eval', 'evals', 'benchmark', 'benchmarks'])
            or any(k in combined_text_lower for k in ['benchmark', 'eval/', 'f1', 'latency', 'p50', 'p95', 'ablation', 'accuracy', 'leak rate', 'over-masking'])
        )

        # True Meta Open-Weights ($10k Bonus Track: Muse Glimmer 30B / Muse Spark Open / LoRA / QLoRA / Distillation / HF published weights)
        true_open_weights = bool(
            huggingface_published
            or readme_cites_muse_glimmer
            or 'muse-spark-open' in combined_text_lower
            or 'muse spark open' in combined_text_lower
            or (open_weights_tuning and any(k in combined_text_lower for k in ['fine-tun', 'finetun', 'lora', 'qlora', 'peft', 'unsloth', 'distill', 'huggingface.co/', 'open-weight', 'open weight']))
        )

        # Count distinct Meta AI model families integrated
        meta_model_families = sum([
            bool(readme_cites_muse_spark or meta_api_in_deps or readme_cites_meta_api),
            bool(readme_cites_sam or 'sam 3' in combined_text_lower or 'sam-3' in combined_text_lower),
            bool(readme_cites_muse_wonder or 'muse image' in combined_text_lower or 'muse voice' in combined_text_lower),
            bool(readme_cites_muse_glimmer or 'muse-spark-open' in combined_text_lower or 'muse spark open' in combined_text_lower),
            bool(readme_cites_muse_code),
        ])

        # --- AUDITED STAGE 2 SCORING RUBRIC ---
        
        # 1. IMPACT (30% -> max 3.0 pts)
        impact = 1.0  # Base for active hackathon submission
        impact_items = [["Base hackathon repo", "+1.0"]]
        if 'Push the Frontier' in track:
            impact += 0.4  # Official hackathon track alignment (equalized across Track 1 & Track 2)
            impact_items.append(["Track 2 (Push the Frontier)", "+0.4"])
        else:
            impact += 0.4  # Official hackathon track alignment (equalized across Track 1 & Track 2)
            impact_items.append(["Track 1 (Build for Your World)", "+0.4"])
        if domain in [
            'Developer Tooling, Infra & Security',
            'Robotics, IoT & Manufacturing',
            'Autonomous Agents & Workflow Automation',
            'Healthcare, Civic Tech & Sustainability',
            'Enterprise Security & Privacy',
            'Developer Infrastructure',
            'Robotics & Hardware',
            'Bioinformatics & Materials',
        ]:
            impact += 0.4
            impact_items.append(["High-impact domain", "+0.4"])
        elif domain in [
            'Multimodal Vision & Video (SAM / Vision)',
            'Voice, Speech & Audio AI',
            'Education & Knowledge Systems',
            'Legal & Compliance',
            'Finance, Crypto & Web3',
            'Business, Sales & Commerce',
            'Developer Tools & Agents',
            'Finance & Compliance',
            'Healthcare & Life Sciences',
        ]:
            impact += 0.3
            impact_items.append(["Domain alignment", "+0.3"])
        else:
            impact += 0.2
            impact_items.append(["General domain", "+0.2"])
        if has_eval_benchmarks:
            impact += 0.3  # Quantitative evaluation & benchmark evidence
            impact_items.append(["Eval & benchmark proof", "+0.3"])
        if has_docker:
            impact += 0.4  # Production deployment ready
            impact_items.append(["Docker packaging", "+0.4"])
        if tree_count > 10:
            impact += 0.2  # Comprehensive multi-module project scope
            impact_items.append(["Multi-module scope (>10 files)", "+0.2"])
        if readme_bytes > 5000:
            impact += 0.3  # Thorough problem formulation & documentation
            impact_items.append(["Detailed problem docs (>5 KB)", "+0.3"])
        if round(impact, 2) > 3.0:
            impact_items.append(["Pillar cap", "max 3.0"])
        impact = round(min(3.0, impact), 2)

        # 2. META TOOLING (25% -> max 2.5 pts)
        meta_tooling = 0.5  # Base
        meta_items = [["Base", "+0.5"]]
        if meta_api_in_deps or readme_cites_meta_api:
            meta_tooling += 0.5
            meta_items.append(["Meta Model API / SDK", "+0.5"])
        if readme_cites_muse_spark:
            meta_tooling += 0.3
            meta_items.append(["Muse Spark integration", "+0.3"])
        if readme_cites_muse_wonder or readme_cites_sam or 'muse image' in combined_text_lower or 'muse voice' in combined_text_lower:
            meta_tooling += 0.3
            meta_items.append(["SAM 3.1 / Multimodal Muse", "+0.3"])
        if meta_model_families >= 3:
            meta_tooling += 0.2  # Multi-model pipeline (3+ distinct Meta models working together)
            meta_items.append(["3+ Meta model pipeline", "+0.2"])
        if baseten_in_deps or fireworks_in_deps or together_in_deps:
            meta_tooling += 0.2  # Official inference partner
            meta_items.append(["Partner inference infra", "+0.2"])
        # $10k Best Build on Meta Open-Weight Models (Muse Glimmer / Muse Spark Open / fine-tuned weights)
        if true_open_weights:
            meta_tooling += 0.5
            meta_items.append(["Open-weights / fine-tuning", "+0.5"])
        if huggingface_published or 'huggingface.co/' in combined_text_lower:
            meta_tooling += 0.3  # Published open-weight model/dataset on Hugging Face Hub
            meta_items.append(["Published HF Hub weights", "+0.3"])
        # Penalty for non-Meta runtime models with zero Meta model integration
        if competitor_in_deps and meta_model_families == 0 and not true_open_weights:
            meta_tooling -= 0.6
            meta_items.append(["Non-Meta runtime SDK only", "-0.6"])
        if round(meta_tooling, 2) > 2.5:
            meta_items.append(["Pillar cap", "max 2.5"])
        elif round(meta_tooling, 2) < 0.2:
            meta_items.append(["Pillar floor", "min 0.2"])
        meta_tooling = round(max(0.2, min(2.5, meta_tooling)), 2)

        # 3. TECH DEPTH (20% -> max 2.0 pts)
        tech_depth = 0.3  # Base
        tech_items = [["Base", "+0.3"]]
        if commits_in_window >= 50:
            tech_depth += 0.6  # High iterative commit cadence
            tech_items.append([f"50+ window commits ({commits_in_window})", "+0.6"])
        elif commits_in_window >= 15:
            tech_depth += 0.4
            tech_items.append([f"15+ window commits ({commits_in_window})", "+0.4"])
        elif commits_in_window >= 5:
            tech_depth += 0.2
            tech_items.append([f"5+ window commits ({commits_in_window})", "+0.2"])
        elif commits_in_window == 0:
            tech_depth -= 0.3  # No commits during hackathon
            tech_items.append(["0 commits in window", "-0.3"])

        if has_tests:
            tech_depth += 0.3
            tech_items.append(["Automated test suite", "+0.3"])
        if has_src:
            tech_depth += 0.3
            tech_items.append(["Modular src/ architecture", "+0.3"])
        if agent_framework or has_eval_benchmarks:
            tech_depth += 0.2
            tech_items.append(["Agent / eval harness", "+0.2"])
        if has_ci:
            tech_depth += 0.2
            tech_items.append(["Automated CI workflow", "+0.2"])
        if prs_merged >= 3 or (prs_total >= 5 and has_ci):
            tech_depth += 0.2  # Structured PR workflow / review discipline
            tech_items.append([f"PR review workflow ({prs_merged or prs_total} PRs)", "+0.2"])

        # Penalty for stale pre-existing codebases or repos where pre-hackathon commits dominate
        if is_preexisting and commits_in_window <= 2:
            tech_depth -= 0.5
            tech_items.append(["Pre-existing repo (<=2 commits)", "-0.5"])
        elif commits_before_window > commits_in_window and commits_before_window >= 10:
            tech_depth -= 0.3
            tech_items.append([f"Pre-Oct 26 commits dominate ({commits_before_window})", "-0.3"])

        if round(tech_depth, 2) > 2.0:
            tech_items.append(["Pillar cap", "max 2.0"])
        elif round(tech_depth, 2) < 0.2:
            tech_items.append(["Pillar floor", "min 0.2"])
        tech_depth = round(max(0.2, min(2.0, tech_depth)), 2)

        # 4. DEMO COMPLETENESS & REPRODUCIBILITY (25% -> max 2.5 pts)
        demo = 0.4  # Base
        demo_items = [["Base", "+0.4"]]
        if has_video_demo:
            demo += 1.1  # Verified 3-minute video walkthrough (YouTube/Loom/Vimeo)
            demo_items.append(["Video walkthrough", "+1.1"])
        if has_setup_guide:
            demo += 0.4  # Reproducible local setup instructions / .env.example / Docker for judges
            demo_items.append(["Reproducible setup guide", "+0.4"])
        if has_live_deploy:
            demo += 0.4  # Live hosted working deployment
            demo_items.append(["Live web deployment", "+0.4"])
        if readme_bytes > 6000:
            demo += 0.2  # Detailed visual walkthrough / architecture / benchmark charts
            demo_items.append(["Visual docs & diagrams (>6 KB)", "+0.2"])
        
        # If neither video demo nor live app exists, cap demo at 1.0/2.5
        if not has_video_demo and not has_live_deploy:
            if round(demo, 2) > 1.0:
                demo_items.append(["No video or live app cap", "max 1.0"])
            demo = min(1.0, demo)
        else:
            if round(demo, 2) > 2.5:
                demo_items.append(["Pillar cap", "max 2.5"])
            demo = min(2.5, demo)
        demo = round(demo, 2)

        # Total score is always the exact sum of the 4 pillars (no regex-based 0.4x disqualification penalty)
        is_disqualified = False
        anti_project_flag = 'Clear'
        total_score = round(impact + meta_tooling + tech_depth + demo, 2)

        record = {
            "full_name": full_name,
            "html_url": f"https://github.com/{full_name}",
            "track": track,
            "domain": domain,
            "summary": base_p.get('summary') or (base_p.get('description') or '')[:140],
            "readme_summary": base_p.get('readme_summary') or base_p.get('summary') or (base_p.get('description') or '')[:240],
            "tech_highlights": base_p.get('tech_highlights') or [],
            "created_at": audit.get('created_at'),
            "is_multi_repo": bool(audit.get('is_multi_repo', False)),
            "repo_count": audit.get('repo_count', 1),
            "linked_repos": audit.get('linked_repos', []),
            "commits_in_window": commits_in_window,
            "commits_before_window": commits_before_window,
            "prs_total": prs_total,
            "prs_merged": prs_merged,
            "is_preexisting": is_preexisting,
            "has_docker": has_docker,
            "has_tests": has_tests,
            "has_src": has_src,
            "has_ci": has_ci,
            "meta_api_verified": meta_api_in_deps or readme_cites_meta_api,
            "partner_infra": "Baseten" if baseten_in_deps else ("Fireworks" if fireworks_in_deps else ("Together" if together_in_deps else "Direct")),
            "open_weights_tuning": true_open_weights,
            "has_eval_benchmarks": has_eval_benchmarks,
            "has_setup_guide": has_setup_guide,
            "has_video_demo": has_video_demo,
            "video_urls": video_urls,
            "has_live_deploy": has_live_deploy,
            "live_urls": live_urls,
            "anti_project_flag": anti_project_flag,
            "is_disqualified": is_disqualified,
            "stars": audit.get('stars', 0),
            "score_impact": round(impact, 2),
            "score_meta_tooling": round(meta_tooling, 2),
            "score_tech_depth": round(tech_depth, 2),
            "score_demo": round(demo, 2),
            "score_total": total_score,
            "score_breakdown": {
                "impact": impact_items,
                "meta": meta_items,
                "tech": tech_items,
                "demo": demo_items,
            },
        }
        scored_projects.append(record)

    # Sort descending by total score, then commits_in_window, then stars
    scored_projects.sort(key=lambda x: (x['score_total'], x['commits_in_window'], x['stars']), reverse=True)

    # Assign ranks
    for rank, p in enumerate(scored_projects, 1):
        p['rank'] = rank

    with open(AUDITED_INVENTORY_FILE, 'w') as f:
        json.dump(scored_projects, f, indent=2)

    # Generate CSV
    import csv
    fieldnames = [
        'rank', 'full_name', 'score_total', 'track', 'domain',
        'score_impact', 'score_meta_tooling', 'score_tech_depth', 'score_demo',
        'commits_in_window', 'commits_before_window', 'prs_merged', 'prs_total',
        'is_preexisting', 'has_docker', 'has_tests', 'has_src', 'has_ci',
        'meta_api_verified', 'partner_infra', 'open_weights_tuning',
        'has_video_demo', 'has_live_deploy', 'is_disqualified', 'anti_project_flag',
        'stars', 'html_url'
    ]
    with open(CSV_OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(scored_projects)

    print(f"Audited scoring complete! {len(scored_projects)} projects ranked and saved to {AUDITED_INVENTORY_FILE} and {CSV_OUTPUT_FILE}")
    print("\n--- TOP 10 AUDITED CONTENDERS ---")
    for p in scored_projects[:10]:
        print(f"#{p['rank']} [{p['score_total']}/10] {p['full_name']} | Track: {p['track']} | Commits: {p['commits_in_window']} | Video: {p['has_video_demo']} | Docker: {p['has_docker']}")

if __name__ == '__main__':
    rescore_all()
