import numpy as np
import pandas as pd
import nflreadpy as nfl

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
for c in ["attempts", "passing_yards", "passing_tds",
          "rushing_yards", "rushing_tds"]:
    H[c] = pd.to_numeric(H[c], errors="coerce").fillna(0)
Q = H[H["position"] == "QB"].copy()
PC = ("fantasy_points_ppr"
      if "fantasy_points_ppr" in Q.columns
      else "fantasy_points")
S = Q.groupby(["player_id", "season"]).agg(
    att=("attempts", "sum"), td=("passing_tds", "sum"),
    pyd=("passing_yards", "sum"),
    pts=(PC, "sum"), g=("week", "nunique")).reset_index()
S["ppg"] = S["pts"] / S["g"]
S = S[S["att"] >= 100].sort_values(
    ["player_id", "season"]).reset_index(drop=True)
LG_TD = S["td"].sum() / S["att"].sum()
LG_YPA = S["pyd"].sum() / S["att"].sum()
AG = pd.read_csv("qb_birthyears.csv")

def build(d, K):
    out = []
    for pid, g in S.groupby("player_id"):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            t = int(g.at[i, "season"])
            h = g[g["season"] <= t]
            w = d ** (t - h["season"])
            wa = float((w * h["att"]).sum())
            out.append({
                "player_id": pid, "season": t,
                "tdr": (float((w * h["td"]).sum())
                        + K * LG_TD) / (wa + K),
                "ypa": (float((w * h["pyd"]).sum())
                        + K * LG_YPA) / (wa + K)})
    return pd.DataFrame(out)

N = S.copy()
N["season"] = N["season"] - 1
N["tdr_n"] = N["td"] / N["att"]
N = N[["player_id", "season", "tdr_n"]]
yrs = sorted(S["season"].unique())
c1 = yrs[int(len(yrs) * 0.50)]
c2 = yrs[int(len(yrs) * 0.75)]
res = {}
for d in [1.0, 0.8, 0.6, 0.5, 0.4, 0.3]:
    P = build(d, 500).merge(
        N, on=["player_id", "season"], how="inner")
    v = P[(P["season"] >= c1) & (P["season"] < c2)]
    t = P[P["season"] >= c2]
    res[d] = ((v["tdr"] - v["tdr_n"]).abs().mean(),
              (t["tdr"] - t["tdr_n"]).abs().mean())
PICK = min(res, key=lambda k: res[k][0])
print("=== RECENCY, CHOSEN ON VALIDATION ===")
for d in res:
    print("  d %.1f  val %.5f  test %.5f"
          % (d, res[d][0], res[d][1]))
print("  PICK d = %.1f" % PICK)

A = S.merge(AG, on="player_id", how="left")
A["age"] = A["season"] - A["by"]
A = A.dropna(subset=["age"])
NP = S[["player_id", "season", "ppg"]].copy()
NP["season"] = NP["season"] - 1
NP = NP.rename(columns={"ppg": "ppg_n"})
A = A.merge(NP, on=["player_id", "season"], how="inner")
ct = sorted(A["season"].unique())[
    int(len(A["season"].unique()) * 0.6)]
TR = A[A["season"] < ct].copy()
TS = A[A["season"] >= ct].copy()
b0 = TR["ppg"].cov(TR["ppg_n"]) / TR["ppg"].var()
a0 = TR["ppg_n"].mean() - b0 * TR["ppg"].mean()
TR["res"] = TR["ppg_n"] - (a0 + b0 * TR["ppg"])
b1 = TR["age"].cov(TR["res"]) / TR["age"].var()
a1 = TR["res"].mean() - b1 * TR["age"].mean()
base = a0 + b0 * TS["ppg"]
add = base + (a1 + b1 * TS["age"])
m0 = (base - TS["ppg_n"]).abs().mean()
m1 = (add - TS["ppg_n"]).abs().mean()
print("\n=== AGE, RETESTED BY MAE ===")
print("  correlation said REJECT (-0.002)")
print("  age slope %+.4f ppg per year" % b1)
print("  test MAE  base %.4f -> with age %.4f" % (m0, m1))
print("  improvement %+.2f%%" % (100.0 * (1 - m1 / m0)))
USE_AGE = m1 < m0 - 0.005
print("  DECISION: %s"
      % ("ADOPT age" if USE_AGE else "REJECT age"))

GAMES = 17
FANWK = 16
rng = np.random.default_rng(2026)
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX"}
BY = pd.read_csv("byes_2026.csv")
BY["team"] = BY["team"].astype(str).replace(FIX)
BYE = dict(zip(BY["team"], BY["bye"]))
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
PY, PT = float(V["pass_yd"]), float(V["pass_td"])
PI, RY = float(V["pass_int"]), float(V["rush_yd"])
RT = float(V["rush_td"])

