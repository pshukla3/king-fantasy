import pandas as pd
import numpy as np
import nflreadpy as nfl

YRS = list(range(2017, 2026))
print("pulling pbp for %s ..." % YRS)
P = nfl.load_pbp(seasons=YRS)
P = P.to_pandas() if hasattr(P, "to_pandas") else P
print("pbp rows: %d" % len(P))

def num(c):
    if c in P.columns:
        return pd.to_numeric(P[c], errors="coerce").fillna(0.0)
    print("  MISSING COLUMN: %s -> zeros" % c)
    return pd.Series(0.0, index=P.index)

def flag(c, val):
    if c in P.columns:
        return (P[c].astype(str) == val).astype(float)
    print("  MISSING COLUMN: %s -> zeros" % c)
    return pd.Series(0.0, index=P.index)

P["_sack"] = num("sack")
P["_int"] = num("interception")
P["_fum"] = num("fumble_lost")
P["_saf"] = num("safety")
P["_rtd"] = num("return_touchdown")
_scrim = (num("rush_attempt") + num("pass_attempt")) > 0
P["_yds"] = num("yards_gained") * _scrim
print("scrimmage plays: %d of %d"
      % (int(_scrim.sum()), len(P)))
P["_blk"] = (num("punt_blocked")
             + flag("field_goal_result", "blocked")
             + flag("extra_point_result", "blocked"))

print("\nblocked kicks found: %d" % int(P["_blk"].sum()))
print("return TDs found:    %d" % int(P["_rtd"].sum()))

D = P[P["defteam"].notna()].copy()
G = D.groupby(["season", "week", "defteam"]).agg(
    sack=("_sack", "sum"), intc=("_int", "sum"),
    fum=("_fum", "sum"), saf=("_saf", "sum"),
    rtd=("_rtd", "sum"), blk=("_blk", "sum"),
    ya=("_yds", "sum")).reset_index()
print("\nteam-games: %d" % len(G))
print("mean yards allowed/game: %.1f" % G["ya"].mean())

S = nfl.load_schedules(seasons=YRS)
S = S.to_pandas() if hasattr(S, "to_pandas") else S
if "game_type" in S.columns:
    S = S[S["game_type"] == "REG"]
S = S.dropna(subset=["home_score", "away_score"])

rows = []
for _, r in S.iterrows():
    rows.append({"season": int(r["season"]), "week": int(r["week"]),
                 "defteam": r["home_team"], "pa": r["away_score"]})
    rows.append({"season": int(r["season"]), "week": int(r["week"]),
                 "defteam": r["away_team"], "pa": r["home_score"]})
G = G.merge(pd.DataFrame(rows), on=["season", "week", "defteam"],
            how="inner")
print("after points allowed merge: %d" % len(G))

def pa_pts(x):
    if x == 0: return 10.0
    if x <= 6: return 7.0
    if x <= 13: return 4.0
    if x <= 20: return 1.0
    if x <= 27: return 0.0
    if x <= 34: return -1.0
    return -4.0

def ya_pts(y):
    if y < 100: return 10.0
    if y < 200: return 7.0
    if y < 300: return 5.0
    if y < 350: return 3.0
    if y < 400: return 0.0
    if y < 450: return -1.0
    if y < 500: return -3.0
    if y < 550: return -5.0
    return -7.0

G["turnover_pts"] = (G["sack"] * 1.0 + G["intc"] * 2.0
                     + G["fum"] * 2.0 + G["saf"] * 2.0
                     + G["blk"] * 2.0 + G["rtd"] * 6.0)
G["pa_pts"] = G["pa"].apply(pa_pts)
G["ya_pts"] = G["ya"].apply(ya_pts)
G["dst_pts"] = G["turnover_pts"] + G["pa_pts"] + G["ya_pts"]
G.to_csv("dst_weekly_v2.csv", index=False)

print("\n=== SLEEPER SCORING, LEAGUE-WIDE ===")
print("  mean %.2f | median %.2f | sd %.2f"
      % (G["dst_pts"].mean(), G["dst_pts"].median(),
         G["dst_pts"].std()))
print("  10th %.1f | 90th %.1f"
      % (G["dst_pts"].quantile(.10), G["dst_pts"].quantile(.90)))

def persist(col):
    T = G.groupby(["season", "defteam"])[col].mean().reset_index()
    nx = T.copy()
    nx["season"] = nx["season"] - 1
    nx = nx.rename(columns={col: "next"})
    M = T.merge(nx, on=["season", "defteam"], how="inner")
    return M[col].corr(M["next"]), len(M)

print("\n=== REPEATABILITY BY COMPONENT (year N vs N+1) ===")
for c, lbl in [("turnover_pts", "turnovers+sacks+TDs"),
               ("pa_pts", "points allowed"),
               ("ya_pts", "yards allowed"),
               ("dst_pts", "TOTAL (Sleeper)")]:
    r, n = persist(c)
    print("  %-22s r = %+.3f  (n=%d)" % (lbl, r, n))
print("\n  my earlier incomplete version:  r = +0.242")
print("  compare WR 0.765 | RB 0.709 | QB 0.560")
