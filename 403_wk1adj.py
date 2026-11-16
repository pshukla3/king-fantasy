import json, re
import numpy as np
import pandas as pd

SD = 8.34      # measured spread of weekly scores
MAXFRAC = 0.12 # a player can move at most 12% of his rank
MAXABS = 14    # and never more than 14 spots

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

W1 = {norm(r["n"]): r
      for r in json.load(open("site/_wk1.json"))["rows"]}
B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
B["base_rank"] = B["rank_v"]

def adj(r):
    w = W1.get(r["k"])
    if not w:
        return 0.0
    surprise = (float(w["act"]) - float(w["proj"])) / SD
    surprise = max(-2.0, min(2.0, surprise))
    room = min(MAXABS, MAXFRAC * float(r["base_rank"]))
    return -surprise * room

B["wk1_move"] = B.apply(adj, axis=1).round(1)
B["adj_rank"] = B["base_rank"] + B["wk1_move"]
B = B.sort_values("adj_rank")
B["rank_v"] = range(1, len(B) + 1)
B["pre_rank"] = B["base_rank"]
B["upd_rank"] = B["rank_v"]
B.drop(columns=["k"]).to_csv("board_final.csv",
                             index=False)

mv = B["rank_v"] - B["base_rank"]
print("players moved: %d | mean |move| %.1f | max %d"
      % (int((mv != 0).sum()), mv.abs().mean(),
         int(mv.abs().max())))

print("\n=== TOP 20 AFTER WEEK 1 ===")
print("%-3s %-24s %-4s %6s %6s"
      % ("#", "PLAYER", "POS", "WAS", "MOVE"))
for _, r in B.head(20).iterrows():
    d = int(r["rank_v"] - r["base_rank"])
    print("%-3d %-24s %-4s %6d %6s"
          % (r["rank_v"], r["player_display_name"][:24],
             r["position"], int(r["base_rank"]),
             ("%+d" % d) if d else "-"))

print("\n=== BIGGEST RISERS ===")
B["mv"] = B["rank_v"] - B["base_rank"]
for _, r in B[B["base_rank"] <= 150].nsmallest(
        8, "mv").iterrows():
    w = W1.get(norm(r["player_display_name"]))
    print("  %-24s #%-4d -> #%-4d  (wk1 %.1f vs %.1f)"
          % (r["player_display_name"][:24],
             int(r["base_rank"]), int(r["rank_v"]),
             w["act"] if w else 0, w["proj"] if w else 0))
print("\n=== BIGGEST FALLERS ===")
for _, r in B[B["base_rank"] <= 150].nlargest(
        8, "mv").iterrows():
    w = W1.get(norm(r["player_display_name"]))
    print("  %-24s #%-4d -> #%-4d  (wk1 %.1f vs %.1f)"
          % (r["player_display_name"][:24],
             int(r["base_rank"]), int(r["rank_v"]),
             w["act"] if w else 0, w["proj"] if w else 0))
