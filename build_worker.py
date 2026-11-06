import json
import os
import base64
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--output-dir', default='wattmind-artifacts', help='Directory for the generated worker')
WORKER_DIR = parser.parse_args().output_dir
SRC_DIR = os.path.join(WORKER_DIR, 'src')
os.makedirs(SRC_DIR, exist_ok=True)

# Read HTML report
with open('meta_hackathon_competitor_analysis_report.html') as f:
    report_html = f.read()

# Read Submission Checklist HTML
checklist_html = ""
if os.path.exists('meta_hackathon_submission_checklist.html'):
    with open('meta_hackathon_submission_checklist.html') as f:
        checklist_html = f.read()

# Read projects JSON
with open('projects_inventory_audited.json') as f:
    projects_json_str = f.read()
projects_json = json.loads(projects_json_str)
repo_count = len(projects_json)

# Read projects CSV
with open('projects_inventory_audited.csv') as f:
    projects_csv_str = f.read()

# Read OG Image as base64
with open('og-image.png', 'rb') as f:
    og_image_b64 = base64.b64encode(f.read()).decode('ascii')

og_checklist_b64 = og_image_b64
if os.path.exists('og-checklist.png'):
    with open('og-checklist.png', 'rb') as f:
        og_checklist_b64 = base64.b64encode(f.read()).decode('ascii')

# 1. Write wrangler.jsonc
wrangler_config = {
    "$schema": "node_modules/wrangler/config-schema.json",
    "name": "wattmind-artifacts",
    "main": "src/index.js",
    "compatibility_date": "2026-10-01",
    "compatibility_flags": ["nodejs_compat"],
    "routes": [
        {
            "pattern": "artifacts.watt-mind.com",
            "custom_domain": True
        }
    ]
}

with open(os.path.join(WORKER_DIR, 'wrangler.jsonc'), 'w') as f:
    json.dump(wrangler_config, f, indent=2)

# 2. Write package.json
package_json = {
    "name": "wattmind-artifacts",
    "version": "1.0.0",
    "description": "Watt Mind Artifacts & Intelligence Reports Portal",
    "main": "src/index.js",
    "scripts": {
        "deploy": "wrangler deploy",
        "dev": "wrangler dev"
    }
}

with open(os.path.join(WORKER_DIR, 'package.json'), 'w') as f:
    json.dump(package_json, f, indent=2)

# 3. Write data modules
with open(os.path.join(SRC_DIR, 'report_html.js'), 'w') as f:
    f.write('export const REPORT_HTML = ' + json.dumps(report_html) + ';\n')

with open(os.path.join(SRC_DIR, 'checklist_html.js'), 'w') as f:
    f.write('export const CHECKLIST_HTML = ' + json.dumps(checklist_html or report_html) + ';\n')

with open(os.path.join(SRC_DIR, 'projects_data.js'), 'w') as f:
    f.write('export const PROJECTS_JSON_STR = ' + json.dumps(projects_json_str) + ';\n')
    f.write('export const PROJECTS_CSV_STR = ' + json.dumps(projects_csv_str) + ';\n')
    f.write(f'export const REPO_COUNT = {repo_count};\n')

with open(os.path.join(SRC_DIR, 'og_image_data.js'), 'w') as f:
    f.write('export const OG_IMAGE_B64 = ' + json.dumps(og_image_b64) + ';\n')
    f.write('export const OG_CHECKLIST_B64 = ' + json.dumps(og_checklist_b64) + ';\n')

has_buzz_report = False
has_push_frontier = False
has_push_frontier_scene = False
has_push_frontier_ink = False

