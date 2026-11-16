import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(d):
    return d.to_pandas() if hasattr(d, "to_pandas") else d

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}

S = pd.read_csv("pos_season_panel.csv", low_memory=False)
D = pd.read_csv("pos_pairs.csv", low_memory=False)
B = pd.read_csv("board_final.csv", low_memory=False)

B["t26"] = B["team"].astype(str).replace(FIX)
T26 = (B.drop_duplicates("player_id")
       .set_index("player_id")["t26"].to_dict())

X = S[S["season"] == 2025].copy()
X["n_team"] = X["player_id"].map(T26)
print("2025 season rows: %d | with a 2026 team: %d"
      % (len(X), int(X["n_team"].notna().sum())))
X = X[X["n_team"].notna()].copy()
X["moved"] = (X["team"] != X["n_team"]).astype(int)

TV = (S[S["season"] == 2025][["team", "t_tpg", "t_cpg"]]
      .drop_duplicates("team")
      .rename(columns={"team": "n_team",
                       "t_tpg": "n_tpg",
                       "t_cpg": "n_cpg"}))
X = X.merge(TV, on="n_team", how="left")

PL = pl(nfl.load_players())
idc = "gsis_id" if "gsis_id" in PL.columns else "player_id"
PL = PL[[idc, "birth_date", "draft_pick"]].rename(
    columns={idc: "player_id"}).drop_duplicates("player_id")
PL["by"] = pd.to_datetime(PL["birth_date"],
                          errors="coerce").dt.year
X = X.merge(PL[["player_id", "by", "draft_pick"]],
            on="player_id", how="left")
X["age"] = 2026 - X["by"]

print("\n  players moving teams: %d" % int(X["moved"].sum()))
print("  age attached %.0f%% | draft %.0f%%"
      % (100 * X["age"].notna().mean(),
         100 * X["draft_pick"].notna().mean()))
print(X.groupby("position").size().to_string())

from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor

WIN = {
    "RB": ["ppg", "cpg", "tpg", "car_share", "opp_share",
           "ypc", "rtdr", "ctch", "age", "draft_pick",
           "moved", "n_cpg", "g"],
    "WR": ["ppg", "tpg", "tar_share", "ctch", "ypr", "tdr",
           "ay_share", "age", "draft_pick", "moved",
           "n_tpg", "g"],
    "TE": ["ppg", "tpg", "age", "ay_share", "draft_pick",
           "moved"],
}

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

SD = pd.read_csv("resid_sd_fit.csv").set_index("pos")
Z = np.load("resid_pool.npz")

out = []
for p, cols in WIN.items():
    tr = D[D["position"] == p]
    te = X[X["position"] == p].copy()
    if len(te) == 0:
        continue
    Xtr, ytr = tr[cols].values, tr["y"].values
    pr = 0.5 * (ridge().fit(Xtr, ytr).predict(te[cols].values)
                + gbm().fit(Xtr, ytr).predict(te[cols].values))
    a, b = float(SD.loc[p, "a"]), float(SD.loc[p, "b"])
    sd = np.clip(a + b * pr, 0.5, None)
    z = Z[p]
    te["proj"] = pr
    te["sd"] = sd
    for q, lab in [(10, "p10"), (50, "p50"), (90, "p90")]:
        te[lab] = pr + sd * float(np.percentile(z, q))
    out.append(te[["player_id", "position", "n_team",
                   "ppg", "age", "moved", "proj", "sd",
                   "p10", "p50", "p90"]])

P = pd.concat(out, ignore_index=True)
P = P.rename(columns={"ppg": "ppg25", "n_team": "team"})
nm = B.drop_duplicates("player_id")[
    ["player_id", "player_display_name", "adp"]]
P = P.merge(nm, on="player_id", how="left")
P.to_csv("proj_2026.csv", index=False)
print("\nprojected %d players -> proj_2026.csv" % len(P))
print("  mean over all: %.2f ppg" % P["proj"].mean())

OLD = B.drop_duplicates("player_id").set_index(
    "player_id")["points"].to_dict()
P["old"] = P["player_id"].map(OLD)

for p in ["WR", "RB", "TE"]:
    d = P[P["position"] == p].nlargest(18, "proj")
    print("\n=== 2026 %s, NEW MODEL ===" % p)
    print("  proj is the MEAN. p50 is the median outcome,")
    print("  which sits lower because upside is skewed.\n")
    print("  %-3s %-22s %-4s %6s %6s %6s %6s %6s %7s %6s"
          % ("#", "player", "tm", "2025", "PROJ", "p10",
             "p50", "p90", "old", "ADP"))
    print("  " + "-" * 76)
    for i, (_, r) in enumerate(d.iterrows()):
        o = r["old"]
        a = r["adp"]
        print("  %-3d %-22s %-4s %6.2f %6.2f %6.2f %6.2f"
              " %6.2f %7s %6s"
              % (i + 1,
                 str(r["player_display_name"])[:22],
                 str(r["team"])[:4], r["ppg25"], r["proj"],
                 r["p10"], r["p50"], r["p90"],
                 "--" if o != o else "%.2f" % o,
                 "--" if a != a else "%.1f" % a))

print("\n=== BIGGEST MOVES vs THE OLD BOARD ===")
M = P[P["old"].notna() & (P["old"] > 3)].copy()
M["mv"] = M["proj"] - M["old"]
print("\n  MODEL LIKES MORE:")
for _, r in M.nlargest(10, "mv").iterrows():
    print("    %-22s %-4s %-3s %6.2f -> %6.2f  %+.2f"
          % (str(r["player_display_name"])[:22],
             str(r["team"])[:4], r["position"],
             r["old"], r["proj"], r["mv"]))
print("\n  MODEL LIKES LESS:")
for _, r in M.nsmallest(10, "mv").iterrows():
    print("    %-22s %-4s %-3s %6.2f -> %6.2f  %+.2f"
          % (str(r["player_display_name"])[:22],
             str(r["team"])[:4], r["position"],
             r["old"], r["proj"], r["mv"]))
print("\n  mean absolute move: %.2f ppg" % M["mv"].abs().mean())
