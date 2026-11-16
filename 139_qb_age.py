import numpy as np
import pandas as pd

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
for c in ["attempts", "passing_yards", "passing_tds"]:
    H[c] = pd.to_numeric(H[c], errors="coerce").fillna(0)
Q = H[H["position"] == "QB"].copy()
PC = ("fantasy_points_ppr"
      if "fantasy_points_ppr" in Q.columns
      else "fantasy_points")
S = Q.groupby(["player_id", "season"]).agg(
    att=("attempts", "sum"), td=("passing_tds", "sum"),
    pyd=("passing_yards", "sum")).reset_index()
S = S[S["att"] >= 100].sort_values(
    ["player_id", "season"]).reset_index(drop=True)
LG_TD = S["td"].sum() / S["att"].sum()
LG_YPA = S["pyd"].sum() / S["att"].sum()

def build(d, K):
    out = []
    for pid, g in S.groupby("player_id"):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            t = int(g.at[i, "season"])
            h = g[g["season"] <= t]
            w = d ** (t - h["season"])
            wa = float((w * h["att"]).sum())
            wt = float((w * h["td"]).sum())
            wy = float((w * h["pyd"]).sum())
            out.append({
                "player_id": pid, "season": t,
                "tdr": (wt + K * LG_TD) / (wa + K),
                "ypa": (wy + K * LG_YPA) / (wa + K)})
    return pd.DataFrame(out)

N = S.copy()
N["season"] = N["season"] - 1
N["tdr_n"] = N["td"] / N["att"]
N["ypa_n"] = N["pyd"] / N["att"]
N = N[["player_id", "season", "tdr_n", "ypa_n"]]

yrs = sorted(S["season"].unique())
cut = yrs[int(len(yrs) * 0.6)]
print("league tdr %.4f | ypa %.3f" % (LG_TD, LG_YPA))
print("train < %d | test >= %d" % (cut, cut))
print("\n=== RECENCY DECAY FIT ===")
print("  d=1.0 is what the model does now:")
print("  a 2011 season counts as much as 2025\n")
print("  %5s %10s %10s %10s"
      % ("decay", "td tr", "td te", "ypa te"))
best = (1.0, 9.9)
for d in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]:
    P = build(d, 500).merge(
        N, on=["player_id", "season"], how="inner")
    tr = P[P["season"] < cut]
    te = P[P["season"] >= cut]
    e0 = (tr["tdr"] - tr["tdr_n"]).abs().mean()
    e1 = (te["tdr"] - te["tdr_n"]).abs().mean()
    e2 = (te["ypa"] - te["ypa_n"]).abs().mean()
    print("  %5.1f %10.5f %10.5f %10.4f"
          % (d, e0, e1, e2))
    if e0 < best[1]:
        best = (d, e0)
print("\n  best decay on train = %.1f" % best[0])

import nflreadpy as nfl
PL = nfl.load_players()
PL = PL.to_pandas() if hasattr(PL, "to_pandas") else PL
idc = "gsis_id" if "gsis_id" in PL.columns else "player_id"
bc = [c for c in PL.columns if "birth" in c][0]
PL = PL[[idc, bc]].rename(
    columns={idc: "player_id", bc: "bd"})
PL["bd"] = pd.to_datetime(PL["bd"], errors="coerce")
A = S.merge(PL, on="player_id", how="left")
A = A[A["bd"].notna()].copy()
A["age"] = (A["season"] - A["bd"].dt.year
            - (A["bd"].dt.month > 9).astype(int))
W = Q.groupby(["player_id", "season"]).agg(
    pts=(PC, "sum"), g=("week", "nunique")).reset_index()
W["ppg"] = W["pts"] / W["g"]
A = A.merge(W[["player_id", "season", "ppg"]],
            on=["player_id", "season"], how="left")
A["r"] = A["td"] / A["att"]
A["y"] = A["pyd"] / A["att"]

print("\n=== QB AGE CURVE ===")
print("  n with birthdate: %d" % len(A))
print("  %5s %5s %7s %7s %7s"
      % ("age", "n", "ppg", "tdr", "ypa"))
for lo, hi in [(21, 24), (25, 27), (28, 30), (31, 33),
               (34, 36), (37, 39), (40, 46)]:
    d = A[(A["age"] >= lo) & (A["age"] <= hi)]
    if len(d) < 5:
        continue
    print("  %2d-%2d %5d %7.2f %7.4f %7.3f"
          % (lo, hi, len(d), d["ppg"].mean(),
             d["r"].mean(), d["y"].mean()))

A = A.sort_values(["player_id", "season"])
A["nppg"] = A.groupby("player_id")["ppg"].shift(-1)
A["ns"] = A.groupby("player_id")["season"].shift(-1)
D = A[(A["ns"] - A["season"]) == 1].copy()
D["dl"] = D["nppg"] - D["ppg"]
print("\n=== YEAR-OVER-YEAR CHANGE BY AGE ===")
print("  this is the aging signal, same players\n")
print("  %5s %5s %8s" % ("age", "n", "d ppg"))
for lo, hi in [(21, 26), (27, 30), (31, 33),
               (34, 36), (37, 46)]:
    d = D[(D["age"] >= lo) & (D["age"] <= hi)]
    if len(d) < 5:
        continue
    print("  %2d-%2d %5d %+8.2f"
          % (lo, hi, len(d), d["dl"].mean()))

