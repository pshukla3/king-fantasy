import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

K = ["game_id", "season", "week", "posteam", "defteam",
     "home_team", "away_team", "home_score", "away_score",
     "sack", "interception", "fumble_lost", "touchdown",
     "td_team", "safety", "play_type"]
rows = []
for yr in range(2015, 2026):
    d = pl(nfl.load_pbp(seasons=[yr]))
    d = d[[c for c in K if c in d.columns]]
    rows.append(d[d["defteam"].notna()])
    print("  %d loaded" % yr)
P = pd.concat(rows, ignore_index=True)
del rows
for c in ["sack", "interception", "fumble_lost",
          "touchdown", "safety", "home_score", "away_score"]:
    if c in P.columns:
        P[c] = pd.to_numeric(P[c], errors="coerce").fillna(0)
print("plays %d" % len(P))

g = P.groupby(["season", "game_id", "defteam"]).agg(
    sack=("sack", "sum"),
    intc=("interception", "sum"),
    fum=("fumble_lost", "sum"),
    saf=("safety", "sum")).reset_index()

sc = P.groupby(["game_id", "home_team", "away_team"]).agg(
    hs=("home_score", "max"), a_s=("away_score", "max")
).reset_index()
pa = {}
for _, r in sc.iterrows():
    pa[(r["game_id"], r["home_team"])] = r["a_s"]
    pa[(r["game_id"], r["away_team"])] = r["hs"]
g["pa"] = [pa.get((a, b), np.nan)
           for a, b in zip(g["game_id"], g["defteam"])]

td = P[(P["touchdown"] == 1) & P["td_team"].notna()]
td = td[td["td_team"] == td["defteam"]]
tdc = td.groupby(["game_id", "defteam"]).size().to_dict()
g["dtd"] = [tdc.get((a, b), 0)
            for a, b in zip(g["game_id"], g["defteam"])]

def pa_pts(x):
    if x != x:
        return 0
    if x == 0:
        return 10
    if x <= 6:
        return 7
    if x <= 13:
        return 4
    if x <= 20:
        return 1
    if x <= 27:
        return 0
    if x <= 34:
        return -1
    return -4

g["fp"] = (g["sack"] * 1 + g["intc"] * 2 + g["fum"] * 2
           + g["saf"] * 2 + g["dtd"] * 6
           + g["pa"].map(pa_pts))
S = g.groupby(["season", "defteam"]).agg(
    gm=("fp", "size"), fp=("fp", "mean"),
    sack=("sack", "mean"), intc=("intc", "mean"),
    fum=("fum", "mean"), dtd=("dtd", "mean"),
    pa=("pa", "mean")).reset_index()
S = S[S["gm"] >= 14]
print("team-seasons: %d" % len(S))

print("\n=== YEAR-OVER-YEAR PERSISTENCE ===")
print("  how much does last season predict this one?")
print("  %-22s %8s %8s" % ("component", "corr", "r2"))
print("  " + "-" * 42)
res = {}
for col, lbl in [("fp", "DST fantasy ppg"),
                 ("sack", "sacks/game"),
                 ("intc", "interceptions/game"),
                 ("fum", "fumble recoveries/gm"),
                 ("dtd", "defensive TDs/game"),
                 ("pa", "points allowed/game")]:
    a, b = [], []
    for t in S["defteam"].unique():
        d = S[S["defteam"] == t].sort_values("season")
        v = d[col].values
        y = d["season"].values
        for i in range(len(v) - 1):
            if y[i + 1] == y[i] + 1:
                a.append(v[i])
                b.append(v[i + 1])
    if len(a) < 40:
        continue
    c = float(np.corrcoef(a, b)[0, 1])
    res[col] = c
    print("  %-22s %+8.3f %8.3f" % (lbl, c, c * c))

print("\n=== WHAT THIS MEANS ===")
r = res.get("fp", 0)
print("  DST scoring persists at r=%.2f, so last season"
      % r)
print("  explains only %.0f%% of this season's variance."
      % (100 * r * r))
print("  A projection should therefore sit mostly at the")
print("  league mean, shrunk by that measured factor.")

last = S[S["season"] == S["season"].max()]
mu = float(last["fp"].mean())
sd = float(last["fp"].std())
print("\n  %d league mean %.2f ppg (sd %.2f)"
      % (S["season"].max(), mu, sd))
print("\n  best/worst last season, and what the measured")
print("  shrinkage projects for next year:")
last = last.sort_values("fp", ascending=False)
sh = max(0.0, r)
for _, x in pd.concat([last.head(5), last.tail(5)]).iterrows():
    proj = mu + sh * (x["fp"] - mu)
    print("    %-4s %5.2f ppg  ->  %5.2f projected"
          % (x["defteam"], x["fp"], proj))

out = []
for _, x in last.iterrows():
    out.append({"team": x["defteam"],
                "last_ppg": round(float(x["fp"]), 2),
                "proj_ppg": round(mu + sh * (x["fp"] - mu), 2),
                "sacks_g": round(float(x["sack"]), 2),
                "pa_g": round(float(x["pa"]), 1)})
pd.DataFrame(out).to_csv("dst_proj.csv", index=False)
print("\nwrote dst_proj.csv (%d teams, shrink=%.2f)"
      % (len(out), sh))