# 4. Write worker index.js
worker_code = """
import { REPORT_HTML } from './report_html.js';
import { CHECKLIST_HTML } from './checklist_html.js';
import { PROJECTS_JSON_STR, PROJECTS_CSV_STR, REPO_COUNT } from './projects_data.js';
import { OG_IMAGE_B64, OG_CHECKLIST_B64 } from './og_image_data.js';
""" + ("import { BUZZ_K3S_REPORT_HTML, BUZZ_K3S_OG_B64 } from './buzz_k3s_report.js';\n" if has_buzz_report else "") + """
function base64ToUint8Array(base64) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

const ogImageBytes = base64ToUint8Array(OG_IMAGE_B64);
const ogChecklistBytes = base64ToUint8Array(OG_CHECKLIST_B64);
""" + ("const buzzK3sOgBytes = base64ToUint8Array(BUZZ_K3S_OG_B64);\n" if has_buzz_report else "") + """
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname.replace(/\\/$/, '') || '/';

    // CORS headers for API consumers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Healthcheck
    if (pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok', service: 'wattmind-artifacts', timestamp: new Date().toISOString() }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }

    // Favicon
    if (pathname === '/favicon.ico' || pathname === '/favicon.svg' || pathname === '/meta-hackathon-2026/favicon.ico') {
      return new Response('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#111916"/><path d="M8 22L13 10L16 17L19 10L24 22" stroke="#4fdbc8" stroke-width="2.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>', {
        headers: {
          'Content-Type': 'image/svg+xml',
          'Cache-Control': 'public, max-age=86400',
          ...corsHeaders
        }
      });
    }

    // OG Images (Root and Subfolder)
    if (pathname === '/og-image.png' || pathname === '/meta-hackathon-2026/og-image.png') {
      return new Response(ogImageBytes, {
        headers: {
          'Content-Type': 'image/png',
          'Cache-Control': 'public, max-age=86400, s-maxage=86400',
          ...corsHeaders
        }
      });
    }

    if (pathname === '/og-checklist.png' || pathname === '/meta-hackathon-2026/og-checklist.png') {
      return new Response(ogChecklistBytes, {
        headers: {
          'Content-Type': 'image/png',
          'Cache-Control': 'public, max-age=86400, s-maxage=86400',
          ...corsHeaders
        }
      });
    }

    // Data APIs (Both subfolder and root paths supported)
    if (
      pathname === '/meta-hackathon-2026/projects.json' ||
      pathname === '/projects.json' ||
      pathname === '/api/projects.json'
    ) {
      return new Response(PROJECTS_JSON_STR, {
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'Cache-Control': 'public, max-age=3600',
          ...corsHeaders
        }
      });
    }

    if (
      pathname === '/meta-hackathon-2026/projects.csv' ||
      pathname === '/projects.csv' ||
      pathname === '/data/projects.csv'
    ) {
      return new Response(PROJECTS_CSV_STR, {
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'inline; filename="meta_hackathon_competitors_2026.csv"',
          'Cache-Control': 'public, max-age=3600',
          ...corsHeaders
        }
      });
    }

    // Root '/' redirect to the dedicated artifact subfolder '/meta-hackathon-2026/'
    // Includes full OG tags in the 302 payload for scrapers/bots that do not follow 302 Location headers
    if (pathname === '/') {
      const redirectHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=/meta-hackathon-2026/">
  <link rel="canonical" href="https://artifacts.watt-mind.com/meta-hackathon-2026/">
  <title>Meta Global AI Hackathon 2026 — Unofficial Project Directory</title>
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Watt Mind (Unofficial Community Tracker)">
  <meta property="og:title" content="Meta Global AI Hackathon 2026 — Unofficial Project Directory">
  <meta property="og:description" content="Unofficial community tracker of ${REPO_COUNT} public hackathon repositories — searchable directory, tech stack telemetry, and automated repo signals.">
  <meta property="og:url" content="https://artifacts.watt-mind.com/meta-hackathon-2026/">
  <meta property="og:image" content="https://artifacts.watt-mind.com/meta-hackathon-2026/og-image.png?v=4">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:type" content="image/png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Meta Global AI Hackathon 2026 — Unofficial Project Directory">
  <meta name="twitter:description" content="Unofficial community tracker of ${REPO_COUNT} public hackathon repositories — searchable directory, tech stack telemetry, and automated repo signals.">
  <meta name="twitter:image" content="https://artifacts.watt-mind.com/meta-hackathon-2026/og-image.png?v=4">
  <meta name="theme-color" content="#4fdbc8">
  <style>
    body { font-family: sans-serif; background: #0e1513; color: #dde4e1; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    a { color: #4fdbc8; text-decoration: none; }
  </style>
</head>
<body>
  <p>Redirecting to <a href="/meta-hackathon-2026/">Meta Global AI Hackathon 2026 Analysis</a>...</p>
</body>
</html>`;
      return new Response(redirectHtml, {
        status: 302,
        headers: {
          'Location': '/meta-hackathon-2026/',
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'no-cache',
          ...corsHeaders
        }
      });
    }

    // Subfolder Artifact: '/meta-hackathon-2026' or '/meta-hackathon-2026/'
    if (
      pathname === '/meta-hackathon-2026' ||
      pathname === '/meta-hackathon-2026/' ||
      pathname === '/meta-hackathon-2026/index.html' ||
      pathname === '/meta-hackathon-2026/report.html' ||
      pathname === '/reports/meta-hackathon-2026'
    ) {
      return new Response(REPORT_HTML, {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'public, max-age=3600',
          ...corsHeaders
        }
      });
    }

    // Submission & Judging Readiness Checklist
    if (
      pathname === '/meta-hackathon-2026/checklist' ||
      pathname === '/meta-hackathon-2026/checklist.html' ||
      pathname === '/meta-hackathon-2026/submission-checklist' ||
      pathname === '/checklist'
    ) {
      return new Response(CHECKLIST_HTML, {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'public, max-age=3600',
          ...corsHeaders
        }
      });
    }
""" + ("""
    // Legacy public aliases redirect into the Cloudflare-Access-protected /private/ subtree
    if (
      pathname === '/buzz-k3s-architecture' ||
      pathname === '/buzz-k3s-architecture/index.html' ||
      pathname === '/buzz-k3s-architecture/report.html' ||
      pathname === '/buzz-k3s-architecture/og-image.png' ||
      pathname === '/buzz-k3s' ||
      pathname === '/buzz-agents'
    ) {
      const target = pathname.endsWith('/og-image.png')
        ? '/private/buzz-k3s-architecture/og-image.png'
        : '/private/buzz-k3s-architecture/';
      return Response.redirect(`${url.origin}${target}`, 302);
    }

    // Protected '/private/*' subtree (enforced at edge by Cloudflare Zero Trust Access + verified in-Worker)
    if (pathname === '/private' || pathname.startsWith('/private/')) {
      const cfAccessJwt = request.headers.get('Cf-Access-Jwt-Assertion');
      const cfAccessEmail = request.headers.get('Cf-Access-Authenticated-User-Email');
      if (!cfAccessJwt && !cfAccessEmail) {
        return new Response('403 Forbidden // Cloudflare Zero Trust Access authentication required for /private/*', {
          status: 403,
          headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' }
        });
      }

      if (pathname === '/private/buzz-k3s-architecture/og-image.png') {
        return new Response(buzzK3sOgBytes, {
          headers: {
            'Content-Type': 'image/png',
            'Cache-Control': 'private, max-age=3600',
          }
        });
      }

      if (
        pathname === '/private' ||
        pathname === '/private/buzz-k3s-architecture' ||
        pathname === '/private/buzz-k3s-architecture/index.html' ||
        pathname === '/private/buzz-k3s-architecture/report.html' ||
        pathname === '/private/buzz-k3s' ||
        pathname === '/private/buzz-agents'
      ) {
        return new Response(BUZZ_K3S_REPORT_HTML, {
          headers: {
            'Content-Type': 'text/html; charset=utf-8',
            'Cache-Control': 'private, no-cache',
          }
        });
      }
    }
""" if has_buzz_report else "") + """
    // 404 handler with Watt Mind styled fallback
    return new Response(
      `<!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>Watt Mind Artifacts - Not Found</title>
        <style>
          body { font-family: sans-serif; background: #0e1513; color: #dde4e1; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
          h1 { color: #4fdbc8; font-size: 32px; margin-bottom: 8px; }
          a { color: #4fdbc8; text-decoration: none; border-bottom: 1px solid #4fdbc8; }
        </style>
      </head>
      <body>
        <h1>404 // Artifact Not Found</h1>
        <p>Return to <a href="/">Meta Global AI Hackathon 2026 Report</a></p>
      </body>
      </html>`,
      {
        status: 404,
        headers: { 'Content-Type': 'text/html; charset=utf-8', ...corsHeaders }
      }
    );
  }
};
"""


