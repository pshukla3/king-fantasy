import os
import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(d):
    return d.to_pandas() if hasattr(d, "to_pandas") else d

def col(df, *names):
    for n in names:
        if n in df.columns:
            return n
    return None

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}
YRS = list(range(2010, 2026))
SKILL = ["RB", "WR", "TE"]

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))

def sv(k, d=0.0):
    return float(V.get(k, d))

W = pl(nfl.load_player_stats(seasons=YRS))
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
NUM = ["receptions", "targets", "receiving_yards",
       "receiving_tds", "carries", "rushing_yards",
       "rushing_tds"]
for c in NUM:
    W[c] = (pd.to_numeric(W[c], errors="coerce").fillna(0.0)
            if c in W.columns else 0.0)
tc = col(W, "team", "recent_team")
W["team"] = W[tc].astype(str).replace(FIX)
W["fp"] = (W["receptions"] * sv("rec", 1.0)
           + W["receiving_yards"] * sv("rec_yd", 0.1)
           + W["receiving_tds"] * sv("rec_td", 6.0)
           + W["rushing_yards"] * sv("rush_yd", 0.1)
           + W["rushing_tds"] * sv("rush_td", 6.0))

# team pools BEFORE the position filter.
# targets: everyone. carries: skill only, so QB scrambles
# do not inflate the RB denominator.
TT = W.groupby(["team", "season"]).agg(
    t_tar=("targets", "sum"),
    tg=("week", "nunique")).reset_index()
RC = W[W["position"].isin(SKILL)].groupby(
    ["team", "season"]).agg(
    t_car=("carries", "sum")).reset_index()
TT = TT.merge(RC, on=["team", "season"], how="left")
TT["t_tpg"] = TT["t_tar"] / TT["tg"]
TT["t_cpg"] = TT["t_car"] / TT["tg"]

W = W[W["position"].isin(SKILL)].copy()
print("weekly skill rows %d | seasons %d-%d"
      % (len(W), W["season"].min(), W["season"].max()))
print("team-seasons %d | league mean %.1f tar/g, %.1f car/g"
      % (len(TT), TT["t_tpg"].mean(), TT["t_cpg"].mean()))

S = W.groupby(["player_id", "season", "position"]).agg(
    fp=("fp", "sum"), g=("week", "nunique"),
    tar=("targets", "sum"), rec=("receptions", "sum"),
    cyd=("receiving_yards", "sum"),
    ctd=("receiving_tds", "sum"),
    car=("carries", "sum"), ryd=("rushing_yards", "sum"),
    rtd=("rushing_tds", "sum")).reset_index()
tm = (W.sort_values(["player_id", "season", "week"])
      .groupby(["player_id", "season"])["team"]
      .last().reset_index())
S = S.merge(tm, on=["player_id", "season"], how="left")
S = S.merge(TT, on=["team", "season"], how="left")
S = S[S["g"] >= 6].copy()

S["ppg"] = S["fp"] / S["g"]
S["tpg"] = S["tar"] / S["g"]
S["cpg"] = S["car"] / S["g"]
S["tar_share"] = S["tar"] / S["t_tar"].replace(0, np.nan)
S["car_share"] = S["car"] / S["t_car"].replace(0, np.nan)
S["opp_share"] = ((S["tar"] + S["car"])
                  / (S["t_tar"] + S["t_car"]).replace(0, np.nan))
S["ctch"] = S["rec"] / S["tar"].replace(0, np.nan)
S["ypr"] = S["cyd"] / S["rec"].replace(0, np.nan)
S["tdr"] = S["ctd"] / S["rec"].replace(0, np.nan)
S["ypc"] = S["ryd"] / S["car"].replace(0, np.nan)
S["rtdr"] = S["rtd"] / S["car"].replace(0, np.nan)

