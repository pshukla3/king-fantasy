import numpy as np
import pandas as pd

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
NX = TV.copy()
NX["season"] = NX["season"] - 1
NX = NX.rename(columns={"apg": "nx"})[[TC, "season", "nx"]]
PR = TV.merge(NX, on=[TC, "season"], how="inner")
R_ATT = PR["apg"].corr(PR["nx"])
LG_APG = TV["apg"].mean()
print("=== TEAM PASS VOLUME ===")
print("  persistence r = %+.3f  (n=%d)" % (R_ATT, len(PR)))
print("  league mean %.1f att/game" % LG_APG)

T = TV[TV["season"] == 2025][[TC, "apg"]].copy()
T["proj"] = LG_APG + R_ATT * (T["apg"] - LG_APG)
T[TC] = T[TC].astype(str).replace(FIX)
TEAM = dict(zip(T[TC], T["proj"]))
print("  2026 projected range %.1f to %.1f att/g"
      % (T["proj"].min(), T["proj"].max()))

G = Q[Q["attempts"] >= 15].copy()
G["ypa"] = G["passing_yards"] / G["attempts"]
SD_ATT = G["attempts"].std()
SD_YPA = G["ypa"].std()
SD_RY = G["rushing_yards"].std()
LGI = 0.0265
K = 500

S = Q.groupby(["player_id", "season"]).agg(
    att=("attempts", "sum"), td=("passing_tds", "sum"),
    pyd=("passing_yards", "sum")).reset_index()
S = S[S["att"] >= 100]
LG_TD = S["td"].sum() / S["att"].sum()
LG_YPA = S["pyd"].sum() / S["att"].sum()
CAR = S.groupby("player_id").agg(
    catt=("att", "sum"), ctd=("td", "sum"),
    cyd=("pyd", "sum")).reset_index()

SP = pd.read_csv("stat_projections_2026.csv",
                 low_memory=False)
B = pd.read_csv("board_final.csv", low_memory=False)
B = B[B["position"] == "QB"][
    ["player_id", "exp_games", "depth_rank", "team"]]
X = SP[SP["position"] == "QB"].copy()
for c in ["attempts", "passing_yards", "passing_tds",
          "rushing_yards", "rushing_tds"]:
    X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
X = X.merge(CAR, on="player_id", how="left")
X = X.merge(B, on="player_id", how="left",
            suffixes=("", "_b"))
for c in ["catt", "ctd", "cyd"]:
    X[c] = X[c].fillna(0)
X = X[X["depth_rank"] == 1].copy()
X["tm"] = X["team_b"].fillna(X["team"]).astype(str)

X["own"] = X["attempts"]
X["tmv"] = X["tm"].map(TEAM).fillna(LG_APG)
w = (X["catt"] / (X["catt"] + 600.0)).clip(0, 1)
X["att"] = w * X["own"] + (1 - w) * X["tmv"]
X["ypa"] = (X["cyd"] + LG_YPA * K) / (X["catt"] + K)
X["tdr"] = (X["ctd"] + LG_TD * K) / (X["catt"] + K)
X["avail"] = (X["exp_games"] / 17.0).clip(0, 1)

print("\n=== SITUATION FIX: STARTERS GET TEAM VOLUME ===")
X["d"] = X["att"] - X["own"]
for _, r in X.nlargest(10, "d").iterrows():
    print("  %-22s %-4s  %4.1f -> %4.1f att/g  (+%.1f)"
          % (str(r["player_display_name"])[:22], r["tm"],
             r["own"], r["att"], r["d"]))

BY = pd.read_csv("byes_2026.csv")
BY["team"] = BY["team"].astype(str).replace(FIX)
BYE = dict(zip(BY["team"], BY["bye"]))
SCv = pd.read_csv("league_scoring.csv")
V = dict(zip(SCv["key"], SCv["value"]))
PY, PT, PI = (float(V["pass_yd"]), float(V["pass_td"]),
              float(V["pass_int"]))
RY, RT = float(V["rush_yd"]), float(V["rush_td"])

