import pandas as pd
import numpy as np

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
B["ad"] = pd.to_numeric(B["adp"], errors="coerce")
M = B[B["ad"].notna() & (B["pp"] > 0)
      & (B["ad"] < 180)].copy()
M["mkt"] = M["ad"].rank(method="min").astype(int)
M["gap"] = M["mkt"] - M["rank"]
print("players with ADP inside 180: %d" % len(M))
print("spearman vs market: %.3f"
      % M["rank"].corr(M["mkt"], method="spearman"))

print("\n=== DE'VON ACHANE ===")
a = M[M["player_display_name"].astype(str)
      .str.contains("Achane", na=False)]
for _, r in a.iterrows():
    print("  ours   #%-3d %s%d  %.2f ppg  %+.2f vorp"
          % (r["rank"], r["position"], r["pos_rank"],
             r["pp"], r["vorp"]))
    print("  market ADP %.1f -> rank #%d"
          % (r["ad"], r["mkt"]))
    print("  we are %+d picks vs the market"
          % (r["mkt"] - r["rank"]))

print("\n=== IS THE BIAS ACHANE OR THE POSITION? ===")
print("  mean gap, positive = we like them more\n")
print("  %-4s %5s %9s %9s" % ("pos", "n", "top24", "all"))
t24 = M[M["rank"] <= 24]
for p in ["RB", "WR", "TE", "QB"]:
    d, e = M[M["position"] == p], t24[t24["position"] == p]
    if not len(d):
        continue
    print("  %-4s %5d %9s %9.1f"
          % (p, len(d),
             "--" if not len(e) else "%.1f" % e["gap"].mean(),
             d["gap"].mean()))

P = pd.read_csv("proj_2026.csv")
a = P[P["player_display_name"].astype(str)
      .str.contains("Achane", na=False)]
print("\n=== WHERE 18.70 COMES FROM ===")
for _, r in a.iterrows():
    print("  2025 actual  %6.2f ppg" % r["ppg25"])
    print("  2026 model   %6.2f ppg  (%+.1f%%)"
          % (r["proj"], 100 * (r["proj"] / r["ppg25"] - 1)))
    print("  band  p10 %.2f | p50 %.2f | p90 %.2f"
          % (r["p10"], r["p50"], r["p90"]))
    print("  age %s | moved teams %s"
          % (r["age"], bool(r["moved"])))
print("\n  p50 below the mean = the model already")
print("  says the median outcome is worse than 18.70")

print("\n=== BIGGEST DISAGREEMENTS, TOP 60 ONLY ===")
T = M[M["rank"] <= 60]
print("\n  WE LIKE MORE THAN THE MARKET:")
for _, r in T.nlargest(8, "gap").iterrows():
    print("    %-22s %-3s ours #%-3d mkt #%-3d %+4d"
          % (str(r["player_display_name"])[:22],
             r["position"], r["rank"], r["mkt"], r["gap"]))
print("\n  WE LIKE LESS:")
for _, r in T.nsmallest(8, "gap").iterrows():
    print("    %-22s %-3s ours #%-3d mkt #%-3d %+4d"
          % (str(r["player_display_name"])[:22],
             r["position"], r["rank"], r["mkt"], r["gap"]))