TC = "team" if "team" in H.columns else "recent_team"
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX"}
for c in ["rushing_yards", "rushing_tds"]:
    Q[c] = pd.to_numeric(Q[c], errors="coerce").fillna(0)
TV = Q.groupby([TC, "season"]).agg(
    att=("attempts", "sum"),
    g=("week", "nunique")).reset_index()
TV["apg"] = TV["att"] / TV["g"]
LG_APG = TV["apg"].mean()
NX = TV.copy()
NX["season"] = NX["season"] - 1
NX = NX.rename(columns={"apg": "nx"})[[TC, "season", "nx"]]
PP = TV.merge(NX, on=[TC, "season"], how="inner")
RA = PP["apg"].corr(PP["nx"])
T = TV[TV["season"] == 2025][[TC, "apg"]].copy()
T["proj"] = LG_APG + RA * (T["apg"] - LG_APG)
T[TC] = T[TC].astype(str).replace(FIX)
TEAM = dict(zip(T[TC], T["proj"]))

AB2 = {}
for lo2, hi2 in [(21, 26), (27, 30), (31, 33),
                 (34, 36), (37, 46)]:
    d = D[(D["age"] >= lo2) & (D["age"] <= hi2)]
    if len(d) >= 5:
        for a in range(lo2, hi2 + 1):
            AB2[a] = float(d["dl"].mean())
BASE = AB2.get(29, 0.0)
AG = A[A["season"] == 2025][["player_id", "age"]].copy()
AG["age"] = AG["age"] + 1

RC = build(best[0], 500)
RC = RC[RC["season"] == 2025][["player_id", "tdr", "ypa"]]
OD = build(1.0, 500)
OD = OD[OD["season"] == 2025][
    ["player_id", "tdr", "ypa"]].rename(
    columns={"tdr": "otdr", "ypa": "oypa"})
CAR = S.groupby("player_id").agg(
    catt=("att", "sum")).reset_index()

SP = pd.read_csv("stat_projections_2026.csv",
                 low_memory=False)
B = pd.read_csv("board_final.csv", low_memory=False)
B = B[B["position"] == "QB"][
    ["player_id", "depth_rank", "team"]]
IR = pd.read_csv("qb_int_rates.csv")[
    ["player_id", "rate"]]
X = SP[SP["position"] == "QB"].copy()
for c in ["attempts", "rushing_yards", "rushing_tds"]:
    X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
for f in (CAR, RC, OD, IR, AG):
    X = X.merge(f, on="player_id", how="left")
X = X.merge(B, on="player_id", how="left",
            suffixes=("", "_b"))
X = X[X["depth_rank"] == 1].copy()
X["catt"] = X["catt"].fillna(0)
X["tm"] = X["team_b"].fillna(X["team"]).astype(str)
w2 = (X["catt"] / (X["catt"] + 600.0)).clip(0, 1)
X["att"] = (w2 * X["attempts"]
            + (1 - w2) * X["tm"].map(TEAM).fillna(LG_APG))
X["tdr"] = X["tdr"].fillna(LG_TD)
X["ypa"] = X["ypa"].fillna(LG_YPA)
X["otdr"] = X["otdr"].fillna(LG_TD)
X["oypa"] = X["oypa"].fillna(LG_YPA)
X["intr"] = X["rate"].fillna(0.0211)
X["ad"] = X["age"].map(AB2).fillna(BASE) - BASE

def f(d, tk, yk):
    return (d["att"] * d[yk] * 0.04
            + d["att"] * d[tk] * 4.0
            + d["att"] * d["intr"] * -2.0
            + d["rushing_yards"] * 0.10
            + d["rushing_tds"] * 6.0)

X["old"] = f(X, "otdr", "oypa")
X["new"] = f(X, "tdr", "ypa") + X["ad"]
X["mv"] = X["new"] - X["old"]
X = X.sort_values("new", ascending=False)
X = X.reset_index(drop=True)
X["qbr"] = X.index + 1

print("\n=== RECENCY %.1f + AGE, 16 GAMES ===" % best[0])
print("  %-3s %-20s %-4s %3s %6s %6s %6s %6s"
      % ("#", "player", "tm", "age", "old", "new",
         "move", "SEASON"))
print("  " + "-" * 62)
for _, r in X.iterrows():
    ag = r["age"]
    ag = "%3.0f" % ag if ag == ag else "  ?"
    print("  %-3d %-20s %-4s %s %6.2f %6.2f %+6.2f %6.0f"
          % (r["qbr"], str(r["player_display_name"])[:20],
             r["tm"][:4], ag, r["old"], r["new"],
             r["mv"], r["new"] * 16))

print("\n=== THE ONES YOU FLAGGED ===")
for nm in ["Rodgers", "Darnold", "Willis", "Watson",
           "Stafford", "Goff", "Williams", "Burrow"]:
    h = X[X["player_display_name"].astype(str)
          .str.contains(nm, na=False)]
    if len(h):
        r = h.iloc[0]
        print("  QB%-2d %-20s %6.2f -> %6.2f  %+.2f"
              % (r["qbr"],
                 str(r["player_display_name"])[:20],
                 r["old"], r["new"], r["mv"]))
