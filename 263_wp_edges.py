import json
import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

YRS = list(range(2017, 2026))
print("pulling OT plays %d-%d (rules changed 2017)"
      % (YRS[0], YRS[-1]))
out = []
KEEP = ["game_id", "season", "qtr", "posteam",
        "home_team", "score_differential", "result",
        "game_seconds_remaining", "down"]
for y in YRS:
    d = pl(nfl.load_pbp(seasons=[y]))
    d = d[[c for c in KEEP if c in d.columns]]
    d = d[d["qtr"] >= 5]
    out.append(d)
P = pd.concat(out, ignore_index=True)
P = P[P["posteam"].notna() & P["result"].notna()]
P = P[P["score_differential"].notna()]
home = P["posteam"] == P["home_team"]
P["win"] = np.where(home, (P["result"] > 0).astype(int),
                    (P["result"] < 0).astype(int))
P = P[P["result"] != 0]
print("OT plays %d | games %d"
      % (len(P), P["game_id"].nunique()))

print("\n=== OT WIN RATE BY SCORE STATE ===")
print("  possessing team\n")
print("  %-12s %8s %9s" % ("state", "n", "win rate"))
OTT = {}
for lo, hi, nm in [(-99, -4, "down 4+"),
                   (-3, -1, "down 1-3"),
                   (0, 0, "tied"),
                   (1, 3, "up 1-3"),
                   (4, 99, "up 4+")]:
    d = P[(P["score_differential"] >= lo)
          & (P["score_differential"] <= hi)]
    if len(d) < 50:
        continue
    v = float(d["win"].mean())
    OTT[nm] = {"p": round(v, 3), "n": int(len(d))}
    print("  %-12s %8d %9.3f" % (nm, len(d), v))

f = P[P["down"].notna()]
f = f.sort_values(["game_id", "game_seconds_remaining"],
                  ascending=[True, False])
first = f.groupby("game_id").head(1)
tied = first[first["score_differential"] == 0]
print("\n  first OT possession while tied:")
print("    games %d | that team wins %.3f"
      % (len(tied), float(tied["win"].mean())))
OTT["first_poss_tied"] = {
    "p": round(float(tied["win"].mean()), 3),
    "n": int(len(tied))}
