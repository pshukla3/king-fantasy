import pandas as pd

A_, B_ = 8.24, 0.512

B = pd.read_csv("board_final.csv", low_memory=False)
H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
PC = "fantasy_points_ppr"

P = H[(H["season"] == 2025) & (H["position"] == "QB")]
P = P.groupby("player_id").agg(
    g=("week", "count"), pts=(PC, "sum")).reset_index()
P["ppg25"] = P["pts"] / P["g"]

Q = B[B["position"] == "QB"].merge(
    P[["player_id", "ppg25", "g"]],
    on="player_id", how="left")
Q["pre"] = (Q["points"] - A_) / B_
Q = Q.sort_values("points", ascending=False)

print("replacement QB = 19.72 ppg")
print("calibrated fixed point = %.2f" % (A_ / (1 - B_)))
print("  above it calibration CUTS, below it BOOSTS\n")
print("  %-3s %-22s %-4s %2s %6s %6s %6s %6s %5s %s"
      % ("rk", "player", "tm", "dp", "2025", "pre",
         "proj", "vorp", "gms", "status"))
print("  " + "-" * 82)
n = 0
for _, r in Q.iterrows():
    if n >= 40:
        break
    n += 1
    dp = r["depth_rank"]
    dp = "%.0f" % dp if dp == dp else " "
    a = r["ppg25"]
    a = "%6.1f" % a if a == a else "    --"
    st = r["status"]
    st = "" if st != st else str(st)[:12]
    print("  %-3d %-22s %-4s %2s %s %6.2f %6.2f %6.2f "
          "%5.1f %s"
          % (int(r["rank"]),
             str(r["player_display_name"])[:22],
             str(r["team"])[:4], dp, a,
             r["pre"], r["points"], r["vorp"],
             r["exp_games"], st))
