import numpy as np
import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
PROMOTE = {"Fernando Mendoza": 1}
DEMOTE = {"Ty Simpson": 2, "Trevor Siemian": 3,
          "Carson Beck": 3, "Drew Allar": 3}
DOWN = {"Kirk Cousins": 2}
n = 0
for nm, d in list(PROMOTE.items()) + list(
        DEMOTE.items()) + list(DOWN.items()):
    m = (B["position"] == "QB") & (
        B["player_display_name"].astype(str) == nm)
    if m.sum():
        B.loc[m, "depth_rank"] = d
        n += int(m.sum())
        print("  %-22s depth_rank -> %d" % (nm, d))
    else:
        print("  %-22s NOT FOUND" % nm)
B.to_csv("board_final.csv", index=False)
QB = B[B["position"] == "QB"]
print("set %d | starters now %d | unranked %d"
      % (n, int((QB["depth_rank"] == 1).sum()),
         int(QB["depth_rank"].isna().sum())))

RK = pd.read_csv("rookie_qb_seasons.csv")
R5 = RK[RK["pick"] <= 5]
RK_YPA = float(R5["ypa"].mean())
RK_TDR = float(R5["tdr"].mean())
RK_RY = float(R5["ryd"].sum() / R5["g"].sum())
RK_RT = float(R5["rtd"].sum() / R5["g"].sum())
RKA = float(RK["ypa"].mean())
RKT = float(RK["tdr"].mean())
print("\nrookie priors")
print("  top5   ypa %.2f tdr %.4f rush %.1f/%.2f"
      % (RK_YPA, RK_TDR, RK_RY, RK_RT))
print("  allrk  ypa %.2f tdr %.4f" % (RKA, RKT))

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
for c in ["attempts", "passing_yards", "passing_tds",
          "rushing_yards", "rushing_tds"]:
    H[c] = pd.to_numeric(H[c], errors="coerce").fillna(0)
Q = H[H["position"] == "QB"].copy()
TC = "team" if "team" in H.columns else "recent_team"
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX"}

TS2 = Q.groupby([TC, "season", "player_id"]).agg(
    att=("attempts", "sum"),
    g=("week", "nunique")).reset_index()
TS2["r"] = TS2.groupby([TC, "season"])["att"].rank(
    ascending=False, method="first")
TG = Q.groupby([TC, "season"])["week"].nunique(
    ).reset_index().rename(columns={"week": "tg"})
TS2 = TS2.merge(TG, on=[TC, "season"], how="left")
TS2["share"] = TS2["g"] / TS2["tg"]
P1 = float(TS2[TS2["r"] == 1]["share"].mean())
P2 = float(TS2[TS2["r"] == 2]["share"].mean())
P3 = float(TS2[TS2["r"] >= 3]["share"].mean())
print("\n=== MEASURED ROLE SHARE ===")
print("  team QB1 plays %.0f%% of games" % (100 * P1))
print("  team QB2 plays %.0f%% of games" % (100 * P2))
print("  team QB3+ plays %.0f%% of games" % (100 * P3))
ROLE = {1: P1, 2: P2, 3: P3}

S = Q.groupby(["player_id", "season"]).agg(
    att=("attempts", "sum"), td=("passing_tds", "sum"),
    pyd=("passing_yards", "sum")).reset_index()
S = S[S["att"] >= 100]
LG_TD = S["td"].sum() / S["att"].sum()
LG_YPA = S["pyd"].sum() / S["att"].sum()
CAR = S.groupby("player_id").agg(
    catt=("att", "sum"), ctd=("td", "sum"),
    cyd=("pyd", "sum")).reset_index()
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
T = TV[TV["season"] == 2025][[TC, "apg"]].copy()
T["proj"] = LG_APG + RATT * (T["apg"] - LG_APG)
T[TC] = T[TC].astype(str).replace(FIX)
TEAM = dict(zip(T[TC], T["proj"]))

SP = pd.read_csv("stat_projections_2026.csv",
                 low_memory=False)
X = SP[SP["position"] == "QB"].copy()
for c in ["attempts", "rushing_yards", "rushing_tds"]:
    X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
BQ = B[B["position"] == "QB"][
    ["player_id", "depth_rank", "team", "exp_games"]]
IR = pd.read_csv("qb_int_rates.csv")[["player_id", "rate"]]
AGf = pd.read_csv("qb_birthyears.csv")
for fr in (CAR, IR, AGf):
    X = X.merge(fr, on="player_id", how="left")
