import pandas as pd
import numpy as np

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
Q = H[H["position"] == "QB"].copy()
for c in ["attempts", "passing_tds", "passing_yards"]:
    Q[c] = pd.to_numeric(Q[c], errors="coerce").fillna(0)

S = Q.groupby(["player_id", "season"]).agg(
    att=("attempts", "sum"), td=("passing_tds", "sum"),
    yds=("passing_yards", "sum"),
    g=("week", "count")).reset_index()
S = S[S["att"] >= 100].copy()
S["tdr"] = S["td"] / S["att"]
LG = S["td"].sum() / S["att"].sum()
print("league pass TD rate: %.4f (%.2f%%)" % (LG, 100 * LG))
print("QB seasons with 100+ att: %d" % len(S))

N = S[["player_id", "season", "tdr"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"tdr": "tdr_n"})
P = S.merge(N, on=["player_id", "season"], how="inner")
print("year N -> N+1 pairs: %d" % len(P))

yrs = sorted(P["season"].unique())
cut = yrs[int(len(yrs) * 0.6)]
TR = P[P["season"] < cut]
TS = P[P["season"] >= cut]

print("\n=== FIT THE REGRESSION CONSTANT k ===")
print("  rate = (td + k*LG) / (att + k)")
print("  k = attempts of league-average prior\n")
print("     k    train r   test r")
best = (0, -1)
for k in [0, 50, 100, 150, 200, 300, 400, 600, 900]:
    f = lambda d: (d["td"] + k * LG) / (d["att"] + k)
    r0 = f(TR).corr(TR["tdr_n"])
    r1 = f(TS).corr(TS["tdr_n"])
    print("  %5d    %.3f    %.3f" % (k, r0, r1))
    if r0 > best[1]:
        best = (k, r0)
K = best[0]
print("\n  best k on train = %d" % K)
print("  raw TD rate predicts next year r = %.3f"
      % TR["tdr"].corr(TR["tdr_n"]))

SP = pd.read_csv("stat_projections_2026.csv",
                 low_memory=False)
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
PY, PT = float(V["pass_yd"]), float(V["pass_td"])
RY, RT = float(V["rush_yd"]), float(V["rush_td"])

X = SP[SP["position"] == "QB"].copy()
for c in ["attempts", "passing_yards", "passing_tds",
          "rushing_yards", "rushing_tds"]:
    X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)

CAR = S.groupby("player_id").agg(
    catt=("att", "sum"), ctd=("td", "sum")).reset_index()
X = X.merge(CAR, on="player_id", how="left")
X["catt"] = X["catt"].fillna(0)
X["ctd"] = X["ctd"].fillna(0)

X["tdr_raw"] = np.where(X["attempts"] > 0,
                        X["passing_tds"] / X["attempts"],
                        LG)
X["tdr_reg"] = (X["ctd"] + K * LG) / (X["catt"] + K)
X["ptd_reg"] = X["attempts"] * X["tdr_reg"]

X["pass_now"] = (X["passing_yards"] * PY
                 + X["passing_tds"] * PT)
X["pass_reg"] = (X["passing_yards"] * PY
                 + X["ptd_reg"] * PT)
X["rush"] = (X["rushing_yards"] * RY
             + X["rushing_tds"] * RT)
X["new"] = X["pass_reg"] + X["rush"]
X["old"] = X["pass_now"] + X["rush"]

B = pd.read_csv("board_final.csv", low_memory=False)
B = B[B["position"] == "QB"][
    ["player_id", "points", "depth_rank"]]
X = X.merge(B, on="player_id", how="left")
X = X[X["depth_rank"] == 1].sort_values(
    "new", ascending=False)

print("\n=== 2026 QB, TD RATE REGRESSED (k=%d) ===" % K)
print("  starters only | no INT penalty in either column")
print("\n  %-22s %-4s %5s %5s %5s %6s %6s %6s %6s"
      % ("player", "tm", "att", "tdRaw", "tdReg",
         "rush", "noReg", "REG", "board"))
print("  " + "-" * 76)
for _, r in X.head(34).iterrows():
    bp = r["points"]
    bp = "%6.2f" % bp if bp == bp else "    --"
    print("  %-22s %-4s %5.1f %5.3f %5.3f %6.2f"
          " %6.2f %6.2f %s"
          % (str(r["player_display_name"])[:22],
             str(r["team"])[:4], r["attempts"],
             r["tdr_raw"], r["tdr_reg"], r["rush"],
             r["old"], r["new"], bp))

X["shift"] = X["new"] - X["old"]
print("\n  BIGGEST TD-RATE HAIRCUTS")
for _, r in X.nsmallest(8, "shift").iterrows():
    print("    %-22s %+5.2f ppg  (%.3f -> %.3f)"
          % (str(r["player_display_name"])[:22],
             r["shift"], r["tdr_raw"], r["tdr_reg"]))
print("\n  BIGGEST TD-RATE BOOSTS")
for _, r in X.nlargest(8, "shift").iterrows():
    print("    %-22s %+5.2f ppg  (%.3f -> %.3f)"
          % (str(r["player_display_name"])[:22],
             r["shift"], r["tdr_raw"], r["tdr_reg"]))
