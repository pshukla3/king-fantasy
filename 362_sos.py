import json
import numpy as np
import pandas as pd

POS = ["QB", "RB", "WR", "TE"]
W = pd.read_parquet("weekly_all.parquet")
W = W[W["position"].isin(POS)].copy()
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
W = W[W["opponent_team"].notna() & W["team"].notna()]
print("rows %d | seasons %s" % (len(W),
      sorted(W["season"].unique())[:3] + ["..."]))

# points allowed by each defense to each position, per game
G = (W.groupby(["season", "week", "team", "opponent_team",
                "position"])["fp"].sum().reset_index())
print("team-game-position rows: %d" % len(G))

def ratings(d):
    """additive split: allowed = mean + off_i + def_j"""
    mu = d["fp"].mean()
    off = {t: 0.0 for t in set(d["team"])}
    dfn = {t: 0.0 for t in set(d["opponent_team"])}
    for _ in range(12):
        d["_r"] = d["fp"] - mu - d["opponent_team"].map(dfn)
        off = d.groupby("team")["_r"].mean().to_dict()
        d["_r2"] = d["fp"] - mu - d["team"].map(off)
        dfn = d.groupby("opponent_team")["_r2"].mean()\
            .to_dict()
    return mu, off, dfn

RAT = {}
for p in POS:
    for s in sorted(G["season"].unique()):
        d = G[(G["position"] == p) & (G["season"] == s)]\
            .copy()
        if len(d) < 200:
            continue
        mu, off, dfn = ratings(d)
        RAT[(p, int(s))] = dfn

print("\n=== YEAR-OVER-YEAR STABILITY OF DEFENSE "
      "RATINGS (does last year predict this year?) ===")
print("%-5s %8s %8s %8s" % ("POS", "r", "n pairs",
                            "spread"))
KEEP = {}
for p in POS:
    xs, ys = [], []
    for s in range(2017, 2026):
        a, b = RAT.get((p, s - 1)), RAT.get((p, s))
        if not a or not b:
            continue
        for t in set(a) & set(b):
            xs.append(a[t])
            ys.append(b[t])
    if len(xs) < 40:
        continue
    r = float(np.corrcoef(xs, ys)[0, 1])
    sd = float(np.std(ys))
    KEEP[p] = r
    print("%-5s %8.3f %8d %8.2f" % (p, r, len(xs), sd))

print("\nshrinkage = measured r (not chosen)")

# current rating: blend 2025 and 2024, shrunk by r
CUR = {}
for p in POS:
    r = KEEP.get(p, 0.0)
    a = RAT.get((p, 2025), {})
    b = RAT.get((p, 2024), {})
    for t in set(list(a) + list(b)):
        v = 0.65 * a.get(t, 0.0) + 0.35 * b.get(t, 0.0)
        CUR[(p, t)] = v * max(0.0, r)

SCH = json.load(open("site/_sched.json"))["sched"]
print("\nschedule teams: %d" % len(SCH))

out = {}
print("\n=== HARDEST / EASIEST REMAINING SCHEDULE ===")
for p in POS:
    rows = []
    for tm, wks in SCH.items():
        vals = []
        for wk, g in wks.items():
            try:
                if int(wk) < 2:
                    continue
            except ValueError:
                continue
            opp = g.get("o")
            if not opp:
                continue
            v = CUR.get((p, opp))
            if v is not None:
                vals.append(v)
        if vals:
            rows.append((tm, float(np.mean(vals)),
                         len(vals)))
    rows.sort(key=lambda x: -x[1])
    out[p] = {t: round(v, 3) for t, v, _ in rows}
    print("\n%s  (+ = more points allowed = easier)" % p)
    for t, v, n in rows[:4]:
        print("   easiest  %-4s %+6.2f  (%d games)"
              % (t, v, n))
    for t, v, n in rows[-4:]:
        print("   hardest  %-4s %+6.2f  (%d games)"
              % (t, v, n))

json.dump({"r": KEEP, "sos": out},
          open("site/_sos.json", "w"))
print("\nwrote site/_sos.json")
