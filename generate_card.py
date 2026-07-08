#!/usr/bin/env python3
"""
generate_card.py
Fetches live GitHub stats and renders a terminal / holographic HUD style SVG,
matching the "scan complete" aesthetic. Output: profile-card.svg

Env vars required:
  GH_USERNAME   - your GitHub username (e.g. ghozt-zx)
  GH_TOKEN      - a GitHub token (repo/read:user scope) - GITHUB_TOKEN in Actions works fine
"""

import os
import sys
import datetime
import requests

USERNAME = os.environ.get("GH_USERNAME")
TOKEN = os.environ.get("GH_TOKEN")

if not USERNAME or not TOKEN:
    sys.exit("Missing GH_USERNAME or GH_TOKEN environment variables")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

API = "https://api.github.com"


def gh_get(path, params=None):
    r = requests.get(f"{API}{path}", headers=HEADERS, params=params or {})
    r.raise_for_status()
    return r.json()


def gh_graphql(query, variables):
    r = requests.post(
        f"{API}/graphql",
        headers=HEADERS,
        json={"query": query, "variables": variables},
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def fetch_stats():
    user = gh_get(f"/users/{USERNAME}")

    # paginate through repos to total stars + find top language
    repos = []
    page = 1
    while True:
        batch = gh_get(
            f"/users/{USERNAME}/repos",
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        if not batch:
            break
        repos.extend(batch)
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    lang_count = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            lang_count[lang] = lang_count.get(lang, 0) + 1
    top_lang = max(lang_count, key=lang_count.get) if lang_count else "UNKNOWN"
    lang_breakdown = sorted(lang_count.items(), key=lambda kv: kv[1], reverse=True)[:5]

    recent_repos = sorted(
        repos, key=lambda r: r.get("pushed_at") or "", reverse=True
    )[:5]
    recent_repo_names = [r["name"] for r in recent_repos]

    # contribution calendar + current streak via GraphQL
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { date contributionCount }
            }
          }
        }
      }
    }
    """
    gql = gh_graphql(query, {"login": USERNAME})
    weeks = gql["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    total_contribs = gql["user"]["contributionsCollection"]["contributionCalendar"][
        "totalContributions"
    ]

    # current streak: walk backwards from today
    streak = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            streak += 1
        else:
            date = datetime.date.fromisoformat(d["date"])
            if date == datetime.date.today():
                continue
            break

    joined = datetime.datetime.strptime(
        user["created_at"], "%Y-%m-%dT%H:%M:%SZ"
    ).year

    return {
        "username": USERNAME,
        "name": user.get("name") or USERNAME,
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "total_stars": total_stars,
        "top_lang": top_lang.upper(),
        "lang_breakdown": lang_breakdown,
        "recent_repos": recent_repo_names,
        "total_contribs": total_contribs,
        "streak": streak,
        "joined": joined,
    }


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 760, 320
BG = "#070c0b"
PANEL = "#0d1613"
LINE = "#4a6b60"
TEXT_DIM = "#5f8a7d"
TEXT_BRIGHT = "#cdf5e6"
ACCENT = "#8ffcd0"


def bracket_corner(x, y, size, flip_x=1, flip_y=1):
    dx = size * flip_x
    dy = size * flip_y
    return f'<path d="M{x} {y+dy} L{x} {y} L{x+dx} {y}" stroke="{ACCENT}" stroke-width="2" fill="none"/>'


def progress_bar(x, y, w, h, pct):
    filled = int(w * pct)
    return f'''
    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{LINE}" stroke-width="1"/>
    <rect x="{x}" y="{y}" width="{filled}" height="{h}" fill="{ACCENT}" opacity="0.85"/>
    '''


def render_svg(s):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    years_active = datetime.datetime.utcnow().year - s["joined"]
    contrib_pct = min(s["total_contribs"] / 3000, 1.0)  # scale bar, tweak as you like

    corners = "".join([
        bracket_corner(14, 14, 22, 1, 1),
        bracket_corner(WIDTH - 14, 14, 22, -1, 1),
        bracket_corner(14, HEIGHT - 14, 22, 1, -1),
        bracket_corner(WIDTH - 14, HEIGHT - 14, 22, -1, -1),
    ])

    rows = [
        ("PUBLIC REPOS", s["public_repos"]),
        ("TOTAL STARS", s["total_stars"]),
        ("FOLLOWERS", s["followers"]),
        ("FOLLOWING", s["following"]),
        ("CURRENT STREAK", f'{s["streak"]} DAYS'),
        ("TOP LANGUAGE", s["top_lang"]),
        ("ACTIVE SINCE", s["joined"]),
    ]

    row_y = 128
    row_gap = 22
    rows_svg = ""
    for label, val in rows:
        rows_svg += f'''
        <text x="40" y="{row_y}" font-family="Consolas, monospace" font-size="12" fill="{TEXT_DIM}">&gt; {label}</text>
        <text x="330" y="{row_y}" font-family="Consolas, monospace" font-size="12" fill="{TEXT_BRIGHT}" text-anchor="end">{val}</text>
        '''
        row_y += row_gap

    svg = f'''<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="4" fill="{BG}"/>
      <line x1="0" y1="0" x2="4" y2="0" stroke="#0f1a17" stroke-width="1"/>
    </pattern>
    <filter id="glow">
      <feGaussianBlur stdDeviation="1.4" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#scan)" opacity="0.35"/>
  <rect x="1" y="1" width="{WIDTH-2}" height="{HEIGHT-2}" fill="none" stroke="{LINE}" stroke-width="1" opacity="0.6"/>

  {corners}

  <!-- header -->
  <text x="40" y="46" font-family="Consolas, monospace" font-size="14" fill="{ACCENT}" filter="url(#glow)">&gt; SCAN COMPLETE // USER: {s["username"].upper()}</text>
  <text x="{WIDTH-40}" y="46" font-family="Consolas, monospace" font-size="10" fill="{TEXT_DIM}" text-anchor="end">SIGNAL: STRONG</text>
  <line x1="40" y1="58" x2="{WIDTH-40}" y2="58" stroke="{LINE}" stroke-width="1"/>

  <text x="40" y="80" font-family="Consolas, monospace" font-size="11" fill="{TEXT_DIM}">&gt; IDENTIFYING ENTITY... {s["name"].upper()}</text>
  <text x="40" y="98" font-family="Consolas, monospace" font-size="11" fill="{TEXT_DIM}">&gt; YEARS ACTIVE: {years_active}   &gt; LAST SYNC: {now}</text>

  <!-- stat rows -->
  {rows_svg}

  <!-- contribution meter -->
  <text x="400" y="140" font-family="Consolas, monospace" font-size="12" fill="{TEXT_DIM}">&gt; CONTRIBUTION LEVEL</text>
  {progress_bar(400, 150, 320, 14, contrib_pct)}
  <text x="400" y="182" font-family="Consolas, monospace" font-size="11" fill="{TEXT_BRIGHT}">{s["total_contribs"]} CONTRIBUTIONS (LAST YEAR)</text>

  <text x="400" y="220" font-family="Consolas, monospace" font-size="11" fill="{TEXT_DIM}">&gt; BATTLEFIELD STATUS: ACTIVE</text>
  <text x="400" y="238" font-family="Consolas, monospace" font-size="11" fill="{TEXT_DIM}">&gt; HOSTILES: 0   ALLIES: {s["followers"]}</text>

  <!-- footer -->
  <line x1="40" y1="270" x2="{WIDTH-40}" y2="270" stroke="{LINE}" stroke-width="1"/>
  <text x="40" y="292" font-family="Consolas, monospace" font-size="12" fill="{ACCENT}" filter="url(#glow)">&gt; LOWER YOUR BLADE. THE LOG SPEAKS FOR ITSELF.</text>
  <text x="{WIDTH-40}" y="292" font-family="Consolas, monospace" font-size="10" fill="{TEXT_DIM}" text-anchor="end">STATUS: OK</text>
</svg>'''
    return svg


def render_side_panel(s):
    """Narrow tall panel: language breakdown + recent repos, styled like the
    left-hand 'REMAINS' panel in the reference image."""
    PW, PH = 260, 320
    max_count = max((c for _, c in s["lang_breakdown"]), default=1)

    corners = "".join([
        bracket_corner(12, 12, 18, 1, 1),
        bracket_corner(PW - 12, 12, 18, -1, 1),
        bracket_corner(12, PH - 12, 18, 1, -1),
        bracket_corner(PW - 12, PH - 12, 18, -1, -1),
    ])

    lang_y = 92
    lang_svg = ""
    for lang, count in s["lang_breakdown"]:
        bar_w = int(140 * (count / max_count))
        lang_svg += f'''
        <text x="26" y="{lang_y}" font-family="Consolas, monospace" font-size="10" fill="{TEXT_DIM}">{lang.upper()}</text>
        <rect x="26" y="{lang_y+6}" width="140" height="6" fill="none" stroke="{LINE}" stroke-width="1"/>
        <rect x="26" y="{lang_y+6}" width="{bar_w}" height="6" fill="{ACCENT}" opacity="0.85"/>
        '''
        lang_y += 26

    repo_y = lang_y + 24
    repo_svg = f'<text x="26" y="{repo_y}" font-family="Consolas, monospace" font-size="11" fill="{ACCENT}">&gt; RECENT ACTIVITY</text>'
    repo_y += 18
    for name in s["recent_repos"]:
        label = name.upper()
        if len(label) > 24:
            label = label[:21] + "..."
        repo_svg += f'<text x="26" y="{repo_y}" font-family="Consolas, monospace" font-size="10" fill="{TEXT_DIM}">- {label}</text>'
        repo_y += 16

    svg = f'''<svg width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <pattern id="scan2" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="4" fill="{BG}"/>
      <line x1="0" y1="0" x2="4" y2="0" stroke="#0f1a17" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="{PW}" height="{PH}" fill="{BG}"/>
  <rect width="{PW}" height="{PH}" fill="url(#scan2)" opacity="0.35"/>
  <rect x="1" y="1" width="{PW-2}" height="{PH-2}" fill="none" stroke="{LINE}" stroke-width="1" opacity="0.6"/>
  {corners}

  <text x="26" y="40" font-family="Consolas, monospace" font-size="12" fill="{ACCENT}">&gt; LANGUAGE INDEX</text>
  <line x1="26" y1="50" x2="{PW-26}" y2="50" stroke="{LINE}" stroke-width="1"/>

  {lang_svg}
  {repo_svg}

  <line x1="26" y1="{PH-30}" x2="{PW-26}" y2="{PH-30}" stroke="{LINE}" stroke-width="1"/>
  <text x="26" y="{PH-14}" font-family="Consolas, monospace" font-size="9" fill="{TEXT_DIM}">STATUS: INDEXED</text>
</svg>'''
    return svg


if __name__ == "__main__":
    stats = fetch_stats()
    with open("profile-card.svg", "w") as f:
        f.write(render_svg(stats))
    with open("side-panel.svg", "w") as f:
        f.write(render_side_panel(stats))
    print("profile-card.svg and side-panel.svg generated")