def sim(r, n):
    a = np.maximum(rng.normal(r["att"], SD_ATT,
                              (WEEKS, n)), 0)
    ai = np.rint(a).astype(int)
    yp = rng.normal(r["ypa"], SD_YPA, (WEEKS, n))
    yd = np.maximum(a * yp, 0)
    td = rng.binomial(ai, r["tdr"])
    it = rng.binomial(ai, LGI)
    ry = np.maximum(rng.normal(r["rushing_yards"],
                               SD_RY, (WEEKS, n)), 0)
    rt = rng.poisson(max(r["rushing_tds"], 0.001),
                     (WEEKS, n))
    p = (yd * PY + td * PT + it * PI
         + ry * RY + rt * RT)
    pl = rng.random((WEEKS, n)) < r["avail"]
    b = int(BYE.get(r["tm"], 0))
    if 1 <= b <= WEEKS:
        pl[b - 1, :] = False
    return p, pl, yd, td, it, ry, rt

rows = []
for _, r in X.iterrows():
    p, pl, yd, td, it, ry, rt = sim(r, 5000)
    tot = (p * pl).sum(axis=0)
    rows.append({"nm": str(r["player_display_name"]),
                 "tm": r["tm"], "att": r["att"],
                 "gms": pl.sum(axis=0).mean(),
                 "yds": (yd * pl).sum(axis=0).mean(),
                 "ptd": (td * pl).sum(axis=0).mean(),
                 "int": (it * pl).sum(axis=0).mean(),
                 "ryd": (ry * pl).sum(axis=0).mean(),
                 "rtd": (rt * pl).sum(axis=0).mean(),
                 "tot": tot.mean(),
                 "p10": np.percentile(tot, 10),
                 "p90": np.percentile(tot, 90)})
R = pd.DataFrame(rows).sort_values("tot", ascending=False)
R = R.reset_index(drop=True)
R["qbr"] = R.index + 1

print("\n=== 2026 QB, FULL 17-WEEK FANTASY SEASON ===")
print("  %-3s %-20s %-4s %4s %4s %5s %5s %4s %5s %4s"
      " %6s %5s %5s"
      % ("#", "player", "tm", "att", "gms", "pYds",
         "pTD", "INT", "rYds", "rTD", "TOTAL",
         "p10", "p90"))
print("  " + "-" * 88)
for _, r in R.iterrows():
    print("  %-3d %-20s %-4s %4.1f %4.1f %5.0f %5.1f"
          " %4.1f %5.0f %4.1f %6.0f %5.0f %5.0f"
          % (r["qbr"], r["nm"][:20], r["tm"][:4],
             r["att"], r["gms"], r["yds"], r["ptd"],
             r["int"], r["ryd"], r["rtd"], r["tot"],
             r["p10"], r["p90"]))
print("\n  QB10 replacement = %.0f pts"
      % float(R.iloc[9]["tot"]))

BIG = 20000000
CH = 20
STREAM = float(R.iloc[14]["tot"]) / WEEKS

def grab(nm):
    h = X[X["player_display_name"].astype(str)
          .str.contains(nm, na=False)]
    return h.iloc[0]

A = grab("Caleb Williams")
Bq = grab("Joe Burrow")
print("\n=== CALEB WILLIAMS vs JOE BURROW ===")
for r in (A, Bq):
    print("  %-18s %-4s att %.1f ypa %.2f tdr %.3f"
          " avail %.2f bye %d"
          % (str(r["player_display_name"])[:18], r["tm"],
             r["att"], r["ypa"], r["tdr"], r["avail"],
             int(BYE.get(r["tm"], 0))))
print("  missed weeks filled by streamer at %.2f ppg"
      % STREAM)
print("  running %d sims..." % BIG)

wa = 0
sa = sb = 0.0
n = BIG // CH
for c in range(CH):
    pa_, la, _, _, _, _, _ = sim(A, n)
    pb_, lb, _, _, _, _, _ = sim(Bq, n)
    ta = np.where(la, pa_, STREAM).sum(axis=0)
    tb = np.where(lb, pb_, STREAM).sum(axis=0)
    wa += int((ta > tb).sum())
    sa += float(ta.sum())
    sb += float(tb.sum())
    if (c + 1) % 5 == 0:
        print("    chunk %d/%d" % (c + 1, CH))

p = 100.0 - 100.0 * wa / BIG
se = 100.0 * (p / 100 * (1 - p / 100) / BIG) ** 0.5
print("\n  Williams season total  %.1f" % (sa / BIG))
print("  Burrow   season total  %.1f" % (sb / BIG))
print("  difference             %+.1f"
      % (sb / BIG - sa / BIG))
print("\n  P(Burrow beats Williams) = %.3f%%" % p)
print("  standard error %.4f%% | at 1e9: %.5f%%"
      % (se, se / (1000 ** 0.5)))
