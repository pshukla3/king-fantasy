import json
import re
import itertools
import pandas as pd

L = json.load(open("league_data.json"))
B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()].copy()
MY = L.get("my_roster_id", 1)

SUF = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")

def nk(s):
    s = re.sub(r"[^a-z ]", "", str(s).lower())
    s = s.replace("los angeles", "la")
    s = SUF.sub("", s)
    return " ".join(s.split())

NAME, DST = {}, {}
for _, r in B.iterrows():
    n = str(r["player_display_name"]).strip()
    NAME[nk(n)] = r
    if str(r["position"]) == "DST":
        DST[nk(n.replace("Defense", ""))] = r

def find(n):
    k = nk(n)
    if k in NAME:
        return NAME[k]
    for city, r in DST.items():
        if city and k.startswith(city):
            return r
    return None

ROST = {}
for t in L["rosters"]:
    ROST[t["roster_id"]] = [
        (x if isinstance(x, str) else x.get("name"))
        for x in (t.get("players") or t.get("roster") or [])]

allp = [n for v in ROST.values() for n in v]
miss = [n for n in allp if find(n) is None]
print("rostered %d | matched %d | unmatched %d"
      % (len(allp), len(allp) - len(miss), len(miss)))
if miss:
    print("  still unmatched: %s" % miss[:8])

srt = sorted(B["points"].fillna(0).values, reverse=True)

def ppg(n):
    r = find(n)
    return float(r["points"]) if r is not None else 0.0

def mppg(n):
    r = find(n)
    if r is None:
        return 0.0
    v = r.get("market_rank")
    if v != v or v is None:
        return float(r["points"])
    k = int(v) - 1
    return float(srt[k]) if 0 <= k < len(srt) \
        else float(r["points"])

def pos(n):
    r = find(n)
    return str(r["position"]) if r is not None else "?"

SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE",
         "FLEX", "FLEX", "K", "DST"]
FL = {"RB", "WR", "TE"}

def lineup(names, f):
    by = {}
    for n in names:
        by.setdefault(pos(n), []).append(f(n))
    for k in by:
        by[k].sort(reverse=True)
    used, tot = {}, 0.0
    for s in SLOTS:
        if s == "FLEX":
            best, bk = 0.0, None
            for k in FL:
                v, i = by.get(k, []), used.get(k, 0)
                if i < len(v) and v[i] > best:
                    best, bk = v[i], k
            if bk:
                used[bk] = used.get(bk, 0) + 1
                tot += best
        else:
            v, i = by.get(s, []), used.get(s, 0)
            if i < len(v):
                tot += v[i]
                used[s] = i + 1
    return tot

TEAM = {t["roster_id"]: t.get("owner") or t.get("name")
        for t in L.get("teams", [])}
me = [n for n in ROST[MY] if find(n) is not None]
base = lineup(me, ppg)
print("\nmy lineup: %.1f ppg  (should be ~110-130)" % base)
if base < 60:
    print("  STILL WRONG - not writing page")
    raise SystemExit(1)

CAND = []
for rid, names in ROST.items():
    if rid == MY:
        continue
    th = [n for n in names if find(n) is not None]
    bt = lineup(th, mppg)
    combos = [([a], [b]) for a in me for b in th]
    combos += [(list(a), [b])
               for a in itertools.combinations(me, 2)
               for b in th]
    combos += [([a], list(b)) for a in me
               for b in itertools.combinations(th, 2)]
    for gv, gt in combos:
        m2 = [x for x in me if x not in gv] + gt
        t2 = [x for x in th if x not in gt] + gv
        CAND.append({"rid": rid,
                     "own": TEAM.get(rid, str(rid)),
                     "give": gv, "get": gt,
                     "gm": lineup(m2, ppg) - base,
                     "gt": lineup(t2, mppg) - bt})

both = [c for c in CAND if c["gm"] > 0.4 and c["gt"] > 0.4]
both.sort(key=lambda x: -x["gm"])
best = {}
for c in both:
    k = (c["rid"], tuple(sorted(c["get"])))
    p = best.get(k)
    if p is None or (len(c["give"]), -c["gm"]) < \
            (len(p["give"]), -p["gm"]):
        best[k] = c
FIN, per = [], {}
for c in sorted(best.values(), key=lambda x: -x["gm"]):
    if per.get(c["rid"], 0) >= 3:
        continue
    per[c["rid"]] = per.get(c["rid"], 0) + 1
    FIN.append(c)
print("evaluated %d | mutual wins %d | unique %d"
      % (len(CAND), len(both), len(FIN)))
print("\n=== TOP TRADES (ppg gain) ===")
for c in FIN[:12]:
    print("  +%.2f you / +%.2f them | %-13s"
          " give %-26s get %s"
          % (c["gm"], c["gt"], c["own"][:13],
             " + ".join(c["give"])[:26],
             " + ".join(c["get"])[:26]))
json.dump({"trades": [
    {"own": c["own"], "give": c["give"], "get": c["get"],
     "gm": round(c["gm"], 2), "gt": round(c["gt"], 2)}
    for c in FIN[:25]]}, open("site/_tfind.json", "w"))
print("\nwrote site/_tfind.json (%d)" % len(FIN[:25]))
