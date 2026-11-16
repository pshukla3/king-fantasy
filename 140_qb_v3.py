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

PL = nfl.load_players()
PL = PL.to_pandas() if hasattr(PL, "to_pandas") else PL
idc = "gsis_id" if "gsis_id" in PL.columns else "player_id"
bc = [c for c in PL.columns if "birth" in c][0]
AG = PL[[idc, bc]].rename(
    columns={idc: "player_id", bc: "bd"})
AG["bd"] = pd.to_datetime(AG["bd"], errors="coerce")
AG = AG.dropna(subset=["bd"]).drop_duplicates("player_id")
AG["by"] = (AG["bd"].dt.year
            + (AG["bd"].dt.month > 9).astype(int))
AG = AG[["player_id", "by"]]
AG.to_csv("qb_birthyears.csv", index=False)
print("birth years on file: %d" % len(AG))

SP = pd.read_csv("stat_projections_2026.csv",
                 low_memory=False)
BD = pd.read_csv("board_final.csv", low_memory=False)
BD = BD[BD["position"] == "QB"][
    ["player_id", "depth_rank", "team"]]
X = SP[SP["position"] == "QB"].merge(
    BD, on="player_id", how="left", suffixes=("", "_b"))
X = X[X["depth_rank"] == 1].copy()
X = X.merge(AG, on="player_id", how="left")
X["age"] = 2026 - X["by"]
print("starters: %d | with age: %d"
      % (len(X), int(X["age"].notna().sum())))
m = X[X["age"].isna()]
if len(m):
    print("\nSTILL MISSING AGE:")
    for _, r in m.iterrows():
        print("  %-24s %s"
              % (str(r["player_display_name"])[:24],
                 r["player_id"]))
else:
    print("  every starter now has an age")
print("\n  oldest starters:")
for _, r in X.nlargest(5, "age").iterrows():
    print("    %-24s %.0f"
          % (str(r["player_display_name"])[:24],
             r["age"]))

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
c1 = yrs[int(len(yrs) * 0.50)]
c2 = yrs[int(len(yrs) * 0.75)]
print("\n=== THREE-WAY SPLIT ===")
print("  train  < %d" % c1)
print("  valid  %d to %d   <- picks the decay" % (c1, c2 - 1))
print("  TEST  >= %d       <- never used to choose" % c2)
print("\n  %5s %9s %9s %9s %9s"
      % ("decay", "tdr val", "tdr TEST", "ypa val",
         "ypa TEST"))
res = {}
for d in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]:
    P = build(d, 500).merge(
        N, on=["player_id", "season"], how="inner")
    v = P[(P["season"] >= c1) & (P["season"] < c2)]
    t = P[P["season"] >= c2]
    a = (v["tdr"] - v["tdr_n"]).abs().mean()
    b = (t["tdr"] - t["tdr_n"]).abs().mean()
    e = (v["ypa"] - v["ypa_n"]).abs().mean()
    f = (t["ypa"] - t["ypa_n"]).abs().mean()
    res[d] = (a, b, e, f)
    print("  %5.1f %9.5f %9.5f %9.4f %9.4f"
          % (d, a, b, e, f))

pick = min(res, key=lambda k: res[k][0] + res[k][2] * 0.02)
print("\n  chosen on VALIDATION only: d = %.1f" % pick)
print("  test tdr MAE  d=1.0 %.5f -> d=%.1f %.5f  (%+.1f%%)"
      % (res[1.0][1], pick, res[pick][1],
         100.0 * (res[pick][1] / res[1.0][1] - 1)))
print("  test ypa MAE  d=1.0 %.4f -> d=%.1f %.4f  (%+.1f%%)"
      % (res[1.0][3], pick, res[pick][3],
         100.0 * (res[pick][3] / res[1.0][3] - 1)))
print("  DECISION: %s"
      % ("ADOPT recency" if pick < 1.0 else "keep flat"))
import os

if os.path.exists("qb_adot.csv"):
    AD = pd.read_csv("qb_adot.csv")
    print("\nloaded qb_adot.csv (%d rows)" % len(AD))
