import numpy as np
import pandas as pd
import os

WEEKS = 17
rng = np.random.default_rng(2026)
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX"}

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
TC = "team" if "team" in H.columns else "recent_team"
for c in ["attempts", "passing_yards", "passing_tds",
          "rushing_yards", "rushing_tds"]:
    H[c] = pd.to_numeric(H[c], errors="coerce").fillna(0)
Q = H[H["position"] == "QB"].copy()

TV = Q.groupby([TC, "season"]).agg(
    att=("attempts", "sum"),
    g=("week", "nunique")).reset_index()
TV["apg"] = TV["att"] / TV["g"]
LG_APG = TV["apg"].mean()
NX = TV.copy()
NX["season"] = NX["season"] - 1
NX = NX.rename(columns={"apg": "nx"})[[TC, "season", "nx"]]
PRr = TV.merge(NX, on=[TC, "season"], how="inner")
R_ATT = PRr["apg"].corr(PRr["nx"])
T = TV[TV["season"] == 2025][[TC, "apg"]].copy()
T["proj"] = LG_APG + R_ATT * (T["apg"] - LG_APG)
T[TC] = T[TC].astype(str).replace(FIX)
TEAM = dict(zip(T[TC], T["proj"]))

G = Q[Q["attempts"] >= 15].copy()
G["ypa"] = G["passing_yards"] / G["attempts"]
SD_ATT, SD_YPA = G["attempts"].std(), G["ypa"].std()
SD_RY = G["rushing_yards"].std()

S = Q.groupby(["player_id", "season"]).agg(
    att=("attempts", "sum"), td=("passing_tds", "sum"),
    pyd=("passing_yards", "sum")).reset_index()
S = S[S["att"] >= 100]
LG_TD = S["td"].sum() / S["att"].sum()
LG_YPA = S["pyd"].sum() / S["att"].sum()
CAR = S.groupby("player_id").agg(
    catt=("att", "sum"), ctd=("td", "sum"),
    cyd=("pyd", "sum")).reset_index()
K = 500

SP = pd.read_csv("stat_projections_2026.csv",
                 low_memory=False)
B = pd.read_csv("board_final.csv", low_memory=False)
B = B[B["position"] == "QB"][
    ["player_id", "exp_games", "depth_rank", "team"]]
X = SP[SP["position"] == "QB"].copy()
for c in ["attempts", "rushing_yards", "rushing_tds"]:
    X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
X = X.merge(CAR, on="player_id", how="left")
X = X.merge(B, on="player_id", how="left",
            suffixes=("", "_b"))
for c in ["catt", "ctd", "cyd"]:
    X[c] = X[c].fillna(0)
X = X[X["depth_rank"] == 1].copy()
X["tm"] = X["team_b"].fillna(X["team"]).astype(str)
w = (X["catt"] / (X["catt"] + 600.0)).clip(0, 1)
X["att"] = (w * X["attempts"]
            + (1 - w) * X["tm"].map(TEAM).fillna(LG_APG))
X["ypa"] = (X["cyd"] + LG_YPA * K) / (X["catt"] + K)
X["tdr"] = (X["ctd"] + LG_TD * K) / (X["catt"] + K)
X["avail"] = (X["exp_games"] / 17.0).clip(0, 1)

LGI = 0.0265
if os.path.exists("qb_int_rates.csv"):
    IR = pd.read_csv("qb_int_rates.csv")[
        ["player_id", "rate"]]
    X = X.merge(IR, on="player_id", how="left")
    X["intr"] = X["rate"].fillna(LGI)
    print("int rates loaded for %d of %d QBs"
          % (int(X["rate"].notna().sum()), len(X)))
else:
    X["intr"] = LGI
    print("qb_int_rates.csv missing, using flat %.4f"
          % LGI)
print("params built for %d starters" % len(X))

BY = pd.read_csv("byes_2026.csv")
BY["team"] = BY["team"].astype(str).replace(FIX)
BYE = dict(zip(BY["team"], BY["bye"]))
SCv = pd.read_csv("league_scoring.csv")
V = dict(zip(SCv["key"], SCv["value"]))
PY, PT, PI = (float(V["pass_yd"]), float(V["pass_td"]),
              float(V["pass_int"]))
RY, RT = float(V["rush_yd"]), float(V["rush_td"])

def sim(r, n, healthy=True):
    a = np.maximum(rng.normal(r["att"], SD_ATT,
                              (WEEKS, n)), 0)
    ai = np.rint(a).astype(int)
    yp = rng.normal(r["ypa"], SD_YPA, (WEEKS, n))
    yd = np.maximum(a * yp, 0)
    td = rng.binomial(ai, r["tdr"])
    it = rng.binomial(ai, r["intr"])
    ry = np.maximum(rng.normal(r["rushing_yards"],
                               SD_RY, (WEEKS, n)), 0)
    rt = rng.poisson(max(r["rushing_tds"], 0.001),
                     (WEEKS, n))
    p = (yd * PY + td * PT + it * PI
         + ry * RY + rt * RT)
    if healthy:
        pl = np.ones((WEEKS, n), dtype=bool)
    else:
        pl = rng.random((WEEKS, n)) < r["avail"]
    b = int(BYE.get(r["tm"], 0))
    if 1 <= b <= WEEKS:
        pl[b - 1, :] = False
    return p, pl, yd, td, it, ry, rt

