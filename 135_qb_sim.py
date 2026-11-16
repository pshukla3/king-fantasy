import numpy as np
import pandas as pd

NSIM = 200000
WEEKS = 14
rng = np.random.default_rng(2026)

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
Q = H[H["position"] == "QB"].copy()
for c in ["attempts", "passing_yards", "passing_tds",
          "rushing_yards", "rushing_tds"]:
    Q[c] = pd.to_numeric(Q[c], errors="coerce").fillna(0)
G = Q[Q["attempts"] >= 15].copy()

G["ypa"] = G["passing_yards"] / G["attempts"]
SD_ATT = G["attempts"].std()
SD_YPA = G["ypa"].std()
SD_RY = G["rushing_yards"].std()
print("=== MEASURED GAME-LEVEL DISPERSION ===")
print("  QB starts in sample: %d" % len(G))
print("  attempts   mean %.1f  sd %.1f"
      % (G["attempts"].mean(), SD_ATT))
print("  yds/att    mean %.2f  sd %.2f"
      % (G["ypa"].mean(), SD_YPA))
print("  rush yds   mean %.1f  sd %.1f"
      % (G["rushing_yards"].mean(), SD_RY))
LGI = (pd.to_numeric(Q["interceptions"], errors="coerce")
       .fillna(0).sum() / Q["attempts"].sum()
       if "interceptions" in Q.columns else 0.0265)
print("  int rate   %.4f %s"
      % (LGI, "measured" if "interceptions" in Q.columns
         else "LEAGUE DEFAULT, col missing"))

S = Q.groupby(["player_id", "season"]).agg(
    att=("attempts", "sum"),
    td=("passing_tds", "sum")).reset_index()
S = S[S["att"] >= 100]
LG = S["td"].sum() / S["att"].sum()
CAR = S.groupby("player_id").agg(
    catt=("att", "sum"), ctd=("td", "sum")).reset_index()
K = 400

SP = pd.read_csv("stat_projections_2026.csv",
                 low_memory=False)
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
PY, PT, PI = (float(V["pass_yd"]), float(V["pass_td"]),
              float(V["pass_int"]))
RY, RT = float(V["rush_yd"]), float(V["rush_td"])

X = SP[SP["position"] == "QB"].copy()
for c in ["attempts", "passing_yards", "passing_tds",
          "rushing_yards", "rushing_tds"]:
    X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
X = X.merge(CAR, on="player_id", how="left")
X["catt"] = X["catt"].fillna(0)
X["tdp"] = np.where(X["attempts"] > 0,
                    X["passing_tds"] / X["attempts"], LG)
X["tdr"] = ((X["tdp"] * X["catt"] + LG * K)
            / (X["catt"] + K))
X["ypa"] = np.where(X["attempts"] > 0,
                    X["passing_yards"] / X["attempts"], 6.8)

B = pd.read_csv("board_final.csv", low_memory=False)
B = B[B["position"] == "QB"][
    ["player_id", "exp_games", "depth_rank", "team"]]
X = X.merge(B, on="player_id", how="left",
            suffixes=("", "_b"))
X = X[X["depth_rank"] == 1].copy()
X["avail"] = (X["exp_games"] / 17.0).clip(0, 1)

def sim(r, n, weeks=WEEKS):
    a = np.maximum(rng.normal(r["attempts"], SD_ATT,
                              (weeks, n)), 0)
    yp = rng.normal(r["ypa"], SD_YPA, (weeks, n))
    yd = np.maximum(a * yp, 0)
    td = rng.binomial(np.rint(a).astype(int), r["tdr"])
    it = rng.binomial(np.rint(a).astype(int), LGI)
    ry = np.maximum(rng.normal(r["rushing_yards"],
                               SD_RY, (weeks, n)), 0)
    rt = rng.poisson(max(r["rushing_tds"], 0.001),
                     (weeks, n))
    pts = yd * PY + td * PT + it * PI + ry * RY + rt * RT
    return pts, yd, td, it, ry, rt

