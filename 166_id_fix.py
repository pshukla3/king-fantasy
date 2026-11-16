import re
import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
bad = B["player_id"].isna() | (
    B["player_id"].astype(str).str.strip().isin(["", "nan"]))
print("rows with no player_id: %d" % int(bad.sum()))
for _, r in B[bad].iterrows():
    print("  %-4s %-24s %s"
          % (r["position"], str(r["player_display_name"])[:24],
             r["team"]))

def synth(nm):
    k = re.sub(r"[^a-z]", "", str(nm).lower())[:18]
    return "SYN-" + k

n = 0
for i in B[bad].index:
    B.at[i, "player_id"] = synth(B.at[i, "player_display_name"])
    n += 1
B.to_csv("board_final.csv", index=False)

d = B["player_id"]
print("\nassigned %d synthetic ids" % n)
print("rows %d | unique ids %d | still blank %d"
      % (len(B), d.nunique(),
         int((d.isna() | d.astype(str).str.strip()
              .isin(["", "nan"])).sum())))
dup = d[d.duplicated(keep=False)]
print("duplicate ids: %d" % len(dup))
if len(dup):
    print(B[B["player_id"].isin(dup)][
        ["player_id", "player_display_name", "position"]]
        .head(10).to_string(index=False))
assert int((d.isna()).sum()) == 0, "still NaN ids"
print("OK")