X = X.merge(BQ, on="player_id", how="left",
            suffixes=("", "_b"))
for c in ["catt", "ctd", "cyd"]:
    X[c] = X[c].fillna(0)
X["tm"] = X["team_b"].fillna(X["team"]).astype(str)
X["dr"] = X["depth_rank"].fillna(3).clip(1, 3)
X["age"] = 2026 - X["by"]
K = 500.0
X["nov"] = X["catt"] < 100
X["pri_y"] = np.where(X["nov"], RK_YPA, LG_YPA)
X["pri_t"] = np.where(X["nov"], RK_TDR, LG_TD)
X["ypa"] = (X["cyd"] + X["pri_y"] * K) / (X["catt"] + K)
X["tdr"] = (X["ctd"] + X["pri_t"] * K) / (X["catt"] + K)
X["intr"] = X["rate"].fillna(0.0211)
w = (X["catt"] / (X["catt"] + 600.0)).clip(0, 1)
X["tv"] = X["tm"].map(TEAM).fillna(LG_APG)
X["att"] = w * X["attempts"] + (1 - w) * X["tv"]
X.loc[X["nov"], "rushing_yards"] = np.where(
    X.loc[X["nov"], "rushing_yards"] > 0,
    X.loc[X["nov"], "rushing_yards"], RK_RY)
X["shr"] = X["dr"].map(ROLE).fillna(P3)
print("\nQBs to rank: %d" % len(X))

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
PY, PT = float(V["pass_yd"]), float(V["pass_td"])
PI, RY = float(V["pass_int"]), float(V["rush_yd"])
RT = float(V["rush_td"])
GM = 17

X["start"] = (X["att"] * X["ypa"] * PY
              + X["att"] * X["tdr"] * PT
              + X["att"] * X["intr"] * PI
              + X["rushing_yards"] * RY
              + X["rushing_tds"] * RT)
X["exp"] = X["start"] * X["shr"]
X = X.sort_values("exp", ascending=False)
X = X.reset_index(drop=True)
X["ovr"] = X.index + 1
ST = X[X["dr"] == 1].sort_values(
    "start", ascending=False).reset_index(drop=True)
ST["qbr"] = ST.index + 1
REPL = float(ST.iloc[9]["start"])

print("\n=== 2026 QB RANKINGS, ALL STARTERS ===")
print("  ppg if starting | 17-game total | vs QB10\n")
print("  %-3s %-21s %-4s %3s %6s %6s %6s %6s"
      % ("#", "player", "tm", "age", "att", "ppg",
         "TOT17", "vorp"))
print("  " + "-" * 62)
for _, r in ST.iterrows():
    ag = "%3.0f" % r["age"] if r["age"] == r["age"] else "  ?"
    print("  %-3d %-21s %-4s %s %6.1f %6.2f %6.0f %+6.2f"
          % (r["qbr"], str(r["player_display_name"])[:21],
             r["tm"][:4], ag, r["att"], r["start"],
             r["start"] * GM, r["start"] - REPL))

BK = X[X["dr"] >= 2].sort_values("start", ascending=False)
print("\n=== BACKUPS: VALUE IF THEY TAKE OVER ===")
print("  QB2 plays %.0f%% of games historically\n"
      % (100 * P2))
print("  %-21s %-4s %2s %7s %7s %7s"
      % ("player", "tm", "dr", "ifstart", "expect",
         "vs QB10"))
print("  " + "-" * 56)
for _, r in BK.head(16).iterrows():
    print("  %-21s %-4s %2.0f %7.2f %7.2f %+7.2f"
          % (str(r["player_display_name"])[:21],
             r["tm"][:4], r["dr"], r["start"],
             r["exp"], r["start"] - REPL))

X["qb_ppg"] = X["exp"]
X[["player_id", "player_display_name", "tm", "dr",
   "age", "att", "ypa", "tdr", "intr", "start",
   "exp"]].to_csv("qb_all_2026.csv", index=False)
up = X.set_index("player_id")["exp"].to_dict()
B["points"] = B.apply(
    lambda r: up.get(r["player_id"], r["points"])
    if r["position"] == "QB" else r["points"], axis=1)
B.to_csv("board_final.csv", index=False)
print("\n  replacement QB10 = %.2f ppg" % REPL)
print("  wrote qb_all_2026.csv")
print("  patched %d QB rows in board_final.csv" % len(X))
