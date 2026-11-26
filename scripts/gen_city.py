#!/usr/bin/env python3
"""Builds assets/city.svg, an isometric "commit city" from the last year of public contributions.

Usage:
  python3 scripts/gen_city.py --login ShriyaP1966 --out assets/city.svg     (needs GITHUB_TOKEN)
  python3 scripts/gen_city.py --placeholder --out assets/city.svg           (flat grid, no data)
Standard library only.
"""
import argparse, json, os, urllib.request

QUERY = ("query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{"
         "totalContributions weeks{contributionDays{date contributionCount weekday}}}}}}")
CY, VI, PK, MT = "#22d3ee", "#a78bfa", "#f472b6", "#34d399"
TEXT, MUTED, PANEL, BORDER = "#e6edf7", "#8b98b5", "#0d1226", "#243049"


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-city"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors"):
        raise SystemExit(f"GraphQL error: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[(d["weekday"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]
    return cal["totalContributions"], weeks


def shade(hex_, f):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c * f))) for c in (r, g, b))


def render(total, weeks, caption=None):
    W = 1000
    tw, th, s = 24.0, 12.0, 0.86
    n = len(weeks)
    counts = [c for w in weeks for _, c in w]
    mx = max(counts) if counts and max(counts) > 0 else 1
    active = sum(1 for c in counts if c > 0)
    xmin, xmax = -6 * tw / 2, (n - 1) * tw / 2
    ox, oy = W / 2 - (xmin + xmax) / 2, 125.0
    H = int(oy + (n - 1 + 6) * th / 2 + 75)
    palette = ["#0e7490", "#06b6d4", CY, VI, PK]

    cells = []
    for w, days in enumerate(weeks):
        for d, c in days:
            cells.append((w + d, w, d, c))
    cells.sort()

    bars = []
    for _, w, d, c in cells:
        cx = ox + (w - d) * tw / 2
        cy = oy + (w + d) * th / 2 + th / 2
        a, b = tw / 2 * s, th / 2 * s
        if c == 0:
            h, col = 1.5, "#18223b"
        else:
            r = c / mx
            h = 6 + 99 * r
            col = palette[0] if r < .2 else palette[1] if r < .4 else palette[2] if r < .65 else palette[3] if r < .85 else palette[4]
        top = [(cx, cy - b - h), (cx + a, cy - h), (cx, cy + b - h), (cx - a, cy - h)]
        left = [(cx - a, cy - h), (cx, cy + b - h), (cx, cy + b), (cx - a, cy)]
        right = [(cx + a, cy - h), (cx, cy + b - h), (cx, cy + b), (cx + a, cy)]
        P = lambda pts: " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        delay = f' style="animation-delay:{w * 0.018:.2f}s"' if c else ""
        bars.append(f'<g class="b"{delay}><polygon points="{P(left)}" fill="{shade(col, .55)}"/>'
                    f'<polygon points="{P(right)}" fill="{shade(col, .78)}"/><polygon points="{P(top)}" fill="{col}"/></g>')

    if caption is None:
        big, sub1 = f"{total:,}", "contributions in the last year"
        sub2 = f"{active} active days · busiest day {max(counts) if counts else 0}"
    else:
        big, sub1, sub2 = "—", caption, "the city fills in after the first sync"
    legend = "".join(f'<rect x="{74 + i * 18}" y="{H - 44}" width="12" height="12" rx="3" fill="{c}"/>'
                     for i, c in enumerate(["#18223b"] + palette))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Isometric city of GitHub contributions over the last year">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#080c18"/><stop offset="1" stop-color="#121538"/></linearGradient>
<linearGradient id="num" x1="0" x2="1"><stop offset="0" stop-color="{CY}"/><stop offset=".6" stop-color="{VI}"/><stop offset="1" stop-color="{PK}"/></linearGradient></defs>
<style>text{{font-family:Inter,'Segoe UI',Helvetica,Arial,sans-serif}}.m{{font-family:'Fira Code','JetBrains Mono',Consolas,'DejaVu Sans Mono',monospace}}
.b{{animation:up .8s ease backwards}}@keyframes up{{from{{opacity:0}}}}</style>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="22" fill="url(#bg)" stroke="{BORDER}"/>
<text x="{W - 40}" y="62" font-size="26" font-weight="800" fill="{TEXT}" text-anchor="end">The city I built this year</text>
<text x="{W - 40}" y="118" font-size="52" font-weight="800" fill="url(#num)" text-anchor="end">{big}</text>
<text class="m" x="{W - 40}" y="142" font-size="13" fill="{MUTED}" text-anchor="end">{sub1}</text>
<text class="m" x="{W - 40}" y="162" font-size="13" fill="{MUTED}" text-anchor="end">{sub2}</text>
{"".join(bars)}
<text class="m" x="40" y="{H - 34}" font-size="11" fill="{MUTED}">less</text>
{legend}
<text class="m" x="{74 + 6 * 18 + 6}" y="{H - 34}" font-size="11" fill="{MUTED}">more</text>
</svg>'''


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", default=os.environ.get("GITHUB_REPOSITORY_OWNER", ""))
    ap.add_argument("--out", default="assets/city.svg")
    ap.add_argument("--placeholder", action="store_true")
    a = ap.parse_args()
    if a.placeholder:
        weeks = [[(d, 0) for d in range(7)] for _ in range(53)]
        svg = render(0, weeks, caption="first sync pending")
    else:
        total, weeks = fetch(a.login, os.environ["GITHUB_TOKEN"])
        svg = render(total, weeks)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", a.out)
