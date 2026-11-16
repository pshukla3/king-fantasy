import numpy as np
import pandas as pd
import nflreadpy as nfl

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
PC = ("fantasy_points_ppr"
      if "fantasy_points_ppr" in H.columns
      else "fantasy_points")
Q = H[H["position"] == "QB"].copy()
for c in ["attempts", "passing_yards",
          "passing_tds", PC]:
    Q[c] = pd.to_numeric(Q[c], errors="coerce").fillna(0)

S = Q.groupby(["player_id", "season"]).agg(
    pts=(PC, "sum"), g=("week", "nunique"),
    att=("attempts", "sum"), td=("passing_tds", "sum"),
    pyd=("passing_yards", "sum")).reset_index()
S = S[S["att"] >= 150].copy()
S["ppg"] = S["pts"] / S["g"]
S["tdr"] = S["td"] / S["att"]
S["ypa"] = S["pyd"] / S["att"]

PL = nfl.load_players()
PL = PL.to_pandas() if hasattr(PL, "to_pandas") else PL
idc = "gsis_id" if "gsis_id" in PL.columns else "player_id"
bd = [c for c in PL.columns if "birth" in c.lower()]
print("id col %s | birth cols %s" % (idc, bd))
PL = PL[[idc, bd[0]]].rename(
    columns={idc: "player_id", bd[0]: "bdate"})
PL["by"] = pd.to_datetime(PL["bdate"],
                          errors="coerce").dt.year
PL = PL.dropna(subset=["by"]).drop_duplicates("player_id")
S = S.merge(PL[["player_id", "by"]], on="player_id",
            how="left")
S["age"] = S["season"] - S["by"]
S = S[S["age"].between(20, 45)].copy()
print("QB seasons with age attached: %d" % len(S))

print("\n=== CROSS-SECTIONAL: QB OUTPUT BY AGE ===")
print("  (survivor-biased, only the good ones last)\n")
print("  %4s %5s %6s %6s %7s"
      % ("age", "n", "ppg", "ypa", "tdr"))
for a in range(22, 44):
    d = S[S["age"] == a]
    if len(d) < 5:
        continue
    print("  %4d %5d %6.2f %6.2f %7.4f"
          % (a, len(d), d["ppg"].mean(),
             d["ypa"].mean(), d["tdr"].mean()))
S.to_csv("qb_seasons_age.csv", index=False)

N = S.copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "ppg_n", "tdr": "tdr_n",
                      "ypa": "ypa_n"})
N = N[["player_id", "season", "ppg_n", "tdr_n", "ypa_n"]]
P2 = S.merge(N, on=["player_id", "season"], how="inner")
P2["r"] = P2["ppg_n"] / P2["ppg"].replace(0, np.nan)

print("\n=== SAME-PLAYER YEAR OVER YEAR, BY AGE ===")
print("  same guy vs himself, no survivor bias")
print("  ratio < 1 means he declined\n")
print("  %4s %5s %8s %7s %7s"
      % ("age", "n", "d ppg", "ratio", "used"))
AM = {}
for a in range(22, 44):
    d = P2[P2["age"] == a].dropna(subset=["r"])
    if len(d) < 4:
        continue
    n = len(d)
    rr = float(d["r"].mean())
    sh = n / (n + 12.0)
    AM[a] = 1.0 + sh * (rr - 1.0)
    print("  %4d %5d %+8.2f %7.3f %7.3f"
          % (a, n, (d["ppg_n"] - d["ppg"]).mean(),
             rr, AM[a]))
pd.Series(AM).to_csv("qb_age_mult.csv")

HIS = {}
for pid, d in S.groupby("player_id"):
    HIS[pid] = d[["season", "att", "td", "pyd"]].to_numpy()
LG_TD = S["td"].sum() / S["att"].sum()
LG_YPA = S["pyd"].sum() / S["att"].sum()
KP = 400

def wr(pid, yr, h, num, prior):
    a = HIS.get(pid)
    if a is None:
        return prior
    m = a[:, 0] <= yr
    if not m.any():
        return prior
    w = 0.5 ** ((yr - a[m, 0]) / h)
    nu = float((w * a[m, num]).sum())
    de = float((w * a[m, 1]).sum())
    return (nu + KP * prior) / (de + KP)

print("\n=== HOW FAR BACK SHOULD HISTORY COUNT? ===")
print("  half-life in years, scored on next-yr TD rate\n")
print("  %6s %11s" % ("half", "test MAE"))
best = (99.0, 9.9)
for h in [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 99.0]:
    e = [abs(wr(r["player_id"], r["season"], h, 2, LG_TD)
             - r["tdr_n"]) for _, r in P2.iterrows()]
    m = float(np.mean(e))
    print("  %6.1f %11.5f" % (h, m))
    if m < best[1]:
        best = (h, m)
HL = best[0]
print("\n  best half-life = %.1f yrs" % HL)
print("  99 = every season equal, what 138 does now")