rows = []
for _, r in X.iterrows():
    p, pl, yd, td, it, ry, rt = sim(r, 6000)
    tot = (p * pl).sum(axis=0)
    yy = (yd * pl).sum(axis=0)
    rows.append({
        "nm": str(r["player_display_name"]), "tm": r["tm"],
        "att": r["att"] * 16, "yds": yy.mean(),
        "ptd": (td * pl).sum(axis=0).mean(),
        "int": (it * pl).sum(axis=0).mean(),
        "ryd": (ry * pl).sum(axis=0).mean(),
        "rtd": (rt * pl).sum(axis=0).mean(),
        "tot": tot.mean(), "ppg": tot.mean() / 16.0,
        "p4k": 100.0 * (yy >= 4000).mean(),
        "av": r["avail"]})
R = pd.DataFrame(rows).sort_values("tot",
                                   ascending=False)
R = R.reset_index(drop=True)
R["qbr"] = R.index + 1

print("\n=== 2026 QB PROJECTIONS, 16 GAMES, HEALTHY ===")
print("  no injury discount. bye removed only.\n")
print("  %-3s %-20s %-4s %4s %5s %5s %4s %5s %4s"
      " %6s %5s %5s"
      % ("#", "player", "tm", "att", "pYds", "pTD",
         "INT", "rYds", "rTD", "TOTAL", "ppg", "4k%"))
print("  " + "-" * 84)
for _, r in R.iterrows():
    print("  %-3d %-20s %-4s %4.0f %5.0f %5.1f %4.1f"
          " %5.0f %4.1f %6.0f %5.1f %5.0f"
          % (r["qbr"], r["nm"][:20], r["tm"][:4],
             r["att"], r["yds"], r["ptd"], r["int"],
             r["ryd"], r["rtd"], r["tot"], r["ppg"],
             r["p4k"]))
print("\n  QBs projected over 4000 pass yds: %d"
      % int((R["yds"] >= 4000).sum()))
print("  QB10 = %.0f pts (%.2f ppg)"
      % (R.iloc[9]["tot"], R.iloc[9]["ppg"]))

print("\n=== DURABILITY, KEPT SEPARATE ===")
print("  availability persists at r=0.598 for QBs,")
print("  so this is signal, not noise. shown apart.\n")
print("  %-3s %-20s %5s %5s %7s %7s %6s"
      % ("#", "player", "avail", "gms", "healthy",
         "risk-adj", "cost"))
print("  " + "-" * 60)
D = R.copy()
D["gms"] = D["av"] * 16
D["adj"] = D["tot"] * D["av"]
D["cost"] = D["adj"] - D["tot"]
for _, r in D.sort_values("cost").head(12).iterrows():
    print("  %-3d %-20s %5.2f %5.1f %7.0f %7.0f %+6.0f"
          % (r["qbr"], r["nm"][:20], r["av"], r["gms"],
             r["tot"], r["adj"], r["cost"]))

BIG = 20000000
CH = 20
def grab(nm):
    return X[X["player_display_name"].astype(str)
             .str.contains(nm, na=False)].iloc[0]
A = grab("Caleb Williams")
Bq = grab("Joe Burrow")
STREAM = float(R.iloc[14]["ppg"])

print("\n=== WILLIAMS vs BURROW ===")
for r in (A, Bq):
    print("  %-16s %-4s att %.1f ypa %.2f tdr %.3f"
          " intr %.3f avail %.2f"
          % (str(r["player_display_name"])[:16], r["tm"],
             r["att"], r["ypa"], r["tdr"], r["intr"],
             r["avail"]))

for lab, hl in (("HEALTHY", True), ("RISK-ADJ", False)):
    wa = 0
    sa = sb = 0.0
    n = BIG // CH
    for c in range(CH):
        pa_, la, _, _, _, _, _ = sim(A, n, hl)
        pb_, lb, _, _, _, _, _ = sim(Bq, n, hl)
        ta = np.where(la, pa_, STREAM).sum(axis=0)
        tb = np.where(lb, pb_, STREAM).sum(axis=0)
        wa += int((ta > tb).sum())
        sa += float(ta.sum())
        sb += float(tb.sum())
    pb = 100.0 - 100.0 * wa / BIG
    se = 100.0 * (pb / 100 * (1 - pb / 100)
                  / BIG) ** 0.5
    print("\n  --- %s (%d sims) ---" % (lab, BIG))
    print("    Williams %.1f | Burrow %.1f | diff %+.1f"
          % (sa / BIG, sb / BIG, sb / BIG - sa / BIG))
    print("    P(Burrow wins) = %.2f%% +- %.4f"
          % (pb, se))
