import pandas as pd
import numpy as np

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX", "SD": "LAC", "OAK": "LV",
       "STL": "LA"}

B = pd.read_csv("board_final.csv", low_memory=False)
seen = set(B["team"].astype(str))
hit = sorted([t for t in FIX if t in seen])
B["team"] = B["team"].astype(str).replace(FIX)
B.to_csv("board_final.csv", index=False)

print("codes normalized: %s" % (hit if hit else "none"))
print("distinct teams on board: %d"
      % B["team"].nunique())
print(sorted(str(t) for t in set(B["team"])
             if str(t) != "nan"))

C = pd.read_csv("wr_components.csv")
C = C[C["season"] == 2025][
    ["player_id", "tpg", "catch_rate", "ypc",
     "td_rate", "tgt_share"]]
W = B[B["position"] == "WR"].copy()
W = W.merge(C, on="player_id", how="left")
W = W.sort_values("rank")

def f(v, w, d):
    try:
        x = float(v)
    except Exception:
        return " " * w
    if x != x:
        return " " * w
    return ("%*.*f" % (w, d, x))

print("\n%s" % ("=" * 108))
print("WR RANKINGS 2026  (live board, teams fixed)")
print("=" * 108)
print("  %-3s %-4s %-21s %-4s %2s %5s %5s %5s %5s "
      "%5s %5s %5s %5s  %s"
      % ("pos", "ovr", "player", "tm", "dp", "ppg",
         "gms", "vorp", "adp", "tgt/g", "cat%",
         "ypc", "shr", "status"))
print("  " + "-" * 104)

for _, r in W.head(50).iterrows():
    cr = r["catch_rate"]
    cr = cr * 100 if cr == cr else float("nan")
    st = str(r["status"]) if r["status"] == r["status"] \
        else ""
    print("  %-3d %-4d %-21s %-4s %2s %s %s %s %s "
          "%s %s %s %s  %s"
          % (int(r["pos_rank"]), int(r["rank"]),
             str(r["player_display_name"])[:21],
             r["team"],
             ("%.0f" % r["depth_rank"])
             if r["depth_rank"] == r["depth_rank"] else " ",
             f(r["points"], 5, 1), f(r["exp_games"], 5, 1),
             f(r["vorp"], 5, 2), f(r["adp"], 5, 1),
             f(r["tpg"], 5, 1), f(cr, 5, 1),
             f(r["ypc"], 5, 1), f(r["tgt_share"], 5, 3),
             st[:12]))

print("\n=== WR1s ON DEPTH CHART, RANKED ===")
o = W[W["depth_rank"] == 1].head(20)
for _, r in o.iterrows():
    print("  %-3d %-21s %-4s  %s ppg"
          % (int(r["pos_rank"]),
             str(r["player_display_name"])[:21],
             r["team"], f(r["points"], 5, 1)))
print("\nWRs on board: %d | with 2025 components: %d"
      % (len(W), int(W["tpg"].notna().sum())))
