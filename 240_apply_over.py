import os
import pandas as pd

if not os.path.exists("situation_overrides.csv"):
    raise SystemExit("no overrides file")
O = pd.read_csv("situation_overrides.csv")
B = pd.read_csv("board_final.csv", low_memory=False)
M = dict(zip(O["player_id"].astype(str),
             O["new_ppg"]))
n = 0
for i in B.index:
    v = M.get(str(B.at[i, "player_id"]))
    if v is None:
        continue
    old = pd.to_numeric(pd.Series([B.at[i, "points"]]),
                        errors="coerce").iloc[0]
    B.at[i, "points"] = float(v)
    n += 1
    print("  %-24s %6.2f -> %6.2f"
          % (str(B.at[i, "player_display_name"])[:24],
             0 if old != old else old, float(v)))
B.to_csv("board_final.csv", index=False)
print("applied %d overrides" % n)
