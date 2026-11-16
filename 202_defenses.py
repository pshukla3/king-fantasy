import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"].astype(str), SC["value"]))

def sv(k, d=0.0):
    got = k in V
    if not got:
        MISS.append(k)
    return float(V.get(k, d))

MISS = []
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}
YRS = [2022, 2023, 2024, 2025]

W = pl(nfl.load_player_stats(seasons=YRS))
CNT = ["def_sacks", "def_interceptions", "def_tds",
       "def_safeties", "def_punt_blocks", "def_pat_blocks",
       "def_fg_blocks", "fumble_recovery_opp",
       "special_teams_tds", "passing_yards", "rushing_yards"]
for c in CNT:
    if c not in W.columns:
        W[c] = 0.0
    W[c] = pd.to_numeric(W[c], errors="coerce").fillna(0.0)
W["team"] = W["team"].astype(str).replace(FIX)
W["opponent_team"] = W["opponent_team"].astype(str).replace(FIX)

G = W.groupby(["team", "season", "week"]).agg(
    sack=("def_sacks", "sum"),
    intc=("def_interceptions", "sum"),
    fr=("fumble_recovery_opp", "sum"),
    dtd=("def_tds", "sum"),
    saf=("def_safeties", "sum"),
    b1=("def_punt_blocks", "sum"),
    b2=("def_pat_blocks", "sum"),
    b3=("def_fg_blocks", "sum"),
    sttd=("special_teams_tds", "sum")).reset_index()
G["blk"] = G["b1"] + G["b2"] + G["b3"]

Y = W.groupby(["opponent_team", "season", "week"]).agg(
    py=("passing_yards", "sum"),
    ry=("rushing_yards", "sum")).reset_index()
Y["yds"] = Y["py"] + Y["ry"]
Y = Y.rename(columns={"opponent_team": "team"})[
    ["team", "season", "week", "yds"]]
G = G.merge(Y, on=["team", "season", "week"], how="left")

S = pl(nfl.load_schedules(seasons=YRS))
S = S[S["home_score"].notna()]
pa = []
for _, r in S.iterrows():
    h = FIX.get(str(r["home_team"]), str(r["home_team"]))
    a = FIX.get(str(r["away_team"]), str(r["away_team"]))
    pa.append({"team": h, "season": int(r["season"]),
               "week": int(r["week"]),
               "pa": float(r["away_score"])})
    pa.append({"team": a, "season": int(r["season"]),
               "week": int(r["week"]),
               "pa": float(r["home_score"])})
PA = pd.DataFrame(pa)
G = G.merge(PA, on=["team", "season", "week"], how="inner")
print("team-games with full stat line: %d" % len(G))
print("yards allowed per game: mean %.0f (sanity ~330)"
      % G["yds"].mean())
print("points allowed per game: mean %.1f (sanity ~22)"
      % G["pa"].mean())

def ptier(p):
    if p <= 0:
        return sv("pts_allow_0", 10.0)
    if p <= 6:
        return sv("pts_allow_1_6", 7.0)
    if p <= 13:
        return sv("pts_allow_7_13", 4.0)
    if p <= 20:
        return sv("pts_allow_14_20", 1.0)
    if p <= 27:
        return sv("pts_allow_21_27", 0.0)
    if p <= 34:
        return sv("pts_allow_28_34", -1.0)
    return sv("pts_allow_35p", -4.0)

def ytier(y):
    if y < 100:
        return sv("yds_allow_0_100", 5.0)
    if y < 200:
        return sv("yds_allow_100_199", 3.0)
    if y < 300:
        return sv("yds_allow_200_299", 2.0)
    if y < 350:
        return sv("yds_allow_300_349", 0.0)
    if y < 400:
        return sv("yds_allow_350_399", -1.0)
    if y < 450:
        return sv("yds_allow_400_449", -3.0)
    if y < 500:
        return sv("yds_allow_450_499", -5.0)
    if y < 550:
        return sv("yds_allow_500_549", -6.0)
    return sv("yds_allow_550p", -7.0)

