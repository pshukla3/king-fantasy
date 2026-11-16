import json
import re
import numpy as np
import pandas as pd

L = json.load(open("league_data.json"))
B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()]
SUF = re.compile(r"\b(jr|sr|ii|iii|iv)\b")

def nk(s):
    s = re.sub(r"[^a-z ]", "", str(s).lower())
    s = s.replace("los angeles", "la")
    return " ".join(SUF.sub("", s).split())

SD = {}
for _, r in B.iterrows():
    a, b = r.get("p10"), r.get("p90")
    if a == a and b == b and b > a:
        SD[nk(r["player_display_name"])] = (b - a) / 2.563

T = sorted(L["teams"], key=lambda x: x["roster_id"])
IDX = {t["roster_id"]: i for i, t in enumerate(T)}
NT = len(T)
mu = np.zeros(NT)
sd = np.zeros(NT)
for t in T:
    i = IDX[t["roster_id"]]
    mu[i] = float(t.get("proj", 110.0))
    v = 0.0
    hit = 0
    for s in t.get("starters", []):
        d = SD.get(nk(s.get("name", "")))
        if d:
            v += d * d
            hit += 1
    sd[i] = np.sqrt(v) if hit >= 5 else 26.0
    print("  %-14s proj %6.1f  sd %5.1f  (%d/%d starters)"
          % ((t.get("owner") or t["name"])[:14], mu[i],
             sd[i], hit, len(t.get("starters", []))))

WK = L.get("weeks", {})
order = sorted(WK.keys(), key=lambda x: int(x))
print("\nweeks scheduled: %d" % len(order))

N = 20000
SPOTS = 6
rng = np.random.default_rng(5)
wins = np.zeros((N, NT))
pf = np.zeros((N, NT))
for w in order:
    for m in WK[w]:
        a, b = IDX.get(m["a"]), IDX.get(m["b"])
        if a is None or b is None:
            continue
        sa = rng.normal(mu[a], sd[a], N)
        sb = rng.normal(mu[b], sd[b], N)
        wins[:, a] += (sa > sb)
        wins[:, b] += (sb > sa)
        pf[:, a] += sa
        pf[:, b] += sb

key = wins * 1e6 + pf * 1e-2
rank = np.argsort(-key, axis=1)
seed_of = np.empty((N, NT), dtype=int)
rows = np.arange(N)[:, None]
seed_of[rows, rank] = np.arange(NT)[None, :]
made = (seed_of < SPOTS)

def game(x, y):
    sa = rng.normal(mu[x], sd[x])
    sb = rng.normal(mu[y], sd[y])
    return np.where(sa > sb, x, y)

s = [rank[:, i] for i in range(SPOTS)]
w36 = game(s[2], s[5])
w45 = game(s[3], s[4])
f1 = game(s[0], w45)
f2 = game(s[1], w36)
champ = game(f1, f2)
ttl = np.zeros(NT)
for i in range(NT):
    ttl[i] = (champ == i).mean()

R = []
WKS_LEFT = len(order)
for t in T:
    i = IDX[t["roster_id"]]
    # the full seed distribution, not just its mean --
    # two teams at 70% playoff odds can have very
    # different title and bye chances
    sd_pct = [float((seed_of[:, i] == k).mean())
              for k in range(NT)]
    wv = wins[:, i]
    R.append({"own": t.get("owner") or t["name"],
              "proj": mu[i], "sd": sd[i],
              "w": wins[:, i].mean(),
              "po": made[:, i].mean(),
              "seed": seed_of[:, i].mean() + 1,
              "ch": ttl[i],
              "seed_pct": [round(x, 4) for x in sd_pct],
              "med_w": float(np.median(wv)),
              "w10": float(np.percentile(wv, 10)),
              "w90": float(np.percentile(wv, 90)),
              "ros": round(float(mu[i]) * WKS_LEFT, 1),
              "wks_left": WKS_LEFT,
              "bye": float((seed_of[:, i] < 2).mean()),
              "last": float((seed_of[:, i] == NT - 1).mean())})
R.sort(key=lambda x: -x["po"])
print("\n=== PLAYOFF ODDS (%d sims, top %d make it) ==="
      % (N, SPOTS))
print("  %-15s %6s %6s %7s %7s" %
      ("team", "wins", "seed", "playoff", "title"))
