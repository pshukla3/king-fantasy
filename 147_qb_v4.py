import numpy as np
import pandas as pd

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
for c in ["attempts", "passing_yards", "passing_tds",
          "rushing_yards", "rushing_tds"]:
    H[c] = pd.to_numeric(H[c], errors="coerce").fillna(0)
Q = H[H["position"] == "QB"].copy()
TC = "team" if "team" in H.columns else "recent_team"
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX"}
S = Q.groupby(["player_id", "season"]).agg(
    att=("attempts", "sum"), td=("passing_tds", "sum"),
    pyd=("passing_yards", "sum")).reset_index()
S = S[S["att"] >= 100].sort_values(
    ["player_id", "season"]).reset_index(drop=True)
LG_TD = S["td"].sum() / S["att"].sum()
LG_YPA = S["pyd"].sum() / S["att"].sum()
RK = pd.read_csv("rookie_qb_seasons.csv")
R5 = RK[RK["pick"] <= 5]
RK_YPA, RK_TDR = float(R5["ypa"].mean()), float(R5["tdr"].mean())
RK_RY = float(R5["ryd"].sum() / R5["g"].sum())


def build(d, K):
    out = []
    for pid, g in S.groupby("player_id"):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            t = int(g.at[i, "season"])
            h = g[g["season"] <= t]
            w = d ** (t - h["season"])
            out.append({
                "player_id": pid, "season": t,
                "wa": float((w * h["att"]).sum()),
                "wt": float((w * h["td"]).sum()),
                "wy": float((w * h["pyd"]).sum())})
    return pd.DataFrame(out)


N = S.copy()
N["season"] = N["season"] - 1
N["tdr_n"] = N["td"] / N["att"]
N = N[["player_id", "season", "tdr_n"]]
yrs = sorted(S["season"].unique())
c1, c2 = yrs[int(len(yrs) * .5)], yrs[int(len(yrs) * .75)]
best, K = (9.9, 1.0), 500.0
for d in [1.0, 0.8, 0.6, 0.5, 0.4]:
    W = build(d, K)
    W["tdr"] = (W["wt"] + K * LG_TD) / (W["wa"] + K)
    P = W.merge(N, on=["player_id", "season"], how="inner")
    v = P[(P["season"] >= c1) & (P["season"] < c2)]
    e = (v["tdr"] - v["tdr_n"]).abs().mean()
    print("  d %.1f  val MAE %.5f" % (d, e))
    if e < best[0]:
        best = (e, d)
DEC = best[1]
print("DECAY = %.1f (validation-selected)" % DEC)
W = build(DEC, K)
W = W[W["season"] == 2025][["player_id", "wa", "wt", "wy"]]
W.to_csv("qb_weighted_2025.csv", index=False)
print("weighted rates for %d QBs" % len(W))

TS2 = Q.groupby([TC, "season", "player_id"]).agg(
    att=("attempts", "sum"),
    g=("week", "nunique")).reset_index()
TS2["r"] = TS2.groupby([TC, "season"])["att"].rank(
    ascending=False, method="first")
TG = Q.groupby([TC, "season"])["week"].nunique(
    ).reset_index().rename(columns={"week": "tg"})
TS2 = TS2.merge(TG, on=[TC, "season"], how="left")
TS2["sh"] = TS2["g"] / TS2["tg"]
ROLE = {1: float(TS2[TS2["r"] == 1]["sh"].mean()),
        2: float(TS2[TS2["r"] == 2]["sh"].mean()),
        3: float(TS2[TS2["r"] >= 3]["sh"].mean())}
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
B = pd.read_csv("board_final.csv", low_memory=False)
BQ = B[B["position"] == "QB"][
    ["player_id", "depth_rank", "team"]]
X = SP[SP["position"] == "QB"].copy()
for c in ["attempts", "rushing_yards", "rushing_tds"]:
    X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
IR = pd.read_csv("qb_int_rates.csv")[["player_id", "rate"]]
AGf = pd.read_csv("qb_birthyears.csv")
for fr in (W, IR, AGf):
    X = X.merge(fr, on="player_id", how="left")
