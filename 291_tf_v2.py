import json
import itertools
import pandas as pd

L = json.load(open("league_data.json"))
B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()].copy()
MY = L.get("my_roster_id", 1)

ROST = {}
for t in L["rosters"]:
    rid = t.get("roster_id")
    pl = t.get("players") or t.get("roster") or []
    ROST[rid] = [(x if isinstance(x, str)
                  else x.get("name")) for x in pl]

NAME = {str(r["player_display_name"]).strip(): r
        for _, r in B.iterrows()}
srt = sorted(B["points"].fillna(0).values, reverse=True)

print("=== COVERAGE ===")
allp = [n for v in ROST.values() for n in v]
miss = [n for n in allp if n not in NAME]
print("rostered %d | matched %d | unmatched %d"
      % (len(allp), len(allp) - len(miss), len(miss)))
print("  unmatched sample: %s" % miss[:6])
mk = B["market_rank"].notna().sum()
print("market_rank present: %d of %d board rows"
      % (mk, len(B)))
onme = [n for n in ROST.get(MY, []) if n in NAME]
gaps = []
for n in onme:
    r = NAME[n]
    try:
        gaps.append((n, int(r["model_rank"]),
                     int(r["market_rank"])))
    except Exception:
        pass
print("\nmy roster model vs market rank:")
for n, a, b in sorted(gaps, key=lambda x: x[1] - x[2])[:5]:
    print("  %-22s model %4d market %4d  (%+d)"
          % (n[:22], a, b, b - a))
print("  ...")
for n, a, b in sorted(gaps, key=lambda x: x[1] - x[2])[-5:]:
    print("  %-22s model %4d market %4d  (%+d)"
          % (n[:22], a, b, b - a))

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
    return float(srt[k]) / 17.0 if 0 <= k < len(srt) \
        else ppg(n)

def pos(n):
    r = NAME.get(n)
    return str(r["position"]) if r is not None else "?"

SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE",
         "FLEX", "FLEX", "K", "DEF"]
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
me = onme
base_me = lineup(me, ppg)
print("\nmy lineup (model): %.2f ppg" % base_me)

CAND = []
for rid, names in ROST.items():
    if rid == MY:
        continue
    th = [n for n in names if n in NAME]
    if not th:
        continue
    base_th = lineup(th, mppg)
    combos = []
    for a in me:
        for b in th:
            combos.append(([a], [b]))
    for a in itertools.combinations(me, 2):
        for b in th:
            combos.append((list(a), [b]))
    for a in me:
        for b in itertools.combinations(th, 2):
            combos.append(([a], list(b)))
    for gv, gt in combos:
        m2 = [x for x in me if x not in gv] + gt
        t2 = [x for x in th if x not in gt] + gv
        if len(m2) > 17 or len(t2) > 17:
            continue
        CAND.append({
            "rid": rid, "own": TEAM.get(rid, str(rid)),
            "give": gv, "get": gt,
            "gm": lineup(m2, ppg) - base_me,
            "gt": lineup(t2, mppg) - base_th})

print("\ncandidates evaluated: %d" % len(CAND))
both = [c for c in CAND if c["gm"] > 0.05 and c["gt"] > 0.05]
print("clear BOTH bars (>0.05): %d" % len(both))

print("\n=== BEST FOR ME (ignoring their side) ===")
for c in sorted(CAND, key=lambda x: -x["gm"])[:6]:
    print("  me %+.2f them %+.2f | %s -> %s"
          % (c["gm"], c["gt"], "+".join(c["give"])[:26],
             "+".join(c["get"])[:26]))
print("\n=== BEST FOR THEM ===")
for c in sorted(CAND, key=lambda x: -x["gt"])[:6]:
    print("  me %+.2f them %+.2f | %s -> %s"
          % (c["gm"], c["gt"], "+".join(c["give"])[:26],
             "+".join(c["get"])[:26]))

both.sort(key=lambda x: -(x["gm"] + x["gt"]))
print("\n=== MUTUAL WINS (top 12) ===")
for c in both[:12]:
    print("  +%.2f you / +%.2f them | give %-24s get %s"
          % (c["gm"], c["gt"], "+".join(c["give"])[:24],
             "+".join(c["get"])[:24]))
json.dump({"trades": [
    {"rid": c["rid"], "own": c["own"], "give": c["give"],
     "get": c["get"], "gm": round(c["gm"], 2),
     "gt": round(c["gt"], 2)} for c in both[:25]]},
    open("site/_tfind.json", "w"))
print("\nwrote site/_tfind.json (%d trades)"
      % min(25, len(both)))