S["ay_share"] = np.nan
if (os.path.exists("wr_pbp_feats.csv")
        and os.path.exists("wr_team_feats.csv")):
    P = pd.read_csv("wr_pbp_feats.csv")
    T = pd.read_csv("wr_team_feats.csv")
    print("  pbp cache cols : %s" % list(P.columns))
    print("  team cache cols: %s" % list(T.columns))
    pid = col(P, "player_id", "receiver_player_id")
    ptm = col(P, "team", "posteam")
    ttm = col(T, "team", "posteam")
    if pid and ptm and ttm and "ay" in P.columns:
        P = P.rename(columns={pid: "player_id", ptm: "team"})
        T = T.rename(columns={ttm: "team"})
        P["team"] = P["team"].astype(str).replace(FIX)
        T["team"] = T["team"].astype(str).replace(FIX)
        P = P.merge(T[["team", "season", "t_ay"]],
                    on=["team", "season"], how="left")
        P["sh"] = P["ay"] / P["t_ay"].replace(0, np.nan)
        P["shw"] = P["sh"] * P["tar"]
        A = P.groupby(["player_id", "season"]).agg(
            shw=("shw", "sum"), tw=("tar", "sum")).reset_index()
        A["ay_share"] = A["shw"] / A["tw"].replace(0, np.nan)
        S = S.drop(columns=["ay_share"]).merge(
            A[["player_id", "season", "ay_share"]],
            on=["player_id", "season"], how="left")
        print("  ay_share attached to %.0f%% of rows"
              % (100 * S["ay_share"].notna().mean()))
    else:
        print("  CACHE SCHEMA UNEXPECTED - ay_share left blank")
else:
    print("  no pbp cache - ay_share left blank")

S.to_csv("pos_season_panel.csv", index=False)
print("\nseason rows (6+ games): %d" % len(S))
print(S.groupby("position").size().to_string())

N = S[["player_id", "season", "ppg", "team"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "y", "team": "n_team"})
D = S.merge(N, on=["player_id", "season"], how="inner")
D["moved"] = (D["team"] != D["n_team"]).astype(int)

NV = TT[["team", "season", "t_tpg", "t_cpg"]].rename(
    columns={"team": "n_team", "t_tpg": "n_tpg",
             "t_cpg": "n_cpg"})
D = D.merge(NV, on=["n_team", "season"], how="left")

PL = pl(nfl.load_players())
idc = col(PL, "gsis_id", "player_id")
keep = [idc, "birth_date", "draft_pick", "rookie_season"]
PL = PL[[c for c in keep if c in PL.columns]].rename(
    columns={idc: "player_id"}).drop_duplicates("player_id")
PL["by"] = pd.to_datetime(PL["birth_date"],
                          errors="coerce").dt.year
D = D.merge(PL, on="player_id", how="left")
D["age"] = D["season"] + 1 - D["by"]
D["exp"] = D["season"] - D["rookie_season"]
D["label_season"] = D["season"] + 1
D = D.dropna(subset=["y", "ppg"]).copy()
D.to_csv("pos_pairs.csv", index=False)

FEAT = {
    "WR": ["ppg", "tpg", "tar_share", "ctch", "ypr", "tdr",
           "ay_share", "age", "draft_pick", "moved",
           "n_tpg", "g"],
    "TE": ["ppg", "tpg", "tar_share", "ctch", "ypr", "tdr",
           "ay_share", "age", "draft_pick", "moved",
           "n_tpg", "g"],
    "RB": ["ppg", "cpg", "tpg", "car_share", "opp_share",
           "ypc", "rtdr", "ctch", "age", "draft_pick",
           "moved", "n_cpg", "g"],
}
CORE = {
    "WR": ["ppg", "tpg", "age", "ay_share", "draft_pick",
           "moved"],
    "TE": ["ppg", "tpg", "age", "ay_share", "draft_pick",
           "moved"],
    "RB": ["ppg", "cpg", "opp_share", "age", "draft_pick",
           "moved"],
}

print("\n=== TRAINING PAIRS ===")
print("  %-4s %6s %12s %10s"
      % ("pos", "pairs", "label yrs", "mean y"))