else:
    print("\npulling air yards by season, ~2 min...")
    rows = []
    for y in range(2016, 2026):
        P = nfl.load_pbp(seasons=[y])
        P = P.to_pandas() if hasattr(P, "to_pandas") else P
        P = P[P["passer_player_id"].notna()]
        P = P[["passer_player_id", "air_yards",
               "pass_attempt"]].copy()
        for c in ["air_yards", "pass_attempt"]:
            P[c] = pd.to_numeric(P[c], errors="coerce")
        P = P[P["pass_attempt"] == 1]
        g = P.groupby("passer_player_id").agg(
            ay=("air_yards", "sum"),
            n=("air_yards", "count")).reset_index()
        g["season"] = y
        rows.append(g)
        print("  %d done" % y)
        del P
    AD = pd.concat(rows, ignore_index=True)
    AD = AD.rename(columns={"passer_player_id": "player_id"})
    AD = AD[AD["n"] >= 100].copy()
    AD["adot"] = AD["ay"] / AD["n"]
    AD.to_csv("qb_adot.csv", index=False)
    print("  wrote qb_adot.csv")

J = S.merge(AD[["player_id", "season", "adot"]],
            on=["player_id", "season"], how="inner")
J = J.merge(AG, on="player_id", how="left")
J["age"] = J["season"] - J["by"]
J = J.sort_values(["player_id", "season"])
J["padot"] = J.groupby("player_id")["adot"].shift(1)
J["drop"] = J["adot"] - J["padot"]
NP = S[["player_id", "season", "ppg"]].copy()
NP["season"] = NP["season"] - 1
NP = NP.rename(columns={"ppg": "ppg_n"})
J = J.merge(NP, on=["player_id", "season"], how="inner")
J = J.dropna(subset=["drop", "age", "ppg_n"])

print("\n=== aDOT: THE RODGERS MECHANISM ===")
print("  n = %d qb-seasons" % len(J))
print("  adot range %.2f to %.2f"
      % (J["adot"].min(), J["adot"].max()))
print("  adot vs next-yr ppg   r = %+.3f"
      % J["adot"].corr(J["ppg_n"]))
print("  yoy adot drop vs next r = %+.3f"
      % J["drop"].corr(J["ppg_n"]))

ct = sorted(J["season"].unique())[int(
    len(J["season"].unique()) * 0.6)]
TR = J[J["season"] < ct].copy()
TS = J[J["season"] >= ct].copy()
b0 = TR["ppg"].cov(TR["ppg_n"]) / TR["ppg"].var()
a0 = TR["ppg_n"].mean() - b0 * TR["ppg"].mean()
TR["res"] = TR["ppg_n"] - (a0 + b0 * TR["ppg"])
for lab, cl in (("adot level", "adot"),
                ("adot drop", "drop"),
                ("age", "age")):
    b1 = TR[cl].cov(TR["res"]) / TR[cl].var()
    a1 = TR["res"].mean() - b1 * TR[cl].mean()
    base = a0 + b0 * TS["ppg"]
    add = base + (a1 + b1 * TS[cl])
    r0 = base.corr(TS["ppg_n"])
    r1 = add.corr(TS["ppg_n"])
    print("\n  + %-11s  base r %.3f -> %.3f  gain %+.3f"
          % (lab, r0, r1, r1 - r0))
    print("    DECISION: %s"
          % ("ADOPT" if r1 - r0 > 0.010 else "REJECT"))

print("\n  Rodgers aDOT by season:")
rg = J[J["player_id"] == AG.merge(
    pd.DataFrame({"player_id": []}), how="left"
).head(0).shape[0] * 0]
R2 = AD.merge(S[["player_id", "season", "ppg"]],
              on=["player_id", "season"], how="inner")
nm = pd.read_csv("board_final.csv", low_memory=False)
nm = nm[["player_id", "player_display_name"]]
R2 = R2.merge(nm.drop_duplicates("player_id"),
              on="player_id", how="left")
for who in ["Rodgers", "Darnold"]:
    d = R2[R2["player_display_name"].astype(str)
           .str.contains(who, na=False)]
    if len(d):
        print("  %s:" % who)
        for _, r in d.sort_values("season").iterrows():
            print("    %d  adot %.2f  ppg %.1f"
                  % (r["season"], r["adot"], r["ppg"]))
