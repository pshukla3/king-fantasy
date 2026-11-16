import numpy as np
import pandas as pd

W = pd.read_parquet("weekly_all.parquet")
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W = W[W["position"].isin(["QB", "RB", "WR", "TE"])].copy()
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
A = (W[W["season"].between(2022, 2025)]
     .groupby(["season", "player_display_name",
               "position"])["fp"]
     .agg(["mean", "count"]).reset_index())
A = A[A["count"] >= 8]

B = pd.read_csv("board_final.csv")
B["points"] = pd.to_numeric(B["points"], errors="coerce")

print("=== IS OUR PROJECTION SPREAD TOO NARROW? ===")
print("%-5s %8s %8s %8s %8s %8s"
      % ("POS", "SRC", "TOP1", "TOP5", "TOP12", "SD"))
for p in ("QB", "RB", "WR", "TE"):
    a = A[A["position"] == p]
    rows = []
    for s in sorted(a["season"].unique()):
        v = sorted(a[a["season"] == s]["mean"].values,
                   reverse=True)
        if len(v) > 12:
            rows.append((v[0], np.mean(v[:5]),
                         np.mean(v[:12]), np.std(v[:36])))
    ra = np.mean([r[0] for r in rows])
    r5 = np.mean([r[1] for r in rows])
    r12 = np.mean([r[2] for r in rows])
    sd = np.mean([r[3] for r in rows])
    print("%-5s %8s %8.2f %8.2f %8.2f %8.2f"
          % (p, "actual", ra, r5, r12, sd))
    o = sorted(B[B["position"] == p]["points"]
               .dropna().values, reverse=True)
    if len(o) > 12:
        print("%-5s %8s %8.2f %8.2f %8.2f %8.2f"
              % ("", "ours", o[0], np.mean(o[:5]),
                 np.mean(o[:12]), np.std(o[:36])))
        print("%-5s %8s %8.2f %8.2f %8.2f %8.2f"
              % ("", "ratio", o[0] / ra,
                 np.mean(o[:5]) / r5,
                 np.mean(o[:12]) / r12, np.std(o[:36]) / sd))
