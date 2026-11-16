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

TGT = 0.65   # spread ratio every position gets
NPOOL_BY = {"QB": 30, "RB": 48, "WR": 60, "TE": 30}

B = pd.read_csv("board_final.csv")
B["points"] = pd.to_numeric(B["points"], errors="coerce")
if "points_raw" not in B.columns:
    B["points_raw"] = B["points"]
B["points"] = B["points_raw"]

print("=== RECALIBRATING EACH POSITION TO THE SAME "
      "SPREAD RATIO (%.2f) ===" % TGT)
print("%-5s %8s %8s %8s %8s"
      % ("POS", "OUR SD", "ACT SD", "SCALE", "NEW TOP1"))
for p in ("QB", "RB", "WR", "TE"):
    NPOOL = NPOOL_BY[p]
    a = A[A["position"] == p]
    sds, mus = [], []
    for s in sorted(a["season"].unique()):
        v = sorted(a[a["season"] == s]["mean"].values,
                   reverse=True)[:NPOOL]
        if len(v) >= 24:
            sds.append(np.std(v))
            mus.append(np.mean(v))
    asd, amu = float(np.mean(sds)), float(np.mean(mus))
    m = B["position"] == p
    o = B.loc[m, "points_raw"].dropna()
    top = o.nlargest(NPOOL)
    osd, omu = float(top.std()), float(top.mean())
    if osd < 0.1:
        continue
    scale = (asd * TGT) / osd
    newmu = omu   # keep our own level; only fix the spread
    B.loc[m, "points"] = (
        newmu + (B.loc[m, "points_raw"] - omu) * scale
    ).round(2)
    nt = float(B.loc[m, "points"].max())
    print("%-5s %8.2f %8.2f %8.3f %8.2f"
          % (p, osd, asd, scale, nt))

B["points"] = B["points"].clip(lower=0)
B.to_csv("board_final.csv", index=False)

print("\n=== TOP 12 AT EACH POSITION AFTER RECALIBRATION ===")
for p in ("QB", "RB", "WR", "TE"):
    z = B[B["position"] == p].nlargest(4, "points")
    print("\n%s:" % p)
    for _, r in z.iterrows():
        print("  %-24s %6.2f  (was %.2f)"
              % (r["player_display_name"][:24],
                 r["points"], r["points_raw"]))
c = B[B["player_display_name"].str.contains("James Cook",
                                            na=False)]
for _, r in c.iterrows():
    print("\nJames Cook: %.2f (was %.2f)"
          % (r["points"], r["points_raw"]))
