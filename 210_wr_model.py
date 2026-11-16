import os
import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}
YRS = list(range(2010, 2026))
P_CACHE, T_CACHE = "wr_pbp_feats.csv", "wr_team_feats.csv"

def build_pbp():
    ply, tmy = [], []
    for yr in YRS:
        P = pl(nfl.load_pbp(seasons=[yr]))
        if "season_type" in P.columns:
            P = P[P["season_type"] == "REG"]
        P["posteam"] = P["posteam"].astype(str).replace(FIX)
        for c in ["air_yards", "yardline_100", "pass_oe"]:
            if c in P.columns:
                P[c] = pd.to_numeric(P[c], errors="coerce")
        R = P[P["receiver_player_id"].notna()]
        if "play_type" in P.columns:
            R = R[R["play_type"] == "pass"]
        R = R.copy()
        R["rz"] = (R["yardline_100"] <= 20).astype(float)
        R["ay"] = R["air_yards"].fillna(0.0)
        g = R.groupby(["receiver_player_id", "posteam"]).agg(
            tar=("ay", "size"), ay=("ay", "sum"),
            rz=("rz", "sum")).reset_index()
        g = g.rename(columns={"receiver_player_id": "player_id",
                              "posteam": "team"})
        g["season"] = yr
        ply.append(g)
        t = g.groupby("team").agg(
            t_tar=("tar", "sum"), t_ay=("ay", "sum"),
            t_rz=("rz", "sum")).reset_index()
        if "pass_oe" in P.columns:
            pr = P[P["pass_oe"].notna()].groupby(
                "posteam")["pass_oe"].mean()
            t["proe"] = t["team"].map(pr)
        else:
            t["proe"] = np.nan
        t["season"] = yr
        tmy.append(t)
        print("  %d  receivers %4d  teams %d  proe %s"
              % (yr, len(g), len(t),
                 "yes" if t["proe"].notna().any() else "NO"))
    A = pd.concat(ply, ignore_index=True)
    B = pd.concat(tmy, ignore_index=True)
    A.to_csv(P_CACHE, index=False)
    B.to_csv(T_CACHE, index=False)
    return A, B

if os.path.exists(P_CACHE) and os.path.exists(T_CACHE):
    PB, TM = pd.read_csv(P_CACHE), pd.read_csv(T_CACHE)
    print("cache: %d stints | %d team-seasons" % (len(PB), len(TM)))
else:
    print("building pbp features 2010-2025 (slow, one time)")
    PB, TM = build_pbp()

PB = PB.merge(TM, on=["team", "season"], how="left")
PB["ays"] = PB["ay"] / PB["t_ay"].replace(0, np.nan)
PB["rzs"] = PB["rz"] / PB["t_rz"].replace(0, np.nan)
for c in ["ays", "rzs", "proe"]:
    PB[c + "_w"] = PB[c] * PB["tar"]
G = PB.groupby(["player_id", "season"]).agg(
    tar_pbp=("tar", "sum"), ay=("ay", "sum"), rz=("rz", "sum"),
    a_w=("ays_w", "sum"), r_w=("rzs_w", "sum"),
    p_w=("proe_w", "sum")).reset_index()
for a, b in [("ay_share", "a_w"), ("rz_share", "r_w"),
             ("proe", "p_w")]:
    G[a] = G[b] / G["tar_pbp"].replace(0, np.nan)
G["adot"] = G["ay"] / G["tar_pbp"].replace(0, np.nan)
G = G.drop(columns=["a_w", "r_w", "p_w"])
G.to_csv("wr_pbp_panel.csv", index=False)

print("\nplayer-seasons with pbp features: %d" % len(G))
d = G[G["season"] == 2025].nlargest(6, "ay")
print(d[["player_id", "tar_pbp", "ay", "ay_share",
         "rz_share", "adot", "proe"]].round(3)
      .to_string(index=False))

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"].astype(str), SC["value"]))

def sv(k, d=0.0):
    try:
        return float(V.get(k, d))
    except Exception:
        return d

W = pl(nfl.load_player_stats(seasons=YRS))
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
NUM = ["targets", "receptions", "receiving_yards",
       "receiving_tds", "carries", "rushing_yards",
       "rushing_tds"]