GG = Q[Q["attempts"] >= 15].copy()
GG["yg"] = GG["passing_yards"] / GG["attempts"]
SD_ATT = GG["attempts"].std()
SD_YPA = GG["yg"].std()
SD_RY = GG["rushing_yards"].std()

TC = "team" if "team" in H.columns else "recent_team"
TV = Q.groupby([TC, "season"]).agg(
    att=("attempts", "sum"),
    g=("week", "nunique")).reset_index()
TV["apg"] = TV["att"] / TV["g"]
LG_APG = TV["apg"].mean()
NX = TV.copy()
NX["season"] = NX["season"] - 1
NX = NX.rename(columns={"apg": "nx"})[[TC, "season", "nx"]]
PPr = TV.merge(NX, on=[TC, "season"], how="inner")
RATT = PPr["apg"].corr(PPr["nx"])
TT = TV[TV["season"] == 2025][[TC, "apg"]].copy()
TT["proj"] = LG_APG + RATT * (TT["apg"] - LG_APG)
TT[TC] = TT[TC].astype(str).replace(FIX)
TEAM = dict(zip(TT[TC], TT["proj"]))

SP = pd.read_csv("stat_projections_2026.csv",
                 low_memory=False)
BD = pd.read_csv("board_final.csv", low_memory=False)
BD = BD[BD["position"] == "QB"][
    ["player_id", "depth_rank", "team", "exp_games"]]
X = SP[SP["position"] == "QB"].merge(
    BD, on="player_id", how="left", suffixes=("", "_b"))
X = X[X["depth_rank"] == 1].copy()
for c in ["attempts", "rushing_yards", "rushing_tds"]:
    X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
RC = build(PICK, 500)
RC = RC[RC["season"] == 2025][["player_id", "tdr", "ypa"]]
CAR = S.groupby("player_id").agg(
    catt=("att", "sum")).reset_index()
IR = pd.read_csv("qb_int_rates.csv")[
    ["player_id", "rate"]]
for fr in (CAR, RC, IR, AG):
    X = X.merge(fr, on="player_id", how="left")
X["age"] = 2026 - X["by"]
X["catt"] = X["catt"].fillna(0)
X["tm"] = X["team_b"].fillna(X["team"]).astype(str)
w = (X["catt"] / (X["catt"] + 600.0)).clip(0, 1)
X["att"] = (w * X["attempts"]
            + (1 - w) * X["tm"].map(TEAM).fillna(LG_APG))
X["ypa"] = X["ypa"].fillna(LG_YPA)
X["tdr"] = X["tdr"].fillna(LG_TD)
X["intr"] = X["rate"].fillna(0.0211)
X["adj"] = (b1 * (X["age"] - 29.0)).fillna(0.0)
if not USE_AGE:
    X["adj"] = 0.0
X["avail"] = (X["exp_games"] / 17.0).clip(0, 1)
print("\nstarters %d | ages %d | decay %.1f | age term %s"
      % (len(X), int(X["age"].notna().sum()), PICK,
         "on" if USE_AGE else "off"))

def sim(r, n):
    a = np.maximum(rng.normal(r["att"], SD_ATT,
                              (GAMES, n)), 0)
    ai = np.rint(a).astype(int)
    yd = np.maximum(a * rng.normal(r["ypa"], SD_YPA,
                                   (GAMES, n)), 0)
    td = rng.binomial(ai, r["tdr"])
    it = rng.binomial(ai, r["intr"])
    ry = np.maximum(rng.normal(r["rushing_yards"],
                               SD_RY, (GAMES, n)), 0)
    rt = rng.poisson(max(r["rushing_tds"], 0.001),
                     (GAMES, n))
    p = (yd * PY + td * PT + it * PI
         + ry * RY + rt * RT + r["adj"])
    return p, yd, td, it, ry, rt

rows = []
for _, r in X.iterrows():
    p, yd, td, it, ry, rt = sim(r, 8000)
    tot = p.sum(axis=0)
    yy = yd.sum(axis=0)
    rows.append({
        "nm": str(r["player_display_name"]), "tm": r["tm"],
        "age": r["age"], "att": r["att"] * GAMES,
        "yds": yy.mean(), "ptd": td.sum(axis=0).mean(),
        "int": it.sum(axis=0).mean(),
        "ryd": ry.sum(axis=0).mean(),
        "rtd": rt.sum(axis=0).mean(),
        "tot": tot.mean(), "ppg": tot.mean() / GAMES,
        "fan": tot.mean() / GAMES * FANWK,
        "p10": np.percentile(tot, 10),
        "p90": np.percentile(tot, 90),
        "p4k": 100.0 * (yy >= 4000).mean(),
        "av": r["avail"]})
R = pd.DataFrame(rows).sort_values(
    "tot", ascending=False).reset_index(drop=True)
