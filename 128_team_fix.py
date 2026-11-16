import re
import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
S = pd.read_csv("my_roster_sleeper.csv")

def k(n):
    return re.sub(r"[^a-z]", "", str(n).lower())

TM = {}
for _, r in S.iterrows():
    TM[k(r["player"])] = str(r["team"])

miss = B["team"].isna() | (B["team"].astype(str) == "nan")
print("rows with no team: %d" % int(miss.sum()))
n = 0
for i in B[miss].index:
    v = TM.get(k(B.at[i, "player_display_name"]))
    if v:
        B.at[i, "team"] = v
        n += 1
        print("  %-22s -> %s"
              % (B.at[i, "player_display_name"], v))

B.to_csv("board_final.csv", index=False)
left = int((B["team"].isna()
            | (B["team"].astype(str) == "nan")).sum())
print("filled %d | still missing %d" % (n, left))
if left:
    q = B[B["team"].isna()
          | (B["team"].astype(str) == "nan")]
    print(q[["rank", "player_display_name",
             "position"]].head(10).to_string(index=False))