rows = []
for _, r in X.iterrows():
    p, yd, td, it, ry, rt = sim(r, 4000)
    play = rng.random((WEEKS, 4000)) < r["avail"]
    rows.append({
        "nm": str(r["player_display_name"]),
        "tm": str(r["team"]),
        "ppg": p.mean(),
        "yds": (yd * play).sum(axis=0).mean(),
        "ptd": (td * play).sum(axis=0).mean(),
        "int": (it * play).sum(axis=0).mean(),
        "ryd": (ry * play).sum(axis=0).mean(),
        "rtd": (rt * play).sum(axis=0).mean(),
        "tot": (p * play).sum(axis=0).mean(),
        "p10": np.percentile((p * play).sum(axis=0), 10),
        "p90": np.percentile((p * play).sum(axis=0), 90),
        "av": r["avail"]})
R = pd.DataFrame(rows).sort_values("tot", ascending=False)
R = R.reset_index(drop=True)
R["qbr"] = R.index + 1
REPL = float(R.iloc[9]["tot"])

print("\n=== 2026 QB RANKINGS, 14-WEEK SEASON ===")
print("  totals include missed games as zero\n")
print("  %-3s %-21s %-4s %5s %5s %4s %5s %4s"
      " %6s %6s %6s"
      % ("#", "player", "tm", "pYds", "pTD", "INT",
         "rYds", "rTD", "TOTAL", "p10", "p90"))
print("  " + "-" * 78)
for _, r in R.iterrows():
    print("  %-3d %-21s %-4s %5.0f %5.1f %4.1f %5.0f"
          " %4.1f %6.0f %6.0f %6.0f"
          % (r["qbr"], r["nm"][:21], r["tm"][:4],
             r["yds"], r["ptd"], r["int"], r["ryd"],
             r["rtd"], r["tot"], r["p10"], r["p90"]))
print("\n  replacement (QB10) = %.0f pts" % REPL)

BIG = 50000000
CH = 40
BYE = {"CHI": 10, "CIN": 6}
STREAM = float(R.iloc[14]["tot"]) / WEEKS

def grab(nm):
    h = X[X["player_display_name"].astype(str)
          .str.contains(nm, na=False)]
    return h.iloc[0]

A = grab("Caleb Williams")
Bq = grab("Joe Burrow")
print("\n=== HEAD TO HEAD ===")
for r in (A, Bq):
    print("  %-20s %-4s att %.1f ypa %.2f tdr %.3f"
          " avail %.2f bye %d"
          % (str(r["player_display_name"])[:20],
             str(r["team"]), r["attempts"], r["ypa"],
             r["tdr"], r["avail"],
             BYE.get(str(r["team"]), 0)))
print("  missed weeks backfilled by a streamer"
      " at %.2f ppg" % STREAM)
print("  running %d sims in %d chunks..." % (BIG, CH))

wa = wb = 0
sa = sb = 0.0
n = BIG // CH
for c in range(CH):
    ta = np.zeros(n)
    tb = np.zeros(n)
    for r, acc in ((A, "a"), (Bq, "b")):
        p, _, _, _, _, _ = sim(r, n)
        pl = rng.random((WEEKS, n)) < r["avail"]
        bw = BYE.get(str(r["team"]), 0)
        if 1 <= bw <= WEEKS:
            pl[bw - 1, :] = False
        v = np.where(pl, p, STREAM).sum(axis=0)
        if acc == "a":
            ta = v
        else:
            tb = v
    wa += int((ta > tb).sum())
    wb += int((tb > ta).sum())
    sa += float(ta.sum())
    sb += float(tb.sum())
    if (c + 1) % 10 == 0:
        print("    chunk %d/%d" % (c + 1, CH))

pa = 100.0 * wa / BIG
se = 100.0 * (pa / 100 * (1 - pa / 100) / BIG) ** 0.5
print("\n  Caleb Williams season pts  %.1f" % (sa / BIG))
print("  Joe Burrow season pts      %.1f" % (sb / BIG))
print("  difference                 %+.1f"
      % (sb / BIG - sa / BIG))
print("\n  P(Burrow outscores Williams) = %.2f%%"
      % (100.0 - pa))
print("  standard error = %.4f%%" % se)
print("  at 1e9 sims the SE would be %.4f%%"
      % (se / (1000 ** 0.5)))