G["fp"] = (G["sack"] * sv("sack", 1.0)
           + G["intc"] * sv("int", 2.0)
           + G["fr"] * sv("fum_rec", 2.0)
           + G["dtd"] * sv("def_td", 6.0)
           + G["sttd"] * sv("st_td", 6.0)
           + G["saf"] * sv("safe", 2.0)
           + G["blk"] * sv("blk_kick", 2.0)
           + G["pa"].apply(ptier)
           + G["yds"].fillna(340).apply(ytier))

print("=== SCORING KEYS NOT IN YOUR LEAGUE FILE ===")
print("  defaulted: %s" % sorted(set(MISS)) or "none")

T = G.groupby(["team", "season"]).agg(
    fp=("fp", "sum"), g=("week", "nunique")).reset_index()
T = T[T["g"] >= 14].copy()
T["ppg"] = T["fp"] / T["g"]
LGM = float(T["ppg"].mean())

N = T.copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "nxt"})[
    ["team", "season", "nxt"]]
P = T.merge(N, on=["team", "season"], how="inner")
R = float(P["ppg"].corr(P["nxt"]))
print("\n=== DOES DEFENSE PERSIST? ===")
print("  n = %d team-season pairs" % len(P))
print("  DST ppg year N vs N+1   r = %+.3f" % R)
print("  league mean %.2f ppg | sd %.2f"
      % (LGM, T["ppg"].std()))
print("  shrink factor applied = %.3f" % max(R, 0.0))

def ptier(p):
    if p <= 0:
        return sv("pts_allow_0", 10.0)
    if p <= 6:
        return sv("pts_allow_1_6", 7.0)
    if p <= 13:
        return sv("pts_allow_7_13", 4.0)
    if p <= 20:
        return sv("pts_allow_14_20", 1.0)
    if p <= 27:
        return sv("pts_allow_21_27", 0.0)
    if p <= 34:
        return sv("pts_allow_28_34", -1.0)
    return sv("pts_allow_35p", -4.0)

def ytier(y):
    if y < 100:
        return sv("yds_allow_0_100", 5.0)
    if y < 200:
        return sv("yds_allow_100_199", 3.0)
    if y < 300:
        return sv("yds_allow_200_299", 2.0)
    if y < 350:
        return sv("yds_allow_300_349", 0.0)
    if y < 400:
        return sv("yds_allow_350_399", -1.0)
    if y < 450:
        return sv("yds_allow_400_449", -3.0)
    if y < 500:
        return sv("yds_allow_450_499", -5.0)
    if y < 550:
        return sv("yds_allow_500_549", -6.0)
    return sv("yds_allow_550p", -7.0)

G["fp"] = (G["sack"] * sv("sack", 1.0)
           + G["intc"] * sv("int", 2.0)
           + G["fr"] * sv("fum_rec", 2.0)
           + G["dtd"] * sv("def_td", 6.0)
           + G["sttd"] * sv("st_td", 6.0)
           + G["saf"] * sv("safe", 2.0)
           + G["blk"] * sv("blk_kick", 2.0)
           + G["pa"].apply(ptier)
           + G["yds"].fillna(340).apply(ytier))

print("=== SCORING KEYS NOT IN YOUR LEAGUE FILE ===")
print("  defaulted: %s" % sorted(set(MISS)) or "none")

T = G.groupby(["team", "season"]).agg(
    fp=("fp", "sum"), g=("week", "nunique")).reset_index()
T = T[T["g"] >= 14].copy()
T["ppg"] = T["fp"] / T["g"]
LGM = float(T["ppg"].mean())

N = T.copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "nxt"})[
    ["team", "season", "nxt"]]
P = T.merge(N, on=["team", "season"], how="inner")
R = float(P["ppg"].corr(P["nxt"]))
print("\n=== DOES DEFENSE PERSIST? ===")
print("  n = %d team-season pairs" % len(P))
print("  DST ppg year N vs N+1   r = %+.3f" % R)
print("  league mean %.2f ppg | sd %.2f"
      % (LGM, T["ppg"].std()))
print("  shrink factor applied = %.3f" % max(R, 0.0))

