import pandas as pd
import numpy as np

B = pd.read_csv("board_final.csv", low_memory=False)
H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
PC = "fantasy_points_ppr"

A = H[H["season"] == 2025].groupby(
    ["player_id", "position"]).agg(
    g=("week", "count"), pts=(PC, "sum")).reset_index()
A = A[A["g"] >= 8].copy()
A["ppg25"] = A["pts"] / A["g"]

M = B.merge(A[["player_id", "ppg25", "g"]],
            on="player_id", how="inner")
M = M[M["points"] > 0]
print("players with 2025 ppg and a live projection: %d"
      % len(M))

print("\n=== SPREAD CHECK ===")
print("  if board sd is already ~0.75x the 2025 sd,")
print("  the 0.746 shrink is being applied twice\n")
print("  pos    n   sd(2025)  sd(board)  ratio  slope")
SL = {"QB": 0.512, "RB": 0.714, "WR": 0.746, "TE": 0.701}
for p in ["QB", "RB", "WR", "TE"]:
    d = M[M["position"] == p]
    if len(d) < 20:
        continue
    s0 = d["ppg25"].std()
    s1 = d["points"].std()
    print("  %-4s %4d   %6.2f     %6.2f   %.3f  %.3f"
          % (p, len(d), s0, s1, s1 / s0, SL[p]))

print("\n=== REGRESSION OF BOARD ON 2025 ACTUAL ===")
print("  slope < 1 means the board already shrank it\n")
for p in ["QB", "RB", "WR", "TE"]:
    d = M[M["position"] == p]
    if len(d) < 20:
        continue
    b = d["ppg25"].cov(d["points"]) / d["ppg25"].var()
    a = d["points"].mean() - b * d["ppg25"].mean()
    print("  %-4s board = %+5.2f + %.3f x ppg25   r=%.3f"
          % (p, a, b, d["ppg25"].corr(d["points"])))
