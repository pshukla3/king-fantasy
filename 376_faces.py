import json, re
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

W = pd.read_parquet("weekly_all.parquet")
hc = [c for c in W.columns if "headshot" in c.lower()]
print("headshot columns:", hc)
IMG = {}
if hc:
    d = W[W[hc[0]].notna()].sort_values("season")
    for _, r in d.iterrows():
        IMG[norm(r["player_display_name"])] = r[hc[0]]
print("headshots found: %d" % len(IMG))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
B["img"] = B["k"].map(lambda k: IMG.get(k, ""))
B = B.drop(columns=["k"])
B.to_csv("board_final.csv", index=False)
print("board rows with an image: %d of %d"
      % (int((B["img"].astype(str) != "").sum()), len(B)))
