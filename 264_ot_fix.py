import json
import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

KEEP = ["play_id", "game_id", "season", "qtr", "posteam",
        "home_team", "score_differential", "result",
        "down", "play_type"]
out = []
for y in range(2017, 2026):
    d = pl(nfl.load_pbp(seasons=[y]))
    d = d[[c for c in KEEP if c in d.columns]]
    out.append(d[d["qtr"] >= 5])
P = pd.concat(out, ignore_index=True)
P = P[P["posteam"].notna() & P["result"].notna()]
P = P[P["result"] != 0]
P = P[P["score_differential"].notna()]
home = P["posteam"] == P["home_team"]
P["win"] = np.where(home, (P["result"] > 0).astype(int),
                    (P["result"] < 0).astype(int))
print("OT plays %d | games %d"
      % (len(P), P["game_id"].nunique()))

F = P[P["down"].notna()].sort_values(
    ["game_id", "play_id"])
first = F.groupby("game_id").head(1)
tied = first[first["score_differential"] == 0]
n = len(tied)
p = float(tied["win"].mean())
se = (p * (1 - p) / max(n, 1)) ** 0.5
print("\n=== FIRST OT POSSESSION, TIED ===")
print("  ordered by play_id (was game_seconds, which")
print("  is 0 for every OT play - that sort was junk)")
print("  games %d | win rate %.3f" % (n, p))
print("  95%% CI  %.3f to %.3f"
      % (max(0, p - 1.96 * se), min(1, p + 1.96 * se)))
print("  coin flip sits at 0.500")

print("\n  by season:")
for s in sorted(tied["season"].unique()):
    d = tied[tied["season"] == s]
    print("    %d  n=%-3d  %.3f"
          % (s, len(d), float(d["win"].mean())))

print("\n=== OT WIN RATE BY SCORE STATE ===")
print("  every OT play, possessing team")
print("  %-12s %8s %9s" % ("state", "n", "win rate"))
OTT = {}
for lo, hi, nm in [(-99, -4, "down 4+"),
                   (-3, -1, "down 1-3"),
                   (0, 0, "tied"),
                   (1, 3, "up 1-3"),
                   (4, 99, "up 4+")]:
    d = P[(P["score_differential"] >= lo)
          & (P["score_differential"] <= hi)]
    if len(d) < 40:
        continue
    v = float(d["win"].mean())
    OTT[nm] = {"p": round(v, 3), "n": int(len(d)),
               "games": int(d["game_id"].nunique())}
    print("  %-12s %8d %9.3f  (%d games)"
          % (nm, len(d), v, d["game_id"].nunique()))
OTT["first_poss_tied"] = {"p": round(p, 3), "n": n,
                          "ci": [round(p - 1.96 * se, 3),
                                 round(p + 1.96 * se, 3)]}
json.dump(OTT, open("ot_table.json", "w"), indent=1)
print("\nwrote ot_table.json")
print("\n  the 'tied' row counts plays not games, so a")
print("  long OT drive is weighted more than a short")
print("  one. first_poss_tied is the honest per-game")
print("  number and it is thin at %d games." % n)