for c in NUM:
    W[c] = pd.to_numeric(W.get(c), errors="coerce").fillna(0.0)
W["team"] = W["team"].astype(str).replace(FIX)
W["fp"] = (W["receptions"] * sv("rec", 1.0)
           + W["receiving_yards"] * sv("rec_yd", 0.1)
           + W["receiving_tds"] * sv("rec_td", 6.0)
           + W["rushing_yards"] * sv("rush_yd", 0.1)
           + W["rushing_tds"] * sv("rush_td", 6.0))

TT = W.groupby(["team", "season"]).agg(
    tt=("targets", "sum"), tg=("week", "nunique")).reset_index()
TT["t_tpg"] = TT["tt"] / TT["tg"]

S = W[W["position"] == "WR"].groupby(
    ["player_id", "season"]).agg(
    fp=("fp", "sum"), g=("week", "nunique"),
    tar=("targets", "sum"), rec=("receptions", "sum"),
    yds=("receiving_yards", "sum"),
    td=("receiving_tds", "sum"),
    car=("carries", "sum"),
    ryd=("rushing_yards", "sum")).reset_index()
tm = (W[W["position"] == "WR"]
      .groupby(["player_id", "season", "team"])["targets"]
      .sum().reset_index()
      .sort_values("targets", ascending=False)
      .drop_duplicates(["player_id", "season"]))
S = S.merge(tm[["player_id", "season", "team"]],
            on=["player_id", "season"], how="left")
S = S.merge(TT[["team", "season", "tt", "t_tpg"]],
            on=["team", "season"], how="left")
S = S[(S["g"] >= 6) & (S["tt"] > 0)].copy()

S["ppg"] = S["fp"] / S["g"]
S["tpg"] = S["tar"] / S["g"]
S["tar_share"] = S["tar"] / S["tt"]
S["ctch"] = S["rec"] / S["tar"].replace(0, np.nan)
S["ypr"] = S["yds"] / S["rec"].replace(0, np.nan)
S["tdr"] = S["td"] / S["rec"].replace(0, np.nan)
S["rush_g"] = S["car"] / S["g"]
S = S.merge(G, on=["player_id", "season"], how="left")
S["rz_tpg"] = S["rz"] / S["g"]

PL = pl(nfl.load_players())
idc = "gsis_id" if "gsis_id" in PL.columns else "player_id"
cols = [idc, "birth_date", "draft_round", "draft_pick",
        "rookie_season"]
PL = PL[[c for c in cols if c in PL.columns]].rename(
    columns={idc: "player_id"}).drop_duplicates("player_id")
PL["by"] = pd.to_datetime(PL["birth_date"],
                          errors="coerce").dt.year
S = S.merge(PL, on="player_id", how="left")
S.to_csv("wr_season_panel.csv", index=False)
print("\nWR season rows (6+ games): %d | seasons %d-%d"
      % (len(S), S["season"].min(), S["season"].max()))
print("  pbp coverage %.0f%% | age %.0f%% | draft %.0f%%"
      % (100 * S["ay_share"].notna().mean(),
         100 * S["by"].notna().mean(),
         100 * S["draft_pick"].notna().mean()))

N = S[["player_id", "season", "ppg", "team", "g"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "y", "team": "n_team",
                      "g": "n_g"})
D = S.merge(N, on=["player_id", "season"], how="inner")
D["moved"] = (D["team"] != D["n_team"]).astype(int)
NV = TT[["team", "season", "t_tpg"]].rename(
    columns={"team": "n_team", "t_tpg": "new_tpg"})
D = D.merge(NV, on=["n_team", "season"], how="left")
D["age"] = D["season"] + 1 - D["by"]
D["exp"] = D["season"] - D["rookie_season"]
D["label_season"] = D["season"] + 1

FEAT = ["ppg", "tpg", "tar_share", "ctch", "ypr", "tdr",
        "ay_share", "adot", "rz_share", "rz_tpg", "proe",
        "rush_g", "g", "age", "exp", "draft_pick",
        "t_tpg", "new_tpg", "moved"]
D = D.dropna(subset=["y", "ppg"]).copy()
D.to_csv("wr_pairs.csv", index=False)
print("\n=== TRAINING PAIRS ===")
print("  N -> N+1 rows: %d" % len(D))
print("  label seasons %d-%d"
      % (D["label_season"].min(), D["label_season"].max()))
