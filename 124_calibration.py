import pandas as pd
import numpy as np

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
PC = "fantasy_points_ppr"
POS = ["QB", "RB", "WR", "TE"]

W = H[H["position"].isin(POS)].copy()
S = W.groupby(["player_id", "position", "season"]).agg(
    g=("week", "count"), pts=(PC, "sum")).reset_index()
S = S[S["g"] >= 8].copy()
S["ppg"] = S["pts"] / S["g"]

N = S[["player_id", "season", "ppg"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "ppg_n"})
P = S.merge(N, on=["player_id", "season"], how="inner")
P = P.dropna(subset=["ppg", "ppg_n"])

print("year N -> N+1 pairs, 8+ games both years:")
print(P.groupby("position").size().to_string())
print("\nmean ppg year N   %.2f" % P["ppg"].mean())
print("mean ppg year N+1 %.2f" % P["ppg_n"].mean())
P.to_csv("calib_pairs.csv", index=False)

yrs = sorted(P["season"].unique())
cut = yrs[int(len(yrs) * 0.6)]
TR = P[P["season"] < cut]
TE = P[P["season"] >= cut]
print("\ntrain < %d  n=%d" % (cut, len(TR)))
print("test >= %d  n=%d" % (cut, len(TE)))

def ols(x, y):
    b = x.cov(y) / x.var()
    return y.mean() - b * x.mean(), b

FIT = {}
print("\n=== CALIBRATION FIT ON TRAIN ===")
print("  next_ppg = intercept + slope x prior_ppg")
print("  slope < 1 means projections exaggerate spread\n")
print("  pos     n   intercept  slope")
for p in POS:
    t = TR[TR["position"] == p]
    a, b = ols(t["ppg"], t["ppg_n"])
    FIT[p] = (a, b)
    print("  %-4s %5d   %+7.2f   %5.3f" % (p, len(t), a, b))
print("\n  published WR benchmark (FFA): 0.85")
print("  RB/TE/QB published values: I could not")
print("  verify those, so trust only the column above")

print("\n=== OUT OF SAMPLE ===")
print("  bias = mean(pred - actual), + means optimistic\n")
print("  pos     n   MAEraw  MAEcal    gain   bias_raw")
tot0 = tot1 = 0.0
for p in POS:
    t = TE[TE["position"] == p]
    a, b = FIT[p]
    p0 = t["ppg"]
    p1 = a + b * t["ppg"]
    e0 = (p0 - t["ppg_n"]).abs().mean()
    e1 = (p1 - t["ppg_n"]).abs().mean()
    bi = (p0 - t["ppg_n"]).mean()
    tot0 += e0 * len(t)
    tot1 += e1 * len(t)
    print("  %-4s %5d   %5.2f   %5.2f  %+6.2f    %+6.2f"
          % (p, len(t), e0, e1, e0 - e1, bi))
print("\n  all positions  MAE %.3f -> %.3f  (%+.3f)"
      % (tot0 / len(TE), tot1 / len(TE),
         tot0 / len(TE) - tot1 / len(TE)))
print("\n  correlation is UNCHANGED by design:")
for p in POS:
    t = TE[TE["position"] == p]
    a, b = FIT[p]
    print("    %-4s raw r %.3f | calib r %.3f"
          % (p, t["ppg"].corr(t["ppg_n"]),
             (a + b * t["ppg"]).corr(t["ppg_n"])))

B = pd.read_csv("board_final.csv", low_memory=False)
B["slope"] = B["position"].map(
    {p: FIT[p][1] for p in POS})
B["icept"] = B["position"].map(
    {p: FIT[p][0] for p in POS})
have = B["slope"].notna()

B["points_cal"] = B["points"]
B.loc[have, "points_cal"] = (
    B.loc[have, "icept"] + B.loc[have, "slope"]
    * B.loc[have, "points"])
B["value_cal"] = B["value"]
B.loc[have, "value_cal"] = (
    B.loc[have, "value"] * B.loc[have, "slope"])

B = B.sort_values("value_cal", ascending=False)
B = B.reset_index(drop=True)
B["rank_cal"] = B.index + 1
B["shift"] = B["rank"] - B["rank_cal"]
B.to_csv("board_calibrated.csv", index=False)

C = ["rank", "rank_cal", "shift",
     "player_display_name", "position", "team",
     "points", "points_cal"]
print("\n=== BIGGEST CROSS-POSITION RISERS ===")
print(B[B["rank"] <= 120].nlargest(12, "shift")[C]
      .round(2).to_string(index=False))
print("\n=== BIGGEST FALLERS ===")
print(B[B["rank"] <= 120].nsmallest(12, "shift")[C]
      .round(2).to_string(index=False))
print("\n=== TOP 20 AFTER CALIBRATION ===")
print(B.head(20)[C].round(2).to_string(index=False))
print("\nSaved board_calibrated.csv - NOT live yet")
