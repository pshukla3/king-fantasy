import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"].astype(str), SC["value"]))

def sv(k, d=0.0):
    return float(V.get(k, d))

YRS = list(range(2010, 2026))
W = pl(nfl.load_player_stats(seasons=YRS))
NEED = ["receptions", "receiving_yards", "receiving_tds",
        "rushing_yards", "rushing_tds", "targets",
        "receiving_fumbles_lost", "rushing_fumbles_lost"]
for c in NEED:
    if c not in W.columns:
        W[c] = 0.0
    W[c] = pd.to_numeric(W[c], errors="coerce").fillna(0.0)
W = W[W["position"] == "WR"].copy()
W["fp"] = (W["receptions"] * sv("rec", 1.0)
           + W["receiving_yards"] * sv("rec_yd", 0.1)
           + W["receiving_tds"] * sv("rec_td", 6.0)
           + W["rushing_yards"] * sv("rush_yd", 0.1)
           + W["rushing_tds"] * sv("rush_td", 6.0)
           + (W["receiving_fumbles_lost"]
              + W["rushing_fumbles_lost"])
           * sv("fum_lost", -2.0))

S = W.groupby(["player_id", "season"]).agg(
    fp=("fp", "sum"), g=("week", "nunique"),
    tar=("targets", "sum"), rec=("receptions", "sum"),
    yds=("receiving_yards", "sum"),
    td=("receiving_tds", "sum")).reset_index()
S = S[S["g"] >= 10].copy()
S["ppg"] = S["fp"] / S["g"]
S["tpg"] = S["tar"] / S["g"]

PLY = pl(nfl.load_players())
idc = "gsis_id" if "gsis_id" in PLY.columns else "player_id"
PLY = PLY[[idc, "display_name", "birth_date"]].rename(
    columns={idc: "player_id"})
PLY["by"] = pd.to_datetime(PLY["birth_date"],
                           errors="coerce").dt.year
S = S.merge(PLY.drop_duplicates("player_id"),
            on="player_id", how="left")
S["age"] = S["season"] - S["by"]
S = S.sort_values(["player_id", "season"])
S.to_csv("wr_seasons.csv", index=False)
print("WR seasons 2010-25, 10+ games: %d" % len(S))
print("  with age  : %d" % int(S["age"].notna().sum()))
print("  ppg mean %.2f | p90 %.2f | max %.2f"
      % (S["ppg"].mean(), S["ppg"].quantile(0.9),
         S["ppg"].max()))

N = S[["player_id", "season", "ppg", "g", "tpg"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "nppg", "g": "ng",
                      "tpg": "ntpg"})
P = S.merge(N[["player_id", "season", "nppg", "ng",
               "ntpg"]], on=["player_id", "season"],
            how="left")
PR = S[["player_id", "season", "ppg"]].copy()
PR["season"] = PR["season"] + 1
PR = PR.rename(columns={"ppg": "pppg"})
P = P.merge(PR, on=["player_id", "season"], how="left")

TH = 18.0
E = P[P["ppg"] >= TH].copy()
gone = int(E["nppg"].isna().sum())
F = E[E["nppg"].notna()].copy()
F["ret"] = F["nppg"] / F["ppg"]

print("=== ELITE WR SEASONS (%.0f+ ppg), 2010-2024 ===" % TH)
print("  elite seasons        : %d" % len(E))
print("  no qualifying next yr: %d (%.0f%%) injury/washout"
      % (gone, 100.0 * gone / max(len(E), 1)))
print("  with a next season   : %d" % len(F))
print("\n  next-year ppg   mean %.2f | median %.2f"
      % (F["nppg"].mean(), F["nppg"].median()))
print("  RETENTION       mean %.1f%% | median %.1f%%"
      % (100 * F["ret"].mean(), 100 * F["ret"].median()))
print("  held 90%% or more : %.0f%%"
      % (100 * (F["ret"] >= 0.9).mean()))
print("  improved         : %.0f%%"
      % (100 * (F["ret"] > 1.0).mean()))
print("  fell 20%%+        : %.0f%%"
      % (100 * (F["ret"] < 0.8).mean()))

print("\n=== RETENTION BY AGE ===")
print("  %-8s %5s %9s %9s" % ("age", "n", "retention", "next ppg"))
for lo, hi in [(21, 23), (24, 25), (26, 27),
               (28, 29), (30, 40)]:
    d = F[(F["age"] >= lo) & (F["age"] <= hi)]
    if len(d) < 4:
        continue
    print("  %2d-%-5d %5d %8.1f%% %9.2f"
          % (lo, hi, len(d), 100 * d["ret"].mean(),
             d["nppg"].mean()))

F["asc"] = F["pppg"].notna() & (F["ppg"] > F["pppg"] * 1.25)
print("\n=== BREAKOUT vs ESTABLISHED ===")
print("  breakout = elite yr was 25%+ above prior yr")
for lab, d in [("breakout", F[F["asc"]]),
               ("established", F[~F["asc"]])]:
    if len(d) < 4:
        continue
    print("  %-12s n=%-4d retention %.1f%% | next %.2f ppg"
          % (lab, len(d), 100 * d["ret"].mean(),
             d["nppg"].mean()))

Y = F[F["asc"] & (F["age"] <= 25)]
print("\n=== JSN'S EXACT PROFILE ===")
print("  breakout elite season, age 25 or younger")
print("  n = %d" % len(Y))
if len(Y):
    print("  retention mean %.1f%% | median %.1f%%"
          % (100 * Y["ret"].mean(), 100 * Y["ret"].median()))
    print("  next-year ppg mean %.2f | median %.2f"
          % (Y["nppg"].mean(), Y["nppg"].median()))
    print("  implied JSN 2026: %.2f ppg (mean-based)"
          % (21.17 * Y["ret"].mean()))