if has_push_frontier:
    FRONTIER_ROUTES = '''
    // Push-the-Frontier artifacts (hand-maintained modules in src/)
    if (
      pathname === '/push-the-frontier' ||
      pathname === '/push-the-frontier/' ||
      pathname === '/push-the-frontier/index.html' ||
      pathname === '/push-the-frontier/frontier-wall.html'
    ) {
      return new Response(PUSH_FRONTIER_HTML, {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'public, max-age=300',
          ...corsHeaders
        }
      });
    }

    if (
      pathname === '/push-the-frontier/tree.html' ||
      pathname === '/push-the-frontier/tree'
    ) {
      return new Response(PUSH_FRONTIER_TREE_HTML, {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'public, max-age=300',
          ...corsHeaders
        }
      });
    }

    if (
      pathname === '/push-the-frontier/og-image.png' ||
      pathname === '/push-the-frontier/push-the-frontier-og.png'
    ) {
      return new Response(base64ToUint8Array(PUSH_FRONTIER_OG_B64), {
        headers: {
          'Content-Type': 'image/png',
          'Cache-Control': 'public, max-age=86400',
          ...corsHeaders
        }
      });
    }

'''
    worker_code = worker_code.replace(
        "function base64ToUint8Array",
        "import { PUSH_FRONTIER_HTML } from './push_frontier_html.js';\n"
        "import { PUSH_FRONTIER_OG_B64 } from './push_frontier_og.js';\n"
        "import { PUSH_FRONTIER_TREE_HTML } from './push_frontier_tree_html.js';\n"
        "function base64ToUint8Array",
        1,
    )
    assert 'push_frontier_html.js' in worker_code, 'import injection failed'
    worker_code = worker_code.replace('    // 404 handler', FRONTIER_ROUTES + '    // 404 handler', 1)
    assert '/push-the-frontier' in worker_code, 'route injection failed'


