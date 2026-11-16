import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

YRS = list(range(2015, 2026))
W = pl(nfl.load_player_stats(seasons=YRS))
PC = "fantasy_points_ppr"
assert PC in W.columns, "no ppr column: %s" % list(W.columns)[:20]
W = W[W["season_type"] == "REG"] if "season_type" in W.columns else W
W = W[W["position"].isin(["QB", "RB", "WR", "TE"])].copy()
W[PC] = pd.to_numeric(W[PC], errors="coerce").fillna(0.0)
print("weekly rows: %d | seasons %d-%d"
      % (len(W), W["season"].min(), W["season"].max()))

D = W.groupby(["opponent_team", "season", "position"]).agg(
    pts=(PC, "sum"), g=("week", "nunique")).reset_index()
D["allowed"] = D["pts"] / D["g"]
LG = D.groupby(["season", "position"])["allowed"].mean()
D = D.join(LG.rename("lgmean"),
           on=["season", "position"])
D["dev"] = D["allowed"] / D["lgmean"]
PRIOR = D.copy()
PRIOR["season"] = PRIOR["season"] + 1
PRIOR = PRIOR.rename(columns={"dev": "prior_dev"})
PRIOR = PRIOR[["opponent_team", "season", "position",
               "prior_dev"]]
print("defense-season rows: %d" % len(D))

S = W.groupby(["player_id", "season", "position"]).agg(
    tot=(PC, "sum"), g=("week", "nunique")).reset_index()
S = S[S["g"] >= 8].copy()
S["base"] = S["tot"] / S["g"]
W = W.merge(S[["player_id", "season", "base"]],
            on=["player_id", "season"], how="inner")
W = W.merge(PRIOR, on=["opponent_team", "season",
                       "position"], how="left")
W = W.dropna(subset=["prior_dev"])
print("weekly rows with a baseline and prior-yr opp: %d"
      % len(W))
W.to_pickle("matchup_weekly.pkl")

print("\n=== DOES OPPONENT ADJUSTMENT BEAT FLAT? ===")
print("  train < 2021 | valid 2021-2022 | TEST >= 2023")
print("  flat  = player season ppg, same every week")
print("  adj   = ppg x (1 + k x (opp_dev - 1))")
print("  k is fit on TRAIN only\n")
TR = W[W["season"] < 2021]
VA = W[(W["season"] >= 2021) & (W["season"] < 2023)]
TE = W[W["season"] >= 2023]

print("  %-4s %7s %9s %9s %9s %8s"
      % ("pos", "k*", "flat MAE", "adj MAE", "gain", "n test"))
for p in ["QB", "RB", "WR", "TE"]:
    tr = TR[TR["position"] == p]
    va = VA[VA["position"] == p]
    te = TE[TE["position"] == p]
    if len(te) < 500:
        continue
    best = (0.0, 9e9)
    for k in [0.0, 0.05, 0.1, 0.15, 0.2, 0.25,
              0.3, 0.4, 0.5]:
        pred = va["base"] * (1 + k * (va["prior_dev"] - 1))
        e = (pred - va[PC]).abs().mean()
        if e < best[1]:
            best = (k, e)
    k = best[0]
    f = (te["base"] - te[PC]).abs().mean()
    a = ((te["base"] * (1 + k * (te["prior_dev"] - 1)))
         - te[PC]).abs().mean()
    print("  %-4s %7.2f %9.4f %9.4f %+8.2f%% %8d"
          % (p, k, f, a, 100.0 * (1 - a / f), len(te)))

print("\n  ADOPT only where the gain is positive on TEST.")
print("  A k near 0 means the matchup carries no signal")
print("  once you already know the player's own rate.")
