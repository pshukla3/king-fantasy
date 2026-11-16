import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
B["ad"] = pd.to_numeric(B["adp"], errors="coerce")
M = B[B["ad"].notna() & (B["pp"] > 0)
      & (B["ad"] < 180)].copy()
M["pmkt"] = M.groupby("position")["ad"].rank(
    method="min").astype(int)
M["pgap"] = M["pmkt"] - M["pos_rank"]

print("=== POSITION RANK vs POSITIONAL ADP ===")
print("  positive = we rate him above the market\n")
print("  %-4s %5s %8s %8s %8s"
      % ("pos", "n", "top12", "top36", "spear"))
for p in ["RB", "WR", "TE", "QB"]:
    d = M[M["position"] == p]
    if len(d) < 8:
        continue
    print("  %-4s %5d %8.1f %8.1f %8.3f"
          % (p, len(d),
             d[d["pos_rank"] <= 12]["pgap"].mean(),
             d[d["pos_rank"] <= 36]["pgap"].mean(),
             d["pos_rank"].corr(d["pmkt"],
                                method="spearman")))

print("\n=== RB TOP 12: OURS vs MARKET ===")
r = M[M["position"] == "RB"].nsmallest(12, "pos_rank")
print("  %-22s %6s %6s %6s %6s"
      % ("player", "ours", "mkt", "gap", "ppg"))
for _, x in r.iterrows():
    print("  %-22s %6d %6d %+6d %6.2f"
          % (str(x["player_display_name"])[:22],
             x["pos_rank"], x["pmkt"], x["pgap"], x["pp"]))