if has_push_frontier_scene:
    FRONTIER_SCENE_ROUTES = '''
    // Push-the-Frontier: beat-reactive scene (frontier.html + Bad Times mp3/JSON)
    if (
      pathname === '/push-the-frontier/frontier.html' ||
      pathname === '/push-the-frontier/frontier'
    ) {
      return new Response(PUSH_FRONTIER_SCENE_HTML, {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'public, max-age=300',
          ...corsHeaders
        }
      });
    }

    if (pathname === '/push-the-frontier/Bad-Times-Extended-Version-qSeSMPRCIUc.json') {
      return new Response(PUSH_FRONTIER_BEATS_JSON, {
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'Cache-Control': 'public, max-age=3600',
          ...corsHeaders
        }
      });
    }

    if (pathname === '/push-the-frontier/Bad-Times-Extended-Version-qSeSMPRCIUc.mp3') {
      const bytes = base64ToUint8Array(PUSH_FRONTIER_MP3_B64);
      const total = bytes.length;
      const range = request.headers.get('Range');
      const m = range && range.match(/bytes=(\d*)-(\d*)/);
      if (m) {
        let start = m[1] === '' ? total - parseInt(m[2], 10) : parseInt(m[1], 10);
        let end = m[2] === '' || m[1] === '' ? total - 1 : Math.min(parseInt(m[2], 10), total - 1);
        start = Math.max(0, start);
        if (start > end || start >= total) {
          return new Response(null, { status: 416, headers: { 'Content-Range': `bytes */${total}`, ...corsHeaders } });
        }
        return new Response(bytes.subarray(start, end + 1), {
          status: 206,
          headers: {
            'Content-Type': 'audio/mpeg',
            'Content-Range': `bytes ${start}-${end}/${total}`,
            'Content-Length': String(end - start + 1),
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'public, max-age=86400',
            ...corsHeaders
          }
        });
      }
      return new Response(bytes, {
        headers: {
          'Content-Type': 'audio/mpeg',
          'Content-Length': String(total),
          'Accept-Ranges': 'bytes',
          'Cache-Control': 'public, max-age=86400',
          ...corsHeaders
        }
      });
    }
    if (pathname === '/push-the-frontier/frontier-og.jpg') {
      return new Response(base64ToUint8Array(PUSH_FRONTIER_SCENE_OG_B64), {
        headers: {
          'Content-Type': 'image/jpeg',
          'Cache-Control': 'public, max-age=86400',
          ...corsHeaders
        }
      });
    }
'''
    worker_code = worker_code.replace(
        "function base64ToUint8Array",
        "import { PUSH_FRONTIER_SCENE_HTML } from './push_frontier_scene_html.js';\n"
        "import { PUSH_FRONTIER_BEATS_JSON } from './push_frontier_beats.js';\n"
        "import { PUSH_FRONTIER_MP3_B64 } from './push_frontier_mp3.js';\n"
        "import { PUSH_FRONTIER_SCENE_OG_B64 } from './push_frontier_scene_og.js';\n"
        "function base64ToUint8Array",
        1,
    )
    assert 'push_frontier_mp3.js' in worker_code, 'scene import injection failed'
    worker_code = worker_code.replace('    // 404 handler', FRONTIER_SCENE_ROUTES + '    // 404 handler', 1)
    assert '/push-the-frontier/frontier' in worker_code, 'scene route injection failed'


