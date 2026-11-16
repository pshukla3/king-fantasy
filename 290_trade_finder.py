import json
import re
import itertools
import pandas as pd

L = json.load(open("league_data.json"))
B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()].copy()
MY = L.get("my_roster_id", 1)

print("rosters key type: %s"
      % type(L.get("rosters")).__name__)
R = L.get("rosters")
ROST = {}
if isinstance(R, dict):
    for k, v in R.items():
        if isinstance(v, list):
            ROST[int(k)] = [
                (x if isinstance(x, str)
                 else x.get("name") or x.get("nm"))
                for x in v]
elif isinstance(R, list):
    for t in R:
        rid = t.get("roster_id")
        pl = t.get("players") or t.get("roster") or []
        ROST[rid] = [(x if isinstance(x, str)
                      else x.get("name")) for x in pl]
if not ROST:
    for t in L.get("teams", []):
        ROST[t["roster_id"]] = [s["name"]
                                for s in t.get("starters", [])]
    print("  fell back to starters only")
print("rosters parsed: %d teams, sizes %s"
      % (len(ROST), [len(v) for v in ROST.values()][:10]))

NAME = {}
for _, r in B.iterrows():
    NAME[str(r["player_display_name"]).strip()] = r
pts = B["points"].fillna(0).values
srt = sorted(pts, reverse=True)

def ppg(n):
    r = NAME.get(n)
    return float(r["points"]) / 17.0 if r is not None else 0.0

def mppg(n):
    r = NAME.get(n)
    if r is None:
        return 0.0
    try:
        k = int(r["market_rank"]) - 1
    except Exception:
        return ppg(n)
    if k < 0 or k >= len(srt):
        return ppg(n)
    return float(srt[k]) / 17.0

def pos(n):
    r = NAME.get(n)
    return str(r["position"]) if r is not None else "?"

SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE",
         "FLEX", "FLEX", "K", "DEF"]
FLEXOK = {"RB", "WR", "TE"}

def lineup(names, f):
    by = {}
    for n in names:
        by.setdefault(pos(n), []).append(f(n))
    for k in by:
        by[k].sort(reverse=True)
    used = {k: 0 for k in by}
    tot = 0.0
    for s in SLOTS:
        if s == "FLEX":
            best, bk = 0.0, None
            for k in FLEXOK:
                v = by.get(k, [])
                i = used.get(k, 0)
                if i < len(v) and v[i] > best:
                    best, bk = v[i], k
            if bk:
                used[bk] += 1
                tot += best
        else:
            v = by.get(s, [])
            i = used.get(s, 0)
            if i < len(v):
                tot += v[i]
                used[s] = i + 1
    return tot

TEAM = {t["roster_id"]: t.get("owner") or t.get("name")
        for t in L.get("teams", [])}
me = [n for n in ROST.get(MY, []) if n in NAME]
print("my roster: %d matched players" % len(me))
base_me = lineup(me, ppg)

OUT = []
for rid, names in ROST.items():
    if rid == MY:
        continue
    th = [n for n in names if n in NAME]
    if not th:
        continue
    base_th = lineup(th, mppg)
    for a in me:
        for b in th:
            if pos(a) != pos(b) and \
               not ({pos(a), pos(b)} <= FLEXOK):
                continue
            m2 = [x for x in me if x != a] + [b]
            t2 = [x for x in th if x != b] + [a]
            g_me = lineup(m2, ppg) - base_me
            g_th = lineup(t2, mppg) - base_th
            if g_me > 0.15 and g_th > 0.15:
                OUT.append({"rid": rid,
                            "own": TEAM.get(rid, str(rid)),
                            "give": [a], "get": [b],
                            "gm": round(g_me, 2),
                            "gt": round(g_th, 2)})
OUT.sort(key=lambda x: -x["gm"])
seen, FIN = set(), []
for o in OUT:
    k = (o["rid"], o["give"][0], o["get"][0])
    if k in seen:
        continue
    seen.add(k)
    FIN.append(o)
FIN = FIN[:25]
json.dump({"trades": FIN}, open("site/_tfind.json", "w"))
print("\ntrades found: %d (showing top 12)" % len(FIN))
for o in FIN[:12]:
    print("  +%.2f me / +%.2f them | give %-20s get %-20s"
          " [%s]" % (o["gm"], o["gt"], o["give"][0][:20],
                     o["get"][0][:20], o["own"][:12]))

rows = ""
for o in FIN:
    rows += ('<tr><td><b>%s</b><br><span>%s</span></td>'
             '<td class="g">%s</td><td class="r">%s</td>'
             '<td class="n">+%.2f</td>'
             '<td class="n d">+%.2f</td></tr>'
             % (o["own"], "roster %d" % o["rid"],
                o["give"][0], o["get"][0],
                o["gm"], o["gt"]))
if not rows:
    rows = ('<tr><td colspan="5">No trades clear both '
            'bars right now.</td></tr>')
HTML = ('<section id="tfind"><div class="pg">'
        '<h2>Trade Finder</h2>'
        '<p class="sub">Every swap scored twice: your gain '
        'by the model, their gain by market consensus. '
        'Only trades where <b>both</b> are positive appear '
        '&mdash; those are the ones you win and they still '
        'accept.</p>'
        '<table class="tf"><tr><th>Team</th><th>You give</th>'
        '<th>You get</th><th>Your gain</th>'
        '<th>Their gain</th></tr>' + rows +
        '</table></div></section>')

H = open("vaporai.html").read()
n0 = len(H)
m = re.search(r'<section id="tfind"[^>]*>', H)
assert m, "no tfind section"
d, k = 0, m.start()
rx = re.compile(r"</?section\b", re.I)
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
H = H[:m.start()] + HTML + H[en:]

CSS = ('<style id="tfcss">.pg{padding:26px}'
       '.pg h2{font-size:24px;margin:0 0 6px}'
       '.pg .sub{color:var(--dm);font-size:13px;'
       'max-width:640px;line-height:1.6;margin:0 0 20px}'
       'table.tf{width:100%;border-collapse:collapse;'
       'background:var(--pnl);border:1px solid var(--line);'
       'border-radius:12px;overflow:hidden;font-size:13px}'
       'table.tf th{text-align:left;padding:11px 14px;'
       'color:var(--dm);font-size:10px;letter-spacing:.09em;'
       'text-transform:uppercase;border-bottom:1px solid '
       'var(--line)}'
       'table.tf td{padding:11px 14px;'
       'border-bottom:1px solid #1c1f24;color:var(--tx)}'
       'table.tf td span{color:var(--dm);font-size:11px}'
       'table.tf td.g{color:#f28b82}'
       'table.tf td.r{color:#81c995}'
       'table.tf td.n{text-align:right;font-weight:700;'
       'color:#8ab4f8}'
       'table.tf td.n.d{color:var(--dm)}</style>')
H = re.sub(r'<style id="tfcss">.*?</style>', "", H,
           flags=re.S)
mb = re.search(r"<body[^>]*>", H)
H = H[:mb.end()] + CSS + H[mb.end():]
assert "</script></body></html>" in H, "tail broken"
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