print("  features: %d" % len(FEAT))
miss = D[FEAT].isna().mean().sort_values(ascending=False)
print("\n  missingness (top 6):")
for k, v in miss.head(6).items():
    print("    %-12s %5.1f%%" % (k, 100 * v))

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

def mae(a, b):
    return float(np.mean(np.abs(a - b)))

def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))

def pinball(a, b, q):
    d = a - b
    return float(np.mean(np.maximum(q * d, (q - 1) * d)))

def hgb(q):
    return HistGradientBoostingRegressor(
        loss="quantile", quantile=q, max_depth=4,
        learning_rate=0.05, max_iter=400,
        min_samples_leaf=25, l2_regularization=1.0,
        random_state=0)

RIDGE = Pipeline([("i", SimpleImputer(strategy="median")),
                  ("s", StandardScaler()),
                  ("m", RidgeCV(alphas=np.logspace(-2, 3, 24)))])

TESTS = [2022, 2023, 2024, 2025]
rows = []
for T in TESTS:
    tr = D[D["label_season"] < T]
    te = D[D["label_season"] == T]
    if len(te) < 30 or len(tr) < 200:
        continue
    Xtr, ytr = tr[FEAT].values, tr["y"].values
    Xte, yte = te[FEAT].values, te["y"].values
    nv = te["ppg"].values
    rd = RIDGE.fit(Xtr, ytr).predict(Xte)
    md = hgb(0.5).fit(Xtr, ytr).predict(Xte)
    lo = hgb(0.25).fit(Xtr, ytr).predict(Xte)
    hi = hgb(0.75).fit(Xtr, ytr).predict(Xte)
    cov = float(np.mean((yte >= lo) & (yte <= hi)))
    rows.append({"yr": T, "n": len(te), "tr": len(tr),
                 "nMAE": mae(nv, yte), "nRMSE": rmse(nv, yte),
                 "rMAE": mae(rd, yte), "rRMSE": rmse(rd, yte),
                 "mMAE": mae(md, yte), "mRMSE": rmse(md, yte),
                 "p25": pinball(lo, yte, 0.25),
                 "p75": pinball(hi, yte, 0.75),
                 "cov": cov})
R = pd.DataFrame(rows)

print("\n=== WALK-FORWARD HOLDOUT ===")
print("  naive = last year's ppg, unchanged\n")
print("  %4s %5s %6s %6s %6s %6s %6s %6s"
      % ("yr", "n", "naive", "ridge", "GBM",
         "nRMSE", "rRMSE", "mRMSE"))
for _, r in R.iterrows():
    print("  %4d %5d %6.3f %6.3f %6.3f %6.3f %6.3f %6.3f"
          % (r["yr"], r["n"], r["nMAE"], r["rMAE"],
             r["mMAE"], r["nRMSE"], r["rRMSE"], r["mRMSE"]))
print("  " + "-" * 52)
print("  %4s %5d %6.3f %6.3f %6.3f %6.3f %6.3f %6.3f"
      % ("all", R["n"].sum(), R["nMAE"].mean(),
         R["rMAE"].mean(), R["mMAE"].mean(),
         R["nRMSE"].mean(), R["rRMSE"].mean(),
         R["mRMSE"].mean()))

g1 = 100 * (1 - R["mMAE"].mean() / R["nMAE"].mean())
g2 = 100 * (1 - R["rMAE"].mean() / R["nMAE"].mean())
print("\n  GBM   vs naive : %+.1f%% MAE" % g1)
print("  ridge vs naive : %+.1f%% MAE" % g2)
print("  VERDICT: %s"
      % ("GBM beats doing nothing" if g1 > 1.0
         else "NO REAL GAIN - do not ship this"))

print("\n=== QUANTILE CALIBRATION ===")
print("  25-75 band should cover ~50%% of outcomes\n")
for _, r in R.iterrows():
    print("  %4d  coverage %5.1f%%  pinball25 %.3f  75 %.3f"
          % (r["yr"], 100 * r["cov"], r["p25"], r["p75"]))
print("  mean coverage %.1f%% (target 50%%)"
      % (100 * R["cov"].mean()))