for r in R:
    print("  %-15s %6.1f %6.1f %6.1f%% %6.1f%%"
          % (r["own"][:15], r["w"], r["seed"],
             100 * r["po"], 100 * r["ch"]))

import json as _json
_json.dump({"n_sims": N, "spots": SPOTS, "teams": NT,
            "wks_left": WKS_LEFT,
            "rows": sorted(R, key=lambda x: -x["po"])},
           open("site/_lgsim.json", "w"),
           separators=(",", ":"))
print("\nwrote site/_lgsim.json (seed distribution, %d teams)"
      % len(R))
print("\n=== SEED DISTRIBUTION ===")
print("  %-15s %5s %5s %6s  %s"
      % ("team", "medW", "ROS", "title", "finish 1..%d" % NT))
for r in sorted(R, key=lambda x: -x["po"]):
    bars = " ".join("%2.0f" % (p * 100) for p in r["seed_pct"])
    print("  %-15s %5.0f %5.0f %5.1f%%  %s"
          % (r["own"][:15], r["med_w"], r["ros"],
             100 * r["ch"], bars))

def esc(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;")

odds = ""
for r in R:
    bar = max(1.0, 100 * r["po"])
    odds += ('<tr><td><b>%s</b></td>'
             '<td class="n">%.1f&ndash;%.1f</td>'
             '<td class="n">%.1f</td>'
             '<td class="bb"><span class="bar" '
             'style="left:0;width:%.1f%%"></span></td>'
             '<td class="n">%.1f%%</td>'
             '<td class="n d">%.1f%%</td></tr>'
             % (esc(r["own"]), r["w"], len(order) - r["w"],
                r["seed"], bar, 100 * r["po"],
                100 * r["ch"]))

P = sorted(R, key=lambda x: -x["proj"])
pw = ""
for i, r in enumerate(P):
    pw += ('<tr><td class="tg">%d</td><td><b>%s</b></td>'
           '<td class="n">%.1f</td><td class="n">%.1f</td>'
           '<td class="n d">%.1f</td></tr>'
           % (i + 1, esc(r["own"]), r["proj"], r["sd"],
              r["w"]))

PAGES = {
 "lgodds": ('<h2>Playoff Odds</h2><p class="sub">%d '
            'simulated seasons over your actual schedule. '
            'Each team\'s weekly variance is built from its '
            'own starters\' floor-to-ceiling spreads, not a '
            'league-wide guess &mdash; so a roster of '
            'boom-bust receivers swings wider than one built '
            'on steady volume. Assumes the top %d make the '
            'playoffs.</p>'
            '<table class="tf"><tr><th>Team</th>'
            '<th>Record</th><th>Seed</th>'
            '<th>Playoff odds</th><th></th><th>Title</th>'
            '</tr>%s</table>'
            '<p class="note">Titles are simulated through a '
            'bracket where the top two seeds get byes. '
            'Because variance is large relative to the '
            'talent gap, even the best team rarely clears '
            '25%% &mdash; that is real, not a bug.</p>'
            % (N, SPOTS, odds)),
 "lgpower": ('<h2>Power Rankings</h2><p class="sub">Ranked '
             'by projected weekly points, with the '
             'volatility that comes with it. A high sigma '
             'means the team wins blowouts and loses games '
             'it should not.</p>'
             '<table class="tf"><tr><th>#</th><th>Team</th>'
             '<th>Proj ppw</th><th>Sigma</th>'
             '<th>Exp. wins</th></tr>%s</table>' % pw),
}

H = open("vaporai.html").read()
n0 = len(H)
rx = re.compile(r"</?section\b", re.I)
for sid, body in PAGES.items():
    m = re.search(r'<section id="%s"[^>]*>' % sid, H)
    if not m:
        print("  no section %s" % sid)
        continue
    d, k = 0, m.start()
    while True:
        mm = rx.search(H, k)
        if H[mm.start():mm.start() + 2] == "</":
            d -= 1
            if d == 0:
                en = H.index(">", mm.start()) + 1
                break
        else:
            d += 1
        k = mm.end()
    H = (H[:m.start()] + '<section id="%s"><div class="pg">'
         % sid + body + '</div></section>' + H[en:])
    print("  wrote %s" % sid)
assert "</script></body></html>" in H, "tail broken"
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