CITY = {"ARI": "Arizona", "ATL": "Atlanta",
        "BAL": "Baltimore", "BUF": "Buffalo",
        "CAR": "Carolina", "CHI": "Chicago",
        "CIN": "Cincinnati", "CLE": "Cleveland",
        "DAL": "Dallas", "DEN": "Denver",
        "DET": "Detroit", "GB": "Green Bay",
        "HOU": "Houston", "IND": "Indianapolis",
        "JAX": "Jacksonville", "KC": "Kansas City",
        "LA": "LA Rams", "LAC": "LA Chargers",
        "LV": "Las Vegas", "MIA": "Miami",
        "MIN": "Minnesota", "NE": "New England",
        "NO": "New Orleans", "NYG": "NY Giants",
        "NYJ": "NY Jets", "PHI": "Philadelphia",
        "PIT": "Pittsburgh", "SEA": "Seattle",
        "SF": "San Francisco", "TB": "Tampa Bay",
        "TEN": "Tennessee", "WAS": "Washington"}

DEC = 0.5
rows = []
for t in sorted(CITY):
    d = T[T["team"] == t]
    if len(d):
        w = DEC ** (2025 - d["season"])
        base = float((w * d["ppg"]).sum() / w.sum())
    else:
        base = LGM
    proj = LGM + max(R, 0.0) * (base - LGM)
    rows.append({"team": t, "recent": base,
                 "proj": round(proj, 2)})
X = pd.DataFrame(rows).sort_values("proj",
                                   ascending=False)
X.to_csv("dst_2026.csv", index=False)

print("\n=== 2026 DEFENSE PROJECTIONS, ALL 32 ===")
print("  %-3s %-5s %-16s %8s %8s"
      % ("#", "tm", "defense", "recent", "PROJ"))
for i, (_, r) in enumerate(X.iterrows()):
    print("  %-3d %-5s %-16s %8.2f %8.2f"
          % (i + 1, r["team"], CITY[r["team"]],
             r["recent"], r["proj"]))
print("\n  spread top to bottom: %.2f ppg"
      % (X["proj"].max() - X["proj"].min()))
print("  raw spread before shrink: %.2f ppg"
      % (X["recent"].max() - X["recent"].min()))

B = pd.read_csv("board_final.csv", low_memory=False)
old = B[B["position"].astype(str).isin(["DST", "DEF"])]
assert len(old), "no existing DST row to use as template"
tpl = old.iloc[0].to_dict()
B = B[~B["position"].astype(str).isin(["DST", "DEF"])]

new = []
for _, r in X.iterrows():
    d = dict(tpl)
    d["player_id"] = "DEF_%s" % r["team"]
    d["player_display_name"] = "%s Defense" % CITY[r["team"]]
    d["position"] = "DST"
    d["team"] = r["team"]
    d["points"] = float(r["proj"])
    d["exp_games"] = 17.0
    d["status"] = np.nan
    d["depth_rank"] = np.nan
    d["adp"] = np.nan
    d["games_mult"] = 1.0
    d["points_mult"] = 1.0
    new.append(d)
B = pd.concat([B, pd.DataFrame(new)], ignore_index=True)
B.to_csv("board_final.csv", index=False)
n = int((B["position"] == "DST").sum())
print("\nboard rows %d | DST rows %d" % (len(B), n))
assert n == 32, "expected 32 defenses, got %d" % n

p = "200_live_teams.py"
s = open(p).read()
o = ('for _, r in B[B["position"].isin(["DST", "DEF"])]'
     '.iterrows():\n    t = str(r["team"]).upper()\n'
     '    if t and t != "NAN":\n        OUT[t] = rec(r)')
nw = ('ALIAS = {"LA": ["LAR"], "WAS": ["WSH"],\n'
      '         "JAX": ["JAC"], "ARI": ["AZ"]}\n'
      + o + '\n        for _a in ALIAS.get(t, []):\n'
      '            OUT[_a] = rec(r)')
if "ALIAS" in s:
    print("200 already alias-aware")
elif o in s:
    open(p, "w").write(s.replace(o, nw, 1))
    print("200 patched: LAR/WSH/JAC/AZ aliases added")
else:
    print("WARNING: could not patch 200 - check DST block")
print("OK")
