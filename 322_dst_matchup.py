import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

K = ["game_id", "season", "week", "posteam", "defteam",
     "home_team", "away_team", "home_score", "away_score",
     "sack", "interception", "fumble_lost", "touchdown",
     "td_team", "safety", "yards_gained"]
rows = []
for yr in range(2015, 2026):
    d = pl(nfl.load_pbp(seasons=[yr]))
    rows.append(d[[c for c in K if c in d.columns]])
P = pd.concat(rows, ignore_index=True)
del rows
for c in ["sack", "interception", "fumble_lost", "touchdown",
          "safety", "home_score", "away_score", "yards_gained"]:
    P[c] = pd.to_numeric(P[c], errors="coerce").fillna(0)
print("plays %d" % len(P))

D = P[P["defteam"].notna()]
g = D.groupby(["season", "week", "game_id", "defteam"]).agg(
    sack=("sack", "sum"), intc=("interception", "sum"),
    fum=("fumble_lost", "sum"), saf=("safety", "sum")
).reset_index()
sc = P.groupby(["game_id", "home_team", "away_team"]).agg(
    hs=("home_score", "max"), a_s=("away_score", "max")
).reset_index()
pa, opp, hm = {}, {}, {}
for _, r in sc.iterrows():
    pa[(r["game_id"], r["home_team"])] = r["a_s"]
    pa[(r["game_id"], r["away_team"])] = r["hs"]
    opp[(r["game_id"], r["home_team"])] = r["away_team"]
    opp[(r["game_id"], r["away_team"])] = r["home_team"]
    hm[(r["game_id"], r["home_team"])] = 1
    hm[(r["game_id"], r["away_team"])] = 0
g["pa"] = [pa.get((a, b), np.nan) for a, b in
           zip(g["game_id"], g["defteam"])]
g["opp"] = [opp.get((a, b)) for a, b in
            zip(g["game_id"], g["defteam"])]
g["home"] = [hm.get((a, b), 0) for a, b in
             zip(g["game_id"], g["defteam"])]
td = P[(P["touchdown"] == 1) & P["td_team"].notna()]
td = td[td["td_team"] == td["defteam"]]
tc = td.groupby(["game_id", "defteam"]).size().to_dict()
g["dtd"] = [tc.get((a, b), 0) for a, b in
            zip(g["game_id"], g["defteam"])]

def pap(x):
    if x != x:
        return 0
    return (10 if x == 0 else 7 if x <= 6 else 4 if x <= 13
            else 1 if x <= 20 else 0 if x <= 27
            else -1 if x <= 34 else -4)

g["fp"] = (g["sack"] + 2 * g["intc"] + 2 * g["fum"]
           + 2 * g["saf"] + 6 * g["dtd"] + g["pa"].map(pap))
g = g.dropna(subset=["opp", "pa"])
print("defense-games: %d" % len(g))

O = P[P["posteam"].notna()].groupby(
    ["season", "posteam"]).agg(
    yds=("yards_gained", "sum"),
    tds=("touchdown", "sum")).reset_index()
gp = P[P["posteam"].notna()].groupby(
    ["season", "posteam"])["game_id"].nunique().reset_index()
gp.columns = ["season", "posteam", "gm"]
O = O.merge(gp, on=["season", "posteam"])
O["ypg"] = O["yds"] / O["gm"]
O["tdpg"] = O["tds"] / O["gm"]
pts = {}
for _, r in sc.iterrows():
    pts.setdefault(r["home_team"], []).append(r["hs"])
OP = P[P["posteam"].notna()].groupby(
    ["season", "game_id", "posteam"]).size().reset_index()
OP["sc"] = [pa.get((gid, opp.get((gid, t))), np.nan)
            for gid, t in zip(OP["game_id"], OP["posteam"])]
OS = OP.groupby(["season", "posteam"])["sc"].mean(
).reset_index()
OS.columns = ["season", "posteam", "ppg"]
O = O.merge(OS, on=["season", "posteam"])
print("team-season offenses: %d" % len(O))

DS = g.groupby(["season", "defteam"])["fp"].mean(
).reset_index()
DS.columns = ["season", "defteam", "own_ppg"]

g["py"] = g["season"] - 1
g = g.merge(DS.rename(columns={"season": "py",
                               "own_ppg": "own_prior"}),
            on=["py", "defteam"], how="left")
g = g.merge(O[["season", "posteam", "ppg", "ypg", "tdpg"]]
            .rename(columns={"season": "py", "posteam": "opp",
                             "ppg": "opp_ppg",
                             "ypg": "opp_ypg",
                             "tdpg": "opp_tdpg"}),
            on=["py", "opp"], how="left")
G = g.dropna(subset=["own_prior", "opp_ppg", "opp_ypg"])
print("usable rows (need prior season): %d" % len(G))

print("\n=== WALK-FORWARD: does the matchup help? ===")
print("  %-34s %8s" % ("model", "MAE"))
print("  " + "-" * 46)
yrs = sorted(G["season"].unique())[1:]
def run(cols):
    err = []
    for y in yrs:
        tr = G[G["season"] < y]
        te = G[G["season"] == y]
        if len(tr) < 300 or not len(te):
            continue
        X = np.column_stack([np.ones(len(tr))]
                            + [tr[c].values for c in cols])
        b = np.linalg.lstsq(X, tr["fp"].values, rcond=None)[0]
        Xt = np.column_stack([np.ones(len(te))]
                             + [te[c].values for c in cols])
        err.append(np.abs(Xt @ b - te["fp"].values).mean())
    return float(np.mean(err)) if err else np.nan

base = []
for y in yrs:
    tr, te = G[G["season"] < y], G[G["season"] == y]
    if len(tr) < 300 or not len(te):
        continue
    base.append(np.abs(te["fp"].values
                       - tr["fp"].mean()).mean())
print("  %-34s %8.3f" % ("league mean only", np.mean(base)))
for cols, lbl in [
        (["own_prior"], "own defense last year"),
        (["opp_ppg"], "opponent offense ppg"),
        (["own_prior", "opp_ppg"], "own + opponent"),
        (["own_prior", "opp_ppg", "home"], "+ home field"),
        (["own_prior", "opp_ppg", "opp_ypg", "opp_tdpg",
          "home"], "+ opp yards & TD rate")]:
    print("  %-34s %8.3f" % (lbl, run(cols)))

cols = ["own_prior", "opp_ppg", "opp_ypg", "opp_tdpg", "home"]
X = np.column_stack([np.ones(len(G))]
                    + [G[c].values for c in cols])
b = np.linalg.lstsq(X, G["fp"].values, rcond=None)[0]
print("\n=== FULL-SAMPLE COEFFICIENTS ===")
print("  intercept          %+8.3f" % b[0])
for i, c in enumerate(cols):
    print("  %-18s %+8.3f" % (c, b[i + 1]))
print("\n  read: every extra point per game the opponent")
print("  offense scored last year costs the defense")
print("  %.2f fantasy points." % abs(b[2]))
np.save("dst_coef.npy", b)
print("\nsaved dst_coef.npy")