for p in ["RB", "WR", "TE"]:
    d = D[D["position"] == p]
    print("  %-4s %6d %6d-%-5d %10.2f"
          % (p, len(d), d["label_season"].min(),
             d["label_season"].max(), d["y"].mean()))
print("\n  year-over-year correlation (the naive signal):")
for p in ["RB", "WR", "TE"]:
    d = D[D["position"] == p]
    print("    %-4s r = %+.3f" % (p, d["ppg"].corr(d["y"])))

from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor

TESTS = [2021, 2022, 2023, 2024, 2025]

def ridge():
    return Pipeline([
        ("i", SimpleImputer(strategy="median")),
        ("s", StandardScaler()),
        ("m", RidgeCV(alphas=np.logspace(-2, 3, 24)))])

def gbm():
    return HistGradientBoostingRegressor(
        max_depth=3, learning_rate=0.05, max_iter=300,
        min_samples_leaf=30, l2_regularization=1.0,
        random_state=0)

def walk(d, cols):
    out = []
    for T in TESTS:
        tr = d[d["label_season"] < T]
        te = d[d["label_season"] == T]
        if len(te) < 25 or len(tr) < 150:
            continue
        Xtr, ytr = tr[cols].values, tr["y"].values
        Xte, yte = te[cols].values, te["y"].values
        nv = te["ppg"].values
        rd = ridge().fit(Xtr, ytr).predict(Xte)
        gb = gbm().fit(Xtr, ytr).predict(Xte)
        out.append([np.mean(np.abs(nv - yte)),
                    np.mean(np.abs(rd - yte)),
                    np.mean(np.abs(gb - yte)),
                    np.sqrt(np.mean((rd - yte) ** 2)),
                    float(len(te))])
    if not out:
        return None
    a = np.array(out)
    w = a[:, 4]
    return [float((a[:, i] * w).sum() / w.sum())
            for i in range(4)] + [float(w.sum())]

print("\n" + "=" * 60)
print("=== WALK-FORWARD, %d HOLDOUT SEASONS ===" % len(TESTS))
print("  naive = last year's ppg, unchanged\n")
print("  %-4s %-6s %4s %6s %7s %7s %7s %8s"
      % ("pos", "set", "n", "naive", "ridge", "GBM",
         "rRMSE", "gain"))
print("  " + "-" * 58)
BEST = {}
for p in ["RB", "WR", "TE"]:
    d = D[D["position"] == p].copy()
    for lab, cs in [("full", FEAT[p]), ("core", CORE[p])]:
        r = walk(d, cs)
        if r is None:
            continue
        g = 100 * (1 - min(r[1], r[2]) / r[0])
        print("  %-4s %-6s %4d %6.3f %7.3f %7.3f %7.3f %+7.1f%%"
              % (p, lab, r[4], r[0], r[1], r[2], r[3], g))
        k = (p, lab)
        BEST[k] = (min(r[1], r[2]), r[0], r[3], cs)

print("\n=== VERDICT BY POSITION ===")
for p in ["RB", "WR", "TE"]:
    ks = [k for k in BEST if k[0] == p]
    if not ks:
        continue
    k = min(ks, key=lambda x: BEST[x][0])
    m, nv, rm, cs = BEST[k]
    gain = 100 * (1 - m / nv)
    ok = gain > 2.0
    print("  %-4s best=%-5s MAE %.3f vs naive %.3f  %+.1f%%  -> %s"
          % (p, k[1], m, nv, gain,
             "ADOPT" if ok else "KEEP NAIVE"))
    if ok:
        tr = D[(D["position"] == p)
               & (D["label_season"] < 2026)]
        mo = ridge().fit(tr[cs].values, tr["y"].values)
        co = mo.named_steps["m"].coef_
        print("       residual sd for the sim: %.2f ppg" % rm)
        print("       standardized coefficients:")
        for a, b in sorted(zip(cs, co), key=lambda x: -abs(x[1])):
            print("         %-12s %+7.3f" % (a, b))