N = S[["player_id", "season", "ppg", "g", "tpg"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "nppg", "g": "ng",
                      "tpg": "ntpg"})
P = S.merge(N[["player_id", "season", "nppg", "ng",
               "ntpg"]], on=["player_id", "season"],
            how="left")
PR = S[["player_id", "season", "ppg"]].copy()
PR["season"] = PR["season"] + 1
PR = PR.rename(columns={"ppg": "pppg"})
P = P.merge(PR, on=["player_id", "season"], how="left")

TH = 18.0
E = P[P["ppg"] >= TH].copy()
gone = int(E["nppg"].isna().sum())
F = E[E["nppg"].notna()].copy()
F["ret"] = F["nppg"] / F["ppg"]

print("=== ELITE WR SEASONS (%.0f+ ppg), 2010-2024 ===" % TH)
print("  elite seasons        : %d" % len(E))
print("  no qualifying next yr: %d (%.0f%%) injury/washout"
      % (gone, 100.0 * gone / max(len(E), 1)))
print("  with a next season   : %d" % len(F))
print("\n  next-year ppg   mean %.2f | median %.2f"
      % (F["nppg"].mean(), F["nppg"].median()))
print("  RETENTION       mean %.1f%% | median %.1f%%"
      % (100 * F["ret"].mean(), 100 * F["ret"].median()))
print("  held 90%% or more : %.0f%%"
      % (100 * (F["ret"] >= 0.9).mean()))
print("  improved         : %.0f%%"
      % (100 * (F["ret"] > 1.0).mean()))
print("  fell 20%%+        : %.0f%%"
      % (100 * (F["ret"] < 0.8).mean()))

print("\n=== RETENTION BY AGE ===")
print("  %-8s %5s %9s %9s" % ("age", "n", "retention", "next ppg"))
for lo, hi in [(21, 23), (24, 25), (26, 27),
               (28, 29), (30, 40)]:
    d = F[(F["age"] >= lo) & (F["age"] <= hi)]
    if len(d) < 4:
        continue
    print("  %2d-%-5d %5d %8.1f%% %9.2f"
          % (lo, hi, len(d), 100 * d["ret"].mean(),
             d["nppg"].mean()))

F["asc"] = F["pppg"].notna() & (F["ppg"] > F["pppg"] * 1.25)
print("\n=== BREAKOUT vs ESTABLISHED ===")
print("  breakout = elite yr was 25%+ above prior yr")
for lab, d in [("breakout", F[F["asc"]]),
               ("established", F[~F["asc"]])]:
    if len(d) < 4:
        continue
    print("  %-12s n=%-4d retention %.1f%% | next %.2f ppg"
          % (lab, len(d), 100 * d["ret"].mean(),
             d["nppg"].mean()))

Y = F[F["asc"] & (F["age"] <= 25)]
print("\n=== JSN'S EXACT PROFILE ===")
print("  breakout elite season, age 25 or younger")
print("  n = %d" % len(Y))
if len(Y):
    print("  retention mean %.1f%% | median %.1f%%"
          % (100 * Y["ret"].mean(), 100 * Y["ret"].median()))
    print("  next-year ppg mean %.2f | median %.2f"
          % (Y["nppg"].mean(), Y["nppg"].median()))
    print("  implied JSN 2026: %.2f ppg (mean-based)"
          % (21.17 * Y["ret"].mean()))

A = S[S["age"].between(20, 40)].copy()
print("\n=== WR AGE CURVE, CROSS-SECTIONAL ===")
print("  (survivor-biased: only the good ones last)")
print("  %5s %6s %8s %8s" % ("age", "n", "ppg", "tar/g"))
for a in range(21, 37):
    d = A[A["age"] == a]
    if len(d) < 8:
        continue
    print("  %5d %6d %8.2f %8.2f"
          % (a, len(d), d["ppg"].mean(), d["tpg"].mean()))

A2 = A.merge(N[["player_id", "season", "nppg"]],
             on=["player_id", "season"], how="inner")
A2["dl"] = A2["nppg"] - A2["ppg"]
print("\n=== YEAR-OVER-YEAR CHANGE BY AGE ===")
print("  same players, so this is the real aging signal")
print("  %7s %6s %9s" % ("age", "n", "d ppg"))
for lo, hi in [(21, 23), (24, 25), (26, 27), (28, 29),
               (30, 31), (32, 40)]:
    d = A2[(A2["age"] >= lo) & (A2["age"] <= hi)]
    if len(d) < 8:
        continue
    print("  %2d-%-4d %6d %+9.2f"
          % (lo, hi, len(d), d["dl"].mean()))
pk = A2.groupby(A2["age"].astype(int))["dl"].mean()
pk = pk[pk.index.isin(range(21, 34))]
best = pk[pk > 0]
print("\n  ages still improving on average: %s"
      % (sorted(best.index.tolist()) or "none"))
print("  peak = last age with a positive delta")

j = S[S["display_name"].astype(str)
      .str.contains("Smith-Njigba", na=False)]
print("\n=== JSN TRAJECTORY ===")
for _, r in j.sort_values("season").iterrows():
    print("  %d  age %s  %4.1f tar/g  %6.2f ppg"
          % (r["season"],
             "?" if r["age"] != r["age"] else "%.0f" % r["age"],
             r["tpg"], r["ppg"]))
print("  2026 age: 24")