X = X.merge(BQ, on="player_id", how="left",
            suffixes=("", "_b"))
for c in ["wa", "wt", "wy"]:
    X[c] = X[c].fillna(0)
X["tm"] = X["team_b"].fillna(X["team"]).astype(str)
X["dr"] = X["depth_rank"].fillna(3).clip(1, 3)
X["age"] = 2026 - X["by"]
X["nov"] = X["wa"] < 100
X["ypa"] = ((X["wy"] + np.where(X["nov"], RK_YPA, LG_YPA)
             * K) / (X["wa"] + K))
X["tdr"] = ((X["wt"] + np.where(X["nov"], RK_TDR, LG_TD)
             * K) / (X["wa"] + K))
X["intr"] = X["rate"].fillna(0.0211)
w = (X["wa"] / (X["wa"] + 600.0)).clip(0, 1)
X["att"] = (w * X["attempts"]
            + (1 - w) * X["tm"].map(TEAM).fillna(LG_APG))
X.loc[X["nov"] & (X["rushing_yards"] <= 0),
      "rushing_yards"] = RK_RY
X["sh"] = X["dr"].map(ROLE).fillna(ROLE[3])
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
X["start"] = (X["att"] * X["ypa"] * float(V["pass_yd"])
              + X["att"] * X["tdr"] * float(V["pass_td"])
              + X["att"] * X["intr"] * float(V["pass_int"])
              + X["rushing_yards"] * float(V["rush_yd"])
              + X["rushing_tds"] * float(V["rush_td"]))
X["exp"] = X["start"] * X["sh"]
print("\nQB1 share %.2f | QB2 %.2f | QB3 %.2f"
      % (ROLE[1], ROLE[2], ROLE[3]))
md = X[X["player_display_name"].astype(str)
       .str.contains("Mendoza", na=False)]
print("Mendoza rows found: %d" % len(md))
if len(md):
    r = md.iloc[0]
    print("  dr %.0f | att %.1f | ypa %.2f | %.2f ppg"
          % (r["dr"], r["att"], r["ypa"], r["start"]))

ST = X[X["dr"] == 1].sort_values(
    "start", ascending=False).reset_index(drop=True)
ST["qbr"] = ST.index + 1
REPL = float(ST.iloc[9]["start"])
print("\n=== 2026 QB RANKINGS, DECAY %.1f, 17 GAMES ==="
      % DEC)
print("  %-3s %-21s %-4s %3s %6s %6s %6s %6s"
      % ("#", "player", "tm", "age", "att", "ppg",
         "TOT17", "vorp"))
print("  " + "-" * 62)
for _, r in ST.iterrows():
    ag = "%3.0f" % r["age"] if r["age"] == r["age"] else "  ?"
    print("  %-3d %-21s %-4s %s %6.1f %6.2f %6.0f %+6.2f"
          % (r["qbr"], str(r["player_display_name"])[:21],
             r["tm"][:4], ag, r["att"], r["start"],
             r["start"] * 17, r["start"] - REPL))
print("\n=== SANITY vs OUTSIDE ===")
for k, note in (("Darnold", "ESPN 242 pts, QB22-26"),
                ("Rodgers", "2025 actual 14.6 ppg"),
                ("Mendoza", "1st overall rookie"),
                ("Allen", "consensus QB1")):
    h = ST[ST["player_display_name"].astype(str)
           .str.contains(k, na=False)]
    if len(h):
        r = h.iloc[0]
        print("  QB%-2d %-18s %6.2f ppg  %4.0f pts  <- %s"
              % (r["qbr"], str(r["player_display_name"])[:18],
                 r["start"], r["start"] * 17, note))
    else:
        print("  %-18s NOT A STARTER" % k)
X.to_csv("qb_all_2026.csv", index=False)
up = X.set_index("player_id")["exp"].to_dict()
B["points"] = B.apply(
    lambda r: up.get(r["player_id"], r["points"])
    if r["position"] == "QB" else r["points"], axis=1)
B.to_csv("board_final.csv", index=False)
print("\n  QB10 replacement %.2f | wrote qb_all_2026.csv"
      % REPL)
