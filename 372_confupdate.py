import json
import numpy as np
import pandas as pd
import re

# measured in 371: week-1 weight by length of track record
LAM = {1: 0.334, 2: 0.237, 3: 0.169}

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

W = pd.read_parquet("weekly_all.parquet")
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W["k"] = W["player_display_name"].map(norm)
H = (W[W["season"].between(2021, 2025)]
     .groupby(["k", "season"])["week"].nunique()
     .reset_index())
H = H[H["week"] >= 6].groupby("k").size().to_dict()
print("players with >=1 qualifying season: %d" % len(H))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
B["yrs"] = B["k"].map(lambda k: int(H.get(k, 0)))
B["lam"] = B["yrs"].map(
    lambda y: LAM.get(min(max(y, 1), 3), 0.334))
print("track record distribution:")
print(B["yrs"].clip(0, 4).value_counts().sort_index())

# rebuild proj_live with per-player weight
ADJ = json.load(open("site/_projadj.json"))
W1 = json.load(open("site/_wk1.json"))
ACT = {norm(r["n"]): r["act"] for r in W1["rows"]}
GP = {norm(r["n"]): 1 for r in W1["rows"]}

def relive(r):
    base = r.get("points")
    if pd.isna(base):
        return None
    a = ACT.get(r["k"])
    if a is None:
        return round(float(base), 2)
    n = GP.get(r["k"], 1)
    w = min(0.85, float(r["lam"]) * n)
    return round((1 - w) * float(base) + w * float(a), 2)

B["proj_live"] = B.apply(relive, axis=1)
B = B.drop(columns=["k"])
B.to_csv("board_final.csv", index=False)

D = B[B["proj_live"].notna()].copy()
D["mv"] = D["proj_live"] - D["points"]
print("\n=== HOW MUCH WEEK 1 MOVED EACH PLAYER NOW ===")
print("%-24s %-4s %4s %6s %7s %7s"
      % ("PLAYER", "POS", "YRS", "WEIGHT", "BASE", "NOW"))
for nm in ("Ja'Marr Chase", "Jalen Coker",
           "Derrick Henry", "Christian Watson",
           "Kyler Murray", "Ashton Jeanty"):
    z = D[D["player_display_name"] == nm]
    for _, r in z.iterrows():
        print("%-24s %-4s %4d %6.3f %7.2f %7.2f"
              % (nm[:24], r["position"], r["yrs"],
                 r["lam"], r["points"], r["proj_live"]))
