import numpy as np
import pandas as pd

S = pd.read_csv("wr_seasons.csv")
S = S.sort_values(["player_id", "season"])

N = S[["player_id", "season", "ppg"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "nppg"})
P = S.merge(N, on=["player_id", "season"], how="left")
PR = S[["player_id", "season", "ppg"]].copy()
PR["season"] = PR["season"] + 1
PR = PR.rename(columns={"ppg": "pppg"})
P = P.merge(PR, on=["player_id", "season"], how="left")

TH = 16.0
F = P[(P["ppg"] >= TH) & P["nppg"].notna()
      & P["age"].notna()].copy()
F["asc"] = (F["pppg"].notna()
            & (F["ppg"] > F["pppg"] * 1.25)).astype(float)

X = np.column_stack([np.ones(len(F)), F["ppg"].values,
                     F["age"].values - 25.0, F["asc"].values])
y = F["nppg"].values
b, *_ = np.linalg.lstsq(X, y, rcond=None)
pred = X @ b
res = y - pred
sd = float(res.std(ddof=4))

print("=== MEAN MODEL: NEXT-YEAR WR ppg ===")
print("  fit on WR seasons >= %.0f ppg, 2010-2024" % TH)
print("  n = %d" % len(F))
print("\n  next_ppg = %+.3f" % b[0])
print("             %+.4f x this_year_ppg" % b[1])
print("             %+.4f x (age - 25)" % b[2])
print("             %+.4f x breakout_flag" % b[3])
print("\n  residual sd %.2f ppg" % sd)
print("  R^2 %.3f"
      % (1 - res.var() / y.var()))

JP, JA, JB = 20.44, 23.0, 1.0
mu = b[0] + b[1] * JP + b[2] * (JA - 25.0) + b[3] * JB
print("\n=== JSN 2026 ===")
print("  2025 ppg          %.2f" % JP)
print("  age in that season  %.0f" % JA)
print("  breakout           yes (14.80 -> 20.44, +38%%)")
print("\n  carryover term    %+.2f" % (b[1] * JP))
print("  age term          %+.2f" % (b[2] * (JA - 25.0)))
print("  breakout penalty  %+.2f" % (b[3] * JB))
print("  intercept         %+.2f" % b[0])
print("  " + "-" * 34)
print("  MODEL MEAN        %6.2f ppg" % mu)
print("\n  for comparison:")
print("    board today            15.57")
print("    raw components         17.05")
print("    age 24-25 bucket ratio %.2f" % (JP * 0.921))
print("    breakout<=25 ratio     %.2f" % (JP * 0.839))
np.save("jsn_mu.npy", np.array([mu, sd]))

import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"].astype(str), SC["value"]))

def sv(k, d=0.0):
    return float(V.get(k, d))

W = pl(nfl.load_player_stats(seasons=list(range(2015, 2026))))
NEED = ["receptions", "receiving_yards", "receiving_tds",
        "rushing_yards", "rushing_tds",
        "receiving_fumbles_lost", "rushing_fumbles_lost"]
for c in NEED:
    if c not in W.columns:
        W[c] = 0.0
    W[c] = pd.to_numeric(W[c], errors="coerce").fillna(0.0)
W = W[W["position"] == "WR"].copy()
W["fp"] = (W["receptions"] * sv("rec", 1.0)
           + W["receiving_yards"] * sv("rec_yd", 0.1)
           + W["receiving_tds"] * sv("rec_td", 6.0)
           + W["rushing_yards"] * sv("rush_yd", 0.1)
           + W["rushing_tds"] * sv("rush_td", 6.0)
           + (W["receiving_fumbles_lost"]
              + W["rushing_fumbles_lost"])
           * sv("fum_lost", -2.0))

A = W.groupby(["player_id", "season"]).agg(
    tot=("fp", "sum"), g=("week", "nunique")).reset_index()
A = A[A["g"] >= 10].copy()
A["base"] = A["tot"] / A["g"]
A = A[A["base"] > 3.0]
W = W.merge(A[["player_id", "season", "base"]],
            on=["player_id", "season"], how="inner")
