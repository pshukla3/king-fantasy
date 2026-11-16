import json, re
from itertools import combinations
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

D = json.load(open("site/_slteams.json"))
SLOTS = [s for s in D["slots"] if s != "BN"]
FLEX = {"FLEX": {"RB", "WR", "TE"},
        "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
        "WRRB_FLEX": {"RB", "WR"}, "REC_FLEX": {"WR", "TE"}}

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
VAL, AVAIL, RK = {}, {}, {}
for _, r in B.iterrows():
    VAL[r["k"]] = float(r.get("mproj") or r.get("points") or 0)
    AVAIL[r["k"]] = float(r.get("avail") or 1.0)
    RK[r["k"]] = int(r["rank_v"]) if pd.notna(r.get("rank_v")) else 999

def worth(p):
    k = p["k"]
    return VAL.get(k, p.get("ppg", 0)) * AVAIL.get(k, 1.0)

def best(players):
    pool = sorted(players, key=lambda x: -worth(x))
    used, tot = set(), 0.0
    for s in SLOTS:
        if s in FLEX:
            continue
        ok = {"DEF", "DST"} if s in ("DEF", "DST") else {s}
        for p in pool:
            if p["pos"] in ok and p["pid"] not in used:
                used.add(p["pid"])
                tot += worth(p)
                break
    for s in SLOTS:
        if s not in FLEX:
            continue
        for p in pool:
            if p["pos"] in FLEX[s] and p["pid"] not in used:
                used.add(p["pid"])
                tot += worth(p)
                break
    return tot

teams = D["teams"]
me = next((t for t in teams
           if str(t.get("owner", "")).startswith("Shukie")),
          teams[0])
print("scanning for: %s" % me["owner"])
base_me = best(me["players"])
print("your optimal lineup: %.1f ppg\n" % base_me)

def swap(a, give, b, get):
    aa = [p for p in a if p["pid"] not in
          {g["pid"] for g in give}] + get
    bb = [p for p in b if p["pid"] not in
          {g["pid"] for g in get}] + give
    return aa, bb

ideas = []
for t in teams:
    if t["id"] == me["id"]:
        continue
    base_t = best(t["players"])
    mine = sorted(me["players"], key=lambda x: -worth(x))[:12]
    hers = sorted(t["players"], key=lambda x: -worth(x))[:12]
    for g in mine:
        for r in hers:
            aa, bb = swap(me["players"], [g],
                          t["players"], [r])
            da, db = best(aa) - base_me, best(bb) - base_t
            if da > 0.15 and db > 0.15:
                ideas.append((da, db, t["owner"],
                              [g["n"]], [r["n"]]))
    for g in mine[:8]:
        for r2 in combinations(hers[:9], 2):
            aa, bb = swap(me["players"], [g],
                          t["players"], list(r2))
            da, db = best(aa) - base_me, best(bb) - base_t
            if da > 0.15 and db > 0.15:
                ideas.append((da, db, t["owner"],
                              [g["n"]],
                              [x["n"] for x in r2]))
    for g2 in combinations(mine[:9], 2):
        for r in hers[:8]:
            aa, bb = swap(me["players"], list(g2),
                          t["players"], [r])
            da, db = best(aa) - base_me, best(bb) - base_t
            if da > 0.15 and db > 0.15:
                ideas.append((da, db, t["owner"],
                              [x["n"] for x in g2], [r["n"]]))

ideas.sort(key=lambda x: -(x[0] + x[1]))
seen, out = set(), []
for it in ideas:
    key = (it[2], tuple(sorted(it[3])), tuple(sorted(it[4])))
    if key in seen:
        continue
    seen.add(key)
    out.append(it)

print("=== TRADES THAT HELP BOTH SIDES ===")
print("(both lineups must improve, or it gets rejected)\n")
for da, db, own, give, get in out[:14]:
    print("%s" % own)
    print("   you give : %s" % ", ".join(
        "%s (#%d)" % (n, RK.get(norm(n), 999)) for n in give))
    print("   you get  : %s" % ", ".join(
        "%s (#%d)" % (n, RK.get(norm(n), 999)) for n in get))
    print("   you %+.2f ppg | them %+.2f ppg\n" % (da, db))
print("total candidates found: %d" % len(out))
