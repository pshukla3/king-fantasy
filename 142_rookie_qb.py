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
TC = "team" if "team" in H.columns else "recent_team"
S = Q.groupby(["player_id", "season"]).agg(
    att=("attempts", "sum"), td=("passing_tds", "sum"),
    pyd=("passing_yards", "sum"),
    ryd=("rushing_yards", "sum"),
    rtd=("rushing_tds", "sum"),
    pts=(PC, "sum"), g=("week", "nunique")).reset_index()
S = S[S["att"] >= 100].copy()
S["ppg"] = S["pts"] / S["g"]
S["ypa"] = S["pyd"] / S["att"]
S["tdr"] = S["td"] / S["att"]
S["apg"] = S["att"] / S["g"]
LG_YPA = S["pyd"].sum() / S["att"].sum()
LG_TD = S["td"].sum() / S["att"].sum()
LG_PPG = S["ppg"].mean()
LG_APG = S["apg"].mean()

DP = nfl.load_draft_picks()
DP = DP.to_pandas() if hasattr(DP, "to_pandas") else DP
idc = "gsis_id" if "gsis_id" in DP.columns else "player_id"
DP = DP[DP["position"].astype(str).str.upper() == "QB"]
DP = DP[[idc, "season", "round", "pick"]].rename(
    columns={idc: "player_id", "season": "dyr"})
DP = DP.dropna(subset=["player_id"]).drop_duplicates(
    "player_id")
print("QBs with draft data: %d" % len(DP))

J = S.merge(DP, on="player_id", how="inner")
J["exp"] = J["season"] - J["dyr"]
RK = J[J["exp"] == 0].copy()
print("rookie QB seasons with 100+ att: %d" % len(RK))


def buck(p):
    if p <= 5:
        return "top5"
    if p <= 32:
        return "rd1"
    if p <= 100:
        return "rd2-3"
    return "late"


RK["bk"] = RK["pick"].apply(buck)
print("\n=== WHAT ROOKIE QBs ACTUALLY DO ===")
print("  league mean ypa %.2f | tdr %.4f | ppg %.2f"
      % (LG_YPA, LG_TD, LG_PPG))
print("\n  %-6s %4s %6s %7s %6s %6s"
      % ("bucket", "n", "ypa", "tdr", "apg", "ppg"))
for b in ["top5", "rd1", "rd2-3", "late"]:
    d = RK[RK["bk"] == b]
    if len(d) < 3:
        continue
    print("  %-6s %4d %6.2f %7.4f %6.1f %6.2f"
          % (b, len(d), d["ypa"].mean(), d["tdr"].mean(),
             d["apg"].mean(), d["ppg"].mean()))
print("\n  ALL rookies vs league:")
print("  ypa %.2f vs %.2f  (%+.1f%%)"
      % (RK["ypa"].mean(), LG_YPA,
         100 * (RK["ypa"].mean() / LG_YPA - 1)))
print("  tdr %.4f vs %.4f  (%+.1f%%)"
      % (RK["tdr"].mean(), LG_TD,
         100 * (RK["tdr"].mean() / LG_TD - 1)))
print("  ppg %.2f vs %.2f  (%+.1f%%)"
      % (RK["ppg"].mean(), LG_PPG,
         100 * (RK["ppg"].mean() / LG_PPG - 1)))
RK.to_csv("rookie_qb_seasons.csv", index=False)

yrs = sorted(RK["season"].unique())
ct = yrs[int(len(yrs) * 0.6)]
TR = RK[RK["season"] < ct]
TS = RK[RK["season"] >= ct]
print("\n=== GATE: DOES DRAFT SLOT BEAT A FLAT PRIOR? ===")
print("  train < %d (n=%d) | test >= %d (n=%d)"
      % (ct, len(TR), ct, len(TS)))

for lab, cl, lg in (("ypa", "ypa", LG_YPA),
                    ("tdr", "tdr", LG_TD),
                    ("ppg", "ppg", LG_PPG)):
    flat = TR[cl].mean()
    b1 = TR["pick"].cov(TR[cl]) / TR["pick"].var()
    a1 = TR[cl].mean() - b1 * TR["pick"].mean()
    m0 = (flat - TS[cl]).abs().mean()
    m1 = (a1 + b1 * TS["pick"] - TS[cl]).abs().mean()
    print("\n  %s" % lab)
    print("    rookie flat prior      %.4f" % flat)
    print("    league-wide value      %.4f" % lg)
    print("    slope per draft pick   %+.6f" % b1)
    print("    test MAE flat %.4f -> slot %.4f (%+.1f%%)"
          % (m0, m1, 100 * (1 - m1 / m0)))
    print("    DECISION: %s"
          % ("USE DRAFT SLOT" if m1 < m0 - 1e-9
             else "USE FLAT ROOKIE PRIOR"))