if has_push_frontier_ink:
    FRONTIER_INK_ROUTES = '''
    // Push-the-Frontier: Xenolinguistic Ink Swarm (ink.html + ink-og.jpg)
    if (
      pathname === '/push-the-frontier/ink.html' ||
      pathname === '/push-the-frontier/ink' ||
      pathname === '/ink'
    ) {
      return new Response(PUSH_FRONTIER_INK_HTML, {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'public, max-age=300',
          ...corsHeaders
        }
      });
    }
    if (pathname === '/push-the-frontier/ink-og.jpg') {
      return new Response(base64ToUint8Array(PUSH_FRONTIER_INK_OG_B64), {
        headers: {
          'Content-Type': 'image/jpeg',
          'Cache-Control': 'public, max-age=86400',
          ...corsHeaders
        }
      });
    }
'''
    worker_code = worker_code.replace(
        "function base64ToUint8Array",
        "import { PUSH_FRONTIER_INK_HTML } from './push_frontier_ink_html.js';\n"
        "import { PUSH_FRONTIER_INK_OG_B64 } from './push_frontier_ink_og.js';\n"
        "function base64ToUint8Array",
        1,
    )
    assert 'push_frontier_ink_html.js' in worker_code, 'ink import injection failed'
    worker_code = worker_code.replace('    // 404 handler', FRONTIER_INK_ROUTES + '    // 404 handler', 1)
    assert '/push-the-frontier/ink' in worker_code, 'ink route injection failed'

with open(os.path.join(SRC_DIR, 'index.js'), 'w') as f:
    f.write(worker_code)

print("Worker generated in", WORKER_DIR)