tr = D[D["label_season"] < 2024]
m = hgb(0.5).fit(tr[FEAT].values, tr["y"].values)
try:
    from sklearn.inspection import permutation_importance
    te = D[D["label_season"] >= 2024]
    pi = permutation_importance(
        m, te[FEAT].values, te["y"].values,
        scoring="neg_mean_absolute_error",
        n_repeats=8, random_state=0)
    imp = sorted(zip(FEAT, pi.importances_mean),
                 key=lambda x: -x[1])
    print("\n=== FEATURE IMPORTANCE (MAE damage) ===")
    for k, v in imp:
        print("  %-12s %+7.4f" % (k, v))
except Exception as e:
    print("importance skipped: %s" % e)

print("\n" + "=" * 64)
print("=== BLOCK E: FEATURE PRUNING ===")
print("  six features had NEGATIVE importance - test removing them\n")

SETS = [
    ("all19", FEAT),
    ("pos12", ["ppg", "tpg", "age", "draft_pick", "ay_share",
               "tdr", "moved", "ypr", "tar_share", "rz_tpg",
               "g", "new_tpg"]),
    ("core6", ["ppg", "tpg", "age", "ay_share",
               "draft_pick", "moved"]),
    ("core3", ["ppg", "age", "tpg"]),
]

def run(cols):
    out = []
    for T in TESTS:
        tr = D[D["label_season"] < T]
        te = D[D["label_season"] == T]
        if len(te) < 40:
            continue
        Xtr, ytr = tr[cols].values, tr["y"].values
        Xte, yte = te[cols].values, te["y"].values
        nv = te["ppg"].values
        rd = RIDGE.fit(Xtr, ytr).predict(Xte)
        md = hgb(0.5).fit(Xtr, ytr).predict(Xte)
        bl = 0.5 * rd + 0.5 * md
        out.append([np.mean(np.abs(nv - yte)),
                    np.mean(np.abs(rd - yte)),
                    np.mean(np.abs(md - yte)),
                    np.mean(np.abs(bl - yte)),
                    float(len(te))])
    a = np.array(out)
    w = a[:, 4]
    return [float((a[:, i] * w).sum() / w.sum())
            for i in range(4)]

print("  %-7s %4s %7s %7s %7s %7s"
      % ("set", "n", "naive", "ridge", "GBM", "blend"))
print("  " + "-" * 46)
RES = {}
for nm, cols in SETS:
    r = run(cols)
    RES[nm] = (r, cols)
    print("  %-7s %4d %7.3f %7.3f %7.3f %7.3f"
          % (nm, len(cols), r[0], r[1], r[2], r[3]))

best = min(RES, key=lambda k: min(RES[k][0][1:]))
BC = RES[best][1]
bv = min(RES[best][0][1:])
who = ["ridge", "GBM", "blend"][RES[best][0][1:].index(bv)]
print("\n  BEST: %s features via %s, MAE %.3f" % (best, who, bv))
print("  vs naive %.3f  ->  %+.1f%% better"
      % (RES[best][0][0], 100 * (1 - bv / RES[best][0][0])))

print("\n=== BAND CALIBRATION ===")
print("  25-75 covered only 43.1%% - find the pair that hits 50%%\n")
print("  %-11s %9s %9s" % ("pair", "coverage", "width"))
for lo_q, hi_q in [(0.25, 0.75), (0.20, 0.80),
                   (0.15, 0.85), (0.10, 0.90)]:
    cov, wid, n = 0.0, 0.0, 0.0
    for T in TESTS:
        tr = D[D["label_season"] < T]
        te = D[D["label_season"] == T]
        if len(te) < 40:
            continue
        Xtr, ytr = tr[BC].values, tr["y"].values
        Xte, yte = te[BC].values, te["y"].values
        lo = hgb(lo_q).fit(Xtr, ytr).predict(Xte)
        hi = hgb(hi_q).fit(Xtr, ytr).predict(Xte)
        cov += float(((yte >= lo) & (yte <= hi)).sum())
        wid += float((hi - lo).sum())
        n += len(te)
    print("  %.2f-%.2f   %8.1f%% %9.2f"
          % (lo_q, hi_q, 100 * cov / n, wid / n))
print("\n  pick the pair nearest 50%% - that is your")
print("  honest floor/ceiling, not the nominal quartiles")