R1 = RK[RK["pick"] <= 5]
print("\n=== TOP-5 PICK ROOKIE SEASONS ===")
nm = pd.read_csv("board_final.csv", low_memory=False)
nm = nm[["player_id", "player_display_name"]]
nm = nm.drop_duplicates("player_id")
R1 = R1.merge(nm, on="player_id", how="left")
R1 = R1.sort_values("season", ascending=False)
print("  %-22s %4s %4s %6s %6s %6s"
      % ("player", "yr", "pk", "ypa", "tdr", "ppg"))
for _, r in R1.head(18).iterrows():
    n2 = r["player_display_name"]
    n2 = str(n2)[:22] if n2 == n2 else str(r["player_id"])
    print("  %-22s %4d %4.0f %6.2f %6.4f %6.2f"
          % (n2, r["season"], r["pick"], r["ypa"],
             r["tdr"], r["ppg"]))
print("\n  top5 mean ppg %.2f | sd %.2f | min %.2f max %.2f"
      % (R1["ppg"].mean(), R1["ppg"].std(),
         R1["ppg"].min(), R1["ppg"].max()))

B = pd.read_csv("board_final.csv", low_memory=False)
QB = B[B["position"] == "QB"].copy()
miss = QB[QB["depth_rank"].isna()]
print("\n=== QBs WITH NO DEPTH RANK ===")
print("  each one's full QB room below\n")
for _, r in miss.iterrows():
    tm = str(r["team"])
    room = QB[QB["team"].astype(str) == tm].copy()
    room = room.sort_values("points", ascending=False)
    print("  %s (%s) rank %s  proj %.2f"
          % (r["player_display_name"], tm,
             r["rank"], r["points"]))
    for _, q in room.iterrows():
        d = q["depth_rank"]
        d = "%.0f" % d if d == d else "NONE"
        mk = "  <<<" if q["player_id"] == r["player_id"] else ""
        print("      dr %-4s %-22s %6.2f%s"
              % (d, str(q["player_display_name"])[:22],
                 q["points"], mk))
    print("")

TV = Q.groupby([TC, "season"]).agg(
    att=("attempts", "sum"),
    g=("week", "nunique")).reset_index()
TV["apg"] = TV["att"] / TV["g"]
LGA = TV["apg"].mean()
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX"}
T25 = TV[TV["season"] == 2025][[TC, "apg"]].copy()
T25[TC] = T25[TC].astype(str).replace(FIX)
TM = dict(zip(T25[TC], T25["apg"]))
r5 = RK[RK["pick"] <= 5]
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
print("=== MENDOZA UNDER THE ROOKIE PRIOR ===")
lv = TM.get("LV", LGA)
ypa = r5["ypa"].mean()
tdr = r5["tdr"].mean()
apg = min(r5["apg"].mean(), lv)
ry = r5["ryd"].sum() / r5["g"].sum()
rt = r5["rtd"].sum() / r5["g"].sum()
p = (apg * ypa * float(V["pass_yd"])
     + apg * tdr * float(V["pass_td"])
     + apg * 0.0211 * float(V["pass_int"])
     + ry * float(V["rush_yd"])
     + rt * float(V["rush_td"]))
print("  LV 2025 team volume   %.1f att/g" % lv)
print("  top5 rookie att/g     %.1f" % r5["apg"].mean())
print("  used att/g            %.1f" % apg)
print("  ypa %.2f (lg %.2f) | tdr %.4f (lg %.4f)"
      % (ypa, LG_YPA, tdr, LG_TD))
print("  rush %.1f yd %.2f td per game" % (ry, rt))
print("\n  PROJECTION  %.2f ppg | %.0f pts over 17"
      % (p, p * 17))
print("  board currently has him at 15.23 ppg")
print("  top5 rookie range was %.2f to %.2f ppg"
      % (r5["ppg"].min(), r5["ppg"].max()))
