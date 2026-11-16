import json, re
import numpy as np
import pandas as pd

SIMS = 20000
rng = np.random.default_rng(7)

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

D = json.load(open("site/_slteams.json"))
SCH = json.load(open("site/_lgsched.json"))
SLOTS = [s for s in D["slots"] if s != "BN"]
FLEX = {"FLEX": {"RB", "WR", "TE"},
        "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
        "WRRB_FLEX": {"RB", "WR"}, "REC_FLEX": {"WR", "TE"}}

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
VAL = {r["k"]: float(r.get("mproj") or r.get("points") or 0)
       for _, r in B.iterrows()}
AV = {r["k"]: float(r.get("avail") or 1.0)
      for _, r in B.iterrows()}
BYE = {}
for _, r in B.iterrows():
    try:
        BYE[r["k"]] = int(r.get("bye") or 0)
    except (TypeError, ValueError):
        BYE[r["k"]] = 0
print("players with a bye week: %d"
      % sum(1 for v in BYE.values() if v))

def worth(p):
    return VAL.get(p["k"], p.get("ppg", 0)) \
        * AV.get(p["k"], 1.0)

def strength(t, week=None):
    ps = t["players"]
    if week is not None:
        ps = [p for p in ps if BYE.get(p["k"], 0) != week]
    pool = sorted(ps, key=lambda x: -worth(x))
    used, tot = set(), 0.0
    for s in SLOTS:
        if s in FLEX:
            continue
        ok = {"DEF", "DST"} if s in ("DEF", "DST") else {s}
        for p in pool:
            if p["pos"] in ok and p["pid"] not in used:
                used.add(p["pid"]); tot += worth(p); break
    for s in SLOTS:
        if s not in FLEX:
            continue
        for p in pool:
            if p["pos"] in FLEX[s] and p["pid"] not in used:
                used.add(p["pid"]); tot += worth(p); break
    return tot

T = {t["id"]: t for t in D["teams"]}
S = {i: strength(t) for i, t in T.items()}
# per-week strength: bye players cannot be started, so a
# team fills the slot from its bench instead
SW = {}
for i, t in T.items():
    SW[i] = {w: strength(t, w) for w in range(2, 15)}
hit = [(T[i]["owner"], w, round(S[i] - SW[i][w], 1))
       for i in T for w in range(2, 15)
       if S[i] - SW[i][w] > 4]
hit.sort(key=lambda x: -x[2])
print("\nbiggest bye-week hits:")
for own, w, d2 in hit[:8]:
    print("  %-22s week %-3d -%.1f ppg" % (own[:22], w, d2))

# measure weekly spread from games already played
played = []
for w, games in SCH.items():
    for g in games:
        for side in g:
            if side.get("pts"):
                played.append(float(side["pts"]))
# player weekly sd is 8.34 (measured); a lineup is 10
# starters, so team sd ~ sqrt(10)*8.34 = 26.4. blend that
# prior with what we have observed, weighted by sample.
PRIOR, PW = 26.4, 30.0
if len(played) > 3:
    obs = float(np.std(played))
    n = float(len(played))
    SD = (obs * n + PRIOR * PW) / (n + PW)
else:
    SD = PRIOR
SD = max(20.0, min(34.0, SD))
print("team scores observed: %d | weekly sd %.1f"
      % (len(played), SD))

WKNOW = max((int(w) for w, g in SCH.items()
             if any(s.get("pts") for gg in g for s in gg)),
            default=1)
print("completed through week %d" % WKNOW)

rec = {i: [T[i].get("w", 0), T[i].get("l", 0),
           T[i].get("pf", 0.0)] for i in T}
REM = []
for w in sorted(SCH, key=int):
    if int(w) <= WKNOW or int(w) > 14:
        continue
    for g in SCH[w]:
        if len(g) == 2:
            REM.append((int(w), g[0]["id"], g[1]["id"]))
print("remaining regular-season games: %d" % len(REM))

PLAYOFF = 6
wins = {i: [] for i in T}
seeds = {i: [] for i in T}
made = {i: 0 for i in T}
# our projections are themselves uncertain: week 1 MAE
# was 5.15 per player, so a lineup's true level is only
# known to within a few points. draw it once per season.
SE = 6.0
for _ in range(SIMS):
    w = {i: rec[i][0] for i in T}
    pf = {i: rec[i][2] for i in T}
    true = {i: rng.normal(S[i], SE) for i in T}
    for wk, a, b in REM:
        sa = rng.normal(true[a] - (S[a] - SW[a].get(wk, S[a])),
                        SD)
        sb = rng.normal(true[b] - (S[b] - SW[b].get(wk, S[b])),
                        SD)
        pf[a] += sa; pf[b] += sb
        if sa > sb:
            w[a] += 1
        else:
            w[b] += 1
    order = sorted(T, key=lambda i: (-w[i], -pf[i]))
    for rank, i in enumerate(order, 1):
        seeds[i].append(rank)
        wins[i].append(w[i])
        if rank <= PLAYOFF:
            made[i] += 1

rows = []
for i in T:
    rows.append({"id": i, "team": T[i]["owner"],
                 "w": rec[i][0], "l": rec[i][1],
                 "pf": round(rec[i][2], 1),
                 "power": round(S[i], 1),
                 "projw": round(float(np.mean(wins[i])), 1),
                 "seed": round(float(np.mean(seeds[i])), 1),
                 "playoff": round(100.0 * made[i] / SIMS, 1)})
rows.sort(key=lambda x: -x["playoff"])
json.dump({"week": WKNOW, "sims": SIMS, "sd": round(SD, 1),
           "rows": rows}, open("site/_league.json", "w"))

print("\n=== STANDINGS / PLAYOFF ODDS ===")
print("%-22s %5s %7s %7s %7s %8s"
      % ("TEAM", "W-L", "PF", "POWER", "PROJ W", "PLAYOFF"))
for r in rows:
    print("%-22s %5s %7.1f %7.1f %7.1f %7.1f%%"
          % (r["team"][:22], "%d-%d" % (r["w"], r["l"]),
             r["pf"], r["power"], r["projw"], r["playoff"]))

print("\n=== POWER RANKINGS (roster strength) ===")
for n, r in enumerate(sorted(rows, key=lambda x: -x["power"]),
                      1):
    print("  %-2d %-22s %.1f ppg" % (n, r["team"][:22],
                                     r["power"]))
