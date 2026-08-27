import re
import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
D = pd.read_csv("dst_projections_2026.csv")
K = pd.read_csv("kicker_projections.csv")

DV = dict(zip(D["defteam"].astype(str),
              pd.to_numeric(D["proj_2026"],
                            errors="coerce")))

def last(n):
    s = str(n).replace(".", " ").strip()
    if not s:
        return ""
    return re.sub(r"[^a-z]", "", s.split()[-1].lower())

KV = {}
for _, r in K.iterrows():
    KV[last(r["kicker"])] = float(r["ppg"])

nd = nk = miss = 0
for i, r in B.iterrows():
    p = r["position"]
    if p == "DST":
        v = DV.get(str(r["team"]))
        if v == v and v is not None:
            B.at[i, "points"] = round(float(v), 2)
            B.at[i, "exp_games"] = 17.0
            nd += 1
        else:
            miss += 1
    elif p == "K":
        v = KV.get(last(r["player_display_name"]))
        if v is not None:
            B.at[i, "points"] = round(v, 2)
            B.at[i, "exp_games"] = 17.0
            nk += 1
        else:
            miss += 1

B.to_csv("board_final.csv", index=False)
print("DST filled %d | K filled %d | unmatched %d"
      % (nd, nk, miss))
print(B[B["position"].isin(["K", "DST"])]
      .nsmallest(12, "rank")
      [["rank", "player_display_name", "position",
        "team", "points"]].to_string(index=False))
