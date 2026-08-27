import pandas as pd
import numpy as np

B = pd.read_csv("board_final.csv", low_memory=False)
C = pd.read_csv("wr_components.csv")

C = C[C["season"] == 2025][
    ["player_id", "tpg", "catch_rate", "ypc",
     "adot", "td_rate", "g"]]
C = C.rename(columns={"g": "g25"})

W = B[B["position"] == "WR"].copy()
W = W.merge(C, on="player_id", how="left")
W = W.sort_values("rank").reset_index(drop=True)

print("WRs on board: %d" % len(W))
print("with 2025 usage data: %d"
      % int(W["tpg"].notna().sum()))
print("with a depth-chart rank: %d"
      % int(W["depth_rank"].notna().sum()))

def f(v, w, d):
    try:
        x = float(v)
    except Exception:
        return " " * w
    if x != x:
        return " " * w
    return "%*.*f" % (w, d, x)

def line(r):
    cr = r["catch_rate"]
    cr = cr * 100 if cr == cr else float("nan")
    dp = r["depth_rank"]
    dp = "%.0f" % dp if dp == dp else " "
    st = r["status"]
    st = str(st)[:11] if st == st else ""
    return ("  %-3d %-4d %-22s %-4s %2s %s %s %s "
            "%s %s %s %s %s  %s"
            % (int(r["pos_rank"]), int(r["rank"]),
               str(r["player_display_name"])[:22],
               r["team"], dp,
               f(r["points"], 5, 1),
               f(r["exp_games"], 5, 1),
               f(r["vorp"], 6, 2),
               f(r["value"], 6, 1),
               f(r["adp"], 5, 1),
               f(r["tpg"], 5, 1),
               f(cr, 5, 1),
               f(r["ypc"], 5, 1),
               st))

HDR = ("  %-3s %-4s %-22s %-4s %2s %5s %5s %6s %6s "
       "%5s %5s %5s %5s  %s"
       % ("pos", "ovr", "player", "tm", "dp", "ppg",
          "gms", "vorp", "value", "adp", "tgt/g",
          "cat%", "ypc", "status"))

print("\n%s" % ("=" * 112))
print("ALL %d WIDE RECEIVERS - 2026" % len(W))
print("=" * 112)
print("  dp = depth-chart rank on his 2026 team")
print("  tgt/g, cat%, ypc are 2025 ACTUALS, not")
print("  inputs to the projection")
print("=" * 112)

blk = 0
for _, r in W.iterrows():
    if blk % 25 == 0:
        print(HDR)
        print("  " + "-" * 108)
    print(line(r))
    blk += 1

print("\n=== TIERS BY PROJECTED PPG ===")
for lo, hi, lb in [(15, 99, "WR1  15+"),
                   (12, 15, "WR2  12-15"),
                   (10, 12, "WR3  10-12"),
                   (7, 10, "WR4   7-10"),
                   (0, 7, "dart   <7")]:
    n = int(((W["points"] >= lo)
             & (W["points"] < hi)).sum())
    print("  %-12s %3d" % (lb, n))

W.to_csv("wr_list_2026.csv", index=False)
print("\nSaved wr_list_2026.csv")
