import json
import os
import re
import pandas as pd

B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()].copy()
for c in ["p10", "p50", "p90", "points"]:
    B[c] = pd.to_numeric(B.get(c), errors="coerce")
print("p10/p90 coverage: %d / %d"
      % (B[["p10", "p90"]].notna().all(axis=1).sum(), len(B)))

POS = ["QB", "RB", "WR", "TE", "K", "DST"]

def esc(s):
    return (str(s).replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))

tier_html = ""
for p in POS:
    d = B[B["position"] == p].sort_values(
        "points", ascending=False).head(48)
    v = d["points"].values
    if len(v) < 8:
        continue
    gaps = [v[i] - v[i + 1] for i in range(len(v) - 1)]
    med = sorted(gaps)[len(gaps) // 2]
    thr = max(0.35, med * 2.2)
    tier, rows, cur = 1, "", []
    for i, (_, r) in enumerate(d.iterrows()):
        cur.append(r)
        brk = (i < len(gaps) and gaps[i] > thr)
        if brk or i == len(d) - 1:
            names = " &middot; ".join(
                esc(x["player_display_name"]) for x in cur)
            lo = min(x["points"] for x in cur)
            hi = max(x["points"] for x in cur)
            rows += ('<tr><td class="tg">T%d</td>'
                     '<td>%s</td><td class="n">%.1f&ndash;%.1f'
                     '</td></tr>' % (tier, names, lo, hi))
            tier += 1
            cur = []
    tier_html += ('<h3>%s &mdash; %d tiers</h3>'
                  '<table class="tf"><tr><th>Tier</th>'
                  '<th>Players</th><th>ppg</th></tr>'
                  '%s</table>' % (p, tier - 1, rows))

boom = ""
for p in POS:
    d = B[(B["position"] == p) & B["p90"].notna()
          & B["p10"].notna()].copy()
    d["spread"] = d["p90"] - d["p10"]
    d = d.sort_values("points", ascending=False).head(14)
    mx = float(d["p90"].max()) or 1.0
    rows = ""
    for _, r in d.iterrows():
        lo = 100.0 * r["p10"] / mx
        md = 100.0 * r["p50"] / mx
        hi = 100.0 * r["p90"] / mx
        tag = ("ceiling" if r["spread"] > d["spread"].median()
               else "floor")
        rows += ('<tr><td>%s</td>'
                 '<td class="bb"><span class="bar" '
                 'style="left:%.1f%%;width:%.1f%%"></span>'
                 '<span class="med" style="left:%.1f%%">'
                 '</span></td>'
                 '<td class="n">%.1f</td><td class="n">%.1f'
                 '</td><td class="n">%.1f</td>'
                 '<td class="tag %s">%s</td></tr>'
                 % (esc(r["player_display_name"]), lo,
                    max(1.0, hi - lo), md, r["p10"],
                    r["p50"], r["p90"], tag, tag))
    boom += ('<h3>%s</h3><table class="tf"><tr>'
             '<th>Player</th><th>Floor &rarr; ceiling</th>'
             '<th>p10</th><th>p50</th><th>p90</th>'
             '<th></th></tr>%s</table>' % (p, rows))

PAGES = {
 "rtiers": ('<h2>Tiers</h2><p class="sub">Players grouped '
            'where the projection actually breaks, not by '
            'round. A tier ends when the gap to the next '
            'player exceeds 2.2&times; the median gap at '
            'that position &mdash; so the last player in a '
            'tier is roughly as good as the first, and '
            'reaching for him costs you nothing.</p>'
            + tier_html),
 "rboom": ('<h2>Boom / Bust</h2><p class="sub">Every '
           'projection here is a distribution, not a point. '
           'p10 is a bad week, p50 typical, p90 a ceiling '
           'game. Wide bars are tournament players; narrow '
           'bars are the ones you start when you just need '
           'to not lose.</p>' + boom),
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
assert len(H) > n0 * 0.9
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))

print("\n=== SoS INPUTS AVAILABLE? ===")
for f in ["def_ratings.csv", "defense_ratings.csv",
          "matchup_def.csv", "team_def.csv",
          "matchup_weekly.pkl"]:
    print("  %-22s %s" % (f, "yes" if os.path.exists(f)
                          else "no"))