R["qbr"] = R.index + 1
R.to_csv("qb_final_2026.csv", index=False)

print("\n=== 2026 QB PROJECTIONS, 17 GAMES ===")
print("  no injury discount anywhere in this table\n")
print("  %-3s %-20s %-4s %3s %4s %5s %5s %4s %5s %4s"
      " %6s %5s %5s"
      % ("#", "player", "tm", "age", "att", "pYds",
         "pTD", "INT", "rYds", "rTD", "TOT17", "ppg",
         "4k%"))
print("  " + "-" * 88)
for _, r in R.iterrows():
    ag = "%3.0f" % r["age"] if r["age"] == r["age"] else "  ?"
    print("  %-3d %-20s %-4s %s %4.0f %5.0f %5.1f %4.1f"
          " %5.0f %4.1f %6.0f %5.1f %5.0f"
          % (r["qbr"], r["nm"][:20], r["tm"][:4], ag,
             r["att"], r["yds"], r["ptd"], r["int"],
             r["ryd"], r["rtd"], r["tot"], r["ppg"],
             r["p4k"]))
print("\n  QBs over 4000 pass yds: %d"
      % int((R["yds"] >= 4000).sum()))

REPL = float(R.iloc[9]["ppg"])
R["vorp"] = R["ppg"] - REPL
print("\n=== VALUE OVER QB10, 10-TEAM 1-QB ===")
print("  replacement = QB10 at %.2f ppg" % REPL)
print("  fantasy season = %d games (bye removed)\n"
      % FANWK)
print("  %-3s %-20s %6s %6s %7s %7s"
      % ("#", "player", "ppg", "vorp", "FANPTS", "vs rep"))
print("  " + "-" * 56)
for _, r in R.head(16).iterrows():
    print("  %-3d %-20s %6.2f %+6.2f %7.0f %+7.0f"
          % (r["qbr"], r["nm"][:20], r["ppg"],
             r["vorp"], r["fan"], r["vorp"] * FANWK))

print("\n=== DURABILITY, SEPARATE FROM PROJECTION ===")
D = R.copy()
D["gms"] = D["av"] * GAMES
D["risk"] = (D["ppg"] * D["gms"]
             + REPL * (FANWK - D["gms"]).clip(lower=0))
D["cost"] = D["risk"] - D["fan"]
print("  assumes missed weeks streamed at QB10\n")
print("  %-3s %-20s %5s %6s %7s %7s"
      % ("#", "player", "gms", "FANPTS", "w/risk",
         "cost"))
print("  " + "-" * 54)
for _, r in D.nsmallest(10, "cost").iterrows():
    print("  %-3d %-20s %5.1f %6.0f %7.0f %+7.0f"
          % (r["qbr"], r["nm"][:20], r["gms"],
             r["fan"], r["risk"], r["cost"]))

print("\n=== SANITY CHECK vs OUTSIDE CONSENSUS ===")
CK = {"Darnold": (4012, 242, "ESPN 4012yd 24-12"),
      "Rodgers": (3322, 233, "2025 actual 3322yd 23td"),
      "Allen": (0, 0, "consensus QB1"),
      "Burrow": (0, 0, ""),
      "Williams": (0, 0, "")}
for k in CK:
    h = R[R["nm"].str.contains(k, na=False)]
    if not len(h):
        continue
    r = h.iloc[0]
    ex = CK[k]
    tag = ("  <-- " + ex[2]) if ex[2] else ""
    print("  QB%-2d %-18s %5.0f yd %6.0f pts%s"
          % (r["qbr"], r["nm"][:18], r["yds"],
             r["tot"], tag))

A2 = R[R["nm"].str.contains("Caleb Williams", na=False)]
B2 = R[R["nm"].str.contains("Joe Burrow", na=False)]
if len(A2) and len(B2):
    a, b = A2.iloc[0], B2.iloc[0]
    print("\n=== THE TRADE, FINAL MODEL ===")
    print("  Williams QB%-2d %.2f ppg | %.0f fantasy pts"
          % (a["qbr"], a["ppg"], a["fan"]))
    print("  Burrow   QB%-2d %.2f ppg | %.0f fantasy pts"
          % (b["qbr"], b["ppg"], b["fan"]))
    print("  edge to Burrow %+.2f ppg | %+.0f pts"
          % (b["ppg"] - a["ppg"], b["fan"] - a["fan"]))
    ar = a["ppg"] * a["av"] * GAMES + REPL * max(
        0, FANWK - a["av"] * GAMES)
    br = b["ppg"] * b["av"] * GAMES + REPL * max(
        0, FANWK - b["av"] * GAMES)
    print("  with durability + streaming: %+.0f pts"
          % (br - ar))
print("\n  saved qb_final_2026.csv")
