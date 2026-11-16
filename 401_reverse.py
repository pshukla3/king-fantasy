import re
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

src = open("400_consensus.py").read()
blk = re.search(r'C = """(.*?)"""', src, re.S).group(1)
names = [x.strip() for x in blk.replace("\n", "").split("|")
         if x.strip()]
def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()
CR = {norm(n): i + 1 for i, n in enumerate(names)}
print("consensus players: %d" % len(CR))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
B["crank"] = B["k"].map(CR)
D = B[B["crank"].notna()].copy()

W = pd.read_parquet("weekly_all.parquet")
W["k"] = W["player_display_name"].map(norm)
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
P25 = W[W["season"] == 2025].groupby("k")["fp"].mean()
D["py"] = D["k"].map(P25)

import json
W1 = {norm(r["n"]): r["act"]
      for r in json.load(open("site/_wk1.json"))["rows"]}
D["wk1"] = D["k"].map(W1)

print("\n=== WHAT DOES CONSENSUS RANK TRACK? ===")
print("(rank correlation; negative = higher rank goes "
      "with a bigger value, which is what we expect)")
for col, lab in (("py", "2025 points per game"),
                 ("adp", "ADP"),
                 ("points", "our preseason projection"),
                 ("mproj", "our model projection"),
                 ("wk1", "WEEK 1 POINTS"),
                 ("inj_risk", "injury risk"),
                 ("exp_g", "expected games")):
    if col not in D.columns:
        continue
    d = D[D[col].notna() & D["crank"].notna()]
    if len(d) < 25:
        continue
    r = spearmanr(d["crank"], d[col]).statistic
    print("  %-26s n=%-4d rho %+.3f" % (lab, len(d), r))

print("\n=== HOW MUCH DID WEEK 1 MOVE THEM? ===")
d = D[D["wk1"].notna() & D["py"].notna()].copy()
d["py_rank"] = d["py"].rank(ascending=False)
d["w1_rank"] = d["wk1"].rank(ascending=False)
print("  consensus vs 2025 production : rho %+.3f"
      % spearmanr(d["crank"], d["py_rank"]).statistic)
print("  consensus vs week 1 alone    : rho %+.3f"
      % spearmanr(d["crank"], d["w1_rank"]).statistic)

print("\n=== BIG WEEK 1, STILL RANKED LOW ===")
for _, r in d.nsmallest(8, "wk1").head(0).iterrows():
    pass
z = d[d["wk1"] >= 20].sort_values("crank",
                                  ascending=False)
for _, r in z.head(8).iterrows():
    print("  %-24s wk1 %5.1f  consensus #%d"
          % (r["player_display_name"][:24], r["wk1"],
             r["crank"]))
print("\n=== BAD WEEK 1, STILL RANKED HIGH ===")
z = d[(d["wk1"] <= 6) & (d["crank"] <= 60)]\
    .sort_values("crank")
for _, r in z.head(8).iterrows():
    print("  %-24s wk1 %5.1f  consensus #%d"
          % (r["player_display_name"][:24], r["wk1"],
             r["crank"]))

print("\n=== POSITIONAL SHAPE OF THE CONSENSUS BOARD ===")
for p in ("RB", "WR", "TE", "QB"):
    z = D[D["position"] == p]["crank"]
    if len(z) < 3:
        continue
    print("  %-4s first at #%-4.0f | %d in the top 50"
          % (p, z.min(), int((z <= 50).sum())))