W["shock"] = W["fp"] / W["base"]
SH = W["shock"].values.astype(np.float32)

print("\n=== WR WEEKLY SHOCK POOL (REBUILT) ===")
print("  n = %d player-weeks" % len(SH))
print("  mean %.4f  (must be ~1.00)" % SH.mean())
print("  sd   %.3f" % SH.std())
for q in [5, 10, 25, 50, 75, 90, 95]:
    print("  p%-3d %.3f" % (q, np.percentile(SH, q)))
assert abs(SH.mean() - 1.0) < 0.02, \
    "shock pool still broken: mean %.3f" % SH.mean()
np.save("wr_shock.npy", SH)
print("  saved wr_shock.npy")

G = pd.read_csv("jsn_schedule.csv")
D = pd.read_csv("def_components.csv")
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}
D["opponent_team"] = D["opponent_team"].astype(str).replace(FIX)
W25 = D[(D["season"] == 2025) & (D["position"] == "WR")]
LG = float(W25["ypt"].mean())
DEV = {r["opponent_team"]: float(r["ypt"]) / LG
       for _, r in W25.iterrows()}
K = 0.10

wk, mus, opp = [], [], []
for _, x in G.iterrows():
    d = DEV.get(x["opp"], 1.0)
    wk.append(int(x["week"]))
    opp.append(x["opp"])
    mus.append(mu * (1.0 + K * (d - 1.0)))
mus = np.array(mus, dtype=np.float64)

print("\n=== 2026 WEEKLY PROJECTION, JSN ===")
print("  mean %.2f, matchup at the validated k=%.2f" % (mu, K))
print("  per-game spread is the shock pool scaled\n")
print("  %3s %-4s %7s %7s %7s %7s %7s"
      % ("wk", "opp", "MEAN", "p10", "p50", "p90", "P20+"))
p10 = np.percentile(SH, 10)
p50 = np.percentile(SH, 50)
p90 = np.percentile(SH, 90)
for i in range(len(wk)):
    m = mus[i]
    p20 = float((SH * m >= 20.0).mean())
    print("  %3d %-4s %7.2f %7.2f %7.2f %7.2f %6.0f%%"
          % (wk[i], opp[i], m, m * p10, m * p50,
             m * p90, 100 * p20))
print("   11 BYE      0.00")
print("\n  season total from means: %.0f pts" % mus.sum())

GAMES = len(mus)
SIMS = 1000000000
NS = SIMS // GAMES
CH = 40
per = NS // CH
rng = np.random.default_rng(20260828)
tot = np.zeros(CH * per, dtype=np.float32)
big = 0
print("\n=== MONTE CARLO ===")
print("  %d games (%d seasons x %d weeks)"
      % (per * CH * GAMES, per * CH, GAMES))
for c in range(CH):
    idx = rng.integers(0, len(SH), size=(per, GAMES))
    s = (SH[idx] * mus).astype(np.float32)
    tot[c * per:(c + 1) * per] = s.sum(axis=1)
    big += int((s >= 20.0).sum())
    if (c + 1) % 10 == 0:
        print("    chunk %d/%d" % (c + 1, CH))

print("\n  season points  mean %.1f | median %.1f"
      % (tot.mean(), np.median(tot)))
print("  p10 %.0f | p25 %.0f | p75 %.0f | p90 %.0f"
      % (np.percentile(tot, 10), np.percentile(tot, 25),
         np.percentile(tot, 75), np.percentile(tot, 90)))
print("  per-game avg   %.2f ppg" % (tot.mean() / GAMES))
print("  se of the mean %.4f ppg"
      % (tot.std() / np.sqrt(len(tot)) / GAMES))
print("\n  weeks of 20+  %.1f of %d expected"
      % (GAMES * big / float(per * CH * GAMES), GAMES))
print("  P(season >= 300 pts) %.1f%%"
      % (100.0 * (tot >= 300).mean()))
print("  P(season >= 340 pts) %.1f%%"
      % (100.0 * (tot >= 340).mean()))
print("  P(finishes below 200) %.1f%%"
      % (100.0 * (tot < 200).mean()))
