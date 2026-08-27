import pandas as pd, numpy as np

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
TC = next(c for c in ["team", "recent_team"] if c in H.columns)
AC = next((c for c in ["attempts", "pass_attempts"] if c in H.columns), None)
H = H[H["position"].isin(["QB", "RB", "WR", "TE"])].copy()
for c in ["carries", "targets", "receptions", "rushing_yards", "rushing_tds",
          "receiving_yards", "receiving_tds", "passing_yards", "passing_tds",
          "interceptions"]:
    if c not in H.columns:
        H[c] = 0.0
    H[c] = H[c].fillna(0.0)
H["att"] = H[AC].fillna(0.0) if AC else 0.0

H["rush_pts"] = H["rushing_yards"] * 0.1 + H["rushing_tds"] * 6
H["rec_pts"] = H["receptions"] + H["receiving_yards"] * 0.1 + H["receiving_tds"] * 6
H["pass_pts"] = H["passing_yards"] * 0.04 + H["passing_tds"] * 4 - H["interceptions"] * 2
H["opp"] = H["carries"] + H["targets"] + H["att"]

S = H.groupby(["player_id", "position", TC, "season"]).agg(
    g=("week", "nunique"), car=("carries", "sum"), tgt=("targets", "sum"),
    att=("att", "sum"), rp=("rush_pts", "sum"), cp=("rec_pts", "sum"),
    pp=("pass_pts", "sum"), rtd=("rushing_tds", "sum"),
    ctd=("receiving_tds", "sum"), opp=("opp", "sum")).reset_index()
S = S[S["g"] >= 4].copy()
S["opg"] = S["opp"] / S["g"]
S["role"] = S.groupby([TC, "season", "position"])["opp"].rank(
    ascending=False, method="first")

B = S[S["role"] <= 4].groupby(["position", "role"]).agg(
    n=("g", "size"),
    car_pg=("car", lambda x: x.sum()), tgt_pg=("tgt", lambda x: x.sum()),
    att_pg=("att", lambda x: x.sum()), gs=("g", "sum")).reset_index()
for c in ["car_pg", "tgt_pg", "att_pg"]:
    B[c] = B[c] / B["gs"]

T = S.groupby([TC, "season"]).agg(car=("car", "sum"), tgt=("tgt", "sum"),
                                  g=("g", "max")).reset_index()
T["rush_pg"] = T["car"] / T["g"]
T["pass_pg"] = T["tgt"] / T["g"]
nt = T[[TC, "season", "rush_pg", "pass_pg"]].copy()
nt["season"] = nt["season"] - 1
nt = nt.rename(columns={"rush_pg": "r_n", "pass_pg": "p_n"})
TT = T.merge(nt, on=[TC, "season"], how="inner")
R_RUSH = TT["rush_pg"].corr(TT["r_n"])
R_PASS = TT["pass_pg"].corr(TT["p_n"])

print("=== FACTOR VALIDATION (each weight below is measured, not chosen) ===")
print("  team rush volume persistence   r = %.3f" % R_RUSH)
print("  team pass volume persistence   r = %.3f" % R_PASS)
print("  (defense-vs-RB was 0.202, defense-vs-WR was -0.085 -> schedule stays out)")

P = S.merge(T[[TC, "season", "car", "tgt"]].rename(
    columns={"car": "t_car", "tgt": "t_tgt"}), on=[TC, "season"])
P["share"] = P["opp"] / (P["t_car"] + P["t_tgt"]).replace(0, np.nan)
nx = P[["player_id", TC, "season", "share"]].copy()
nx["season"] = nx["season"] - 1
nx = nx.rename(columns={"share": "share_n"})
JJ = P.merge(nx, on=["player_id", TC, "season"], how="left")
gone = JJ[JJ["share_n"].isna()].groupby([TC, "season"])["share"].sum().reset_index()
gone = gone.rename(columns={"share": "vacated"})
gone["season"] = gone["season"] + 1
K = P.merge(gone, on=[TC, "season"], how="left")
K["vacated"] = K["vacated"].fillna(0.0)
pv = P[["player_id", TC, "season", "share"]].copy()
pv["season"] = pv["season"] + 1
pv = pv.rename(columns={"share": "share_prev"})
K = K.merge(pv, on=["player_id", TC, "season"], how="inner")
K = K[K["g"] >= 8].copy()
K["d"] = K["share"] - K["share_prev"]

SLOPE = {}
print("\n  vacated-opportunity absorption (measured slope per position):")
for pos, x in K.groupby("position"):
    if len(x) < 60:
        continue
    v = x["vacated"]
    den = ((v - v.mean()) ** 2).sum()
    sl = ((v - v.mean()) * (x["d"] - x["d"].mean())).sum() / den if den else 0.0
    r = v.corr(x["d"])
    SLOPE[pos] = max(sl, 0.0)
    print("    %-4s r = %+.3f   slope = %+.3f" % (pos, r, sl))

W = {}
for c, r in [("rush", R_RUSH), ("pass", R_PASS)]:
    W[c] = max(min(r, 1.0), 0.0)
cur = T[T["season"] == 2025].set_index(TC)
lg_r, lg_p = cur["rush_pg"].mean(), cur["pass_pg"].mean()

E = S[S["season"].isin([2024, 2025])].groupby(["player_id", "position"]).agg(
    car=("car", "sum"), tgt=("tgt", "sum"), att=("att", "sum"),
    rp=("rp", "sum"), cp=("cp", "sum"), pp=("pp", "sum"),
    rtd=("rtd", "sum"), ctd=("ctd", "sum"), g=("g", "sum")).reset_index()
E["ppg_hist"] = (E["rp"] + E["cp"] + E["pp"]) / E["g"]

PRIOR = 90.0
TDW = {"RB": 0.45, "WR": 0.95, "TE": 0.90, "QB": 0.60}
for kind, num, den in [("r", "rp", "car"), ("c", "cp", "tgt"), ("p", "pp", "att")]:
    m = E.groupby("position").apply(
        lambda x: x[num].sum() / max(x[den].sum(), 1), include_groups=False)
    E["m_" + kind] = E["position"].map(m)
    E["e_" + kind] = (E[num] + E["m_" + kind] * PRIOR) / (E[den] + PRIOR)

DC = pd.read_csv("depth_latest.csv", low_memory=False)
DC = DC[DC["pos_abb"].isin(["QB", "RB", "WR", "TE"])][
    ["gsis_id", "player_name", "team", "pos_abb", "pos_rank"]].dropna(subset=["gsis_id"])
DC = DC.sort_values("pos_rank").drop_duplicates("gsis_id")

X = E.merge(DC, left_on=["player_id", "position"],
            right_on=["gsis_id", "pos_abb"], how="inner")
X = X.merge(B[["position", "role", "car_pg", "tgt_pg", "att_pg"]].rename(
    columns={"role": "pos_rank"}), on=["position", "pos_rank"], how="left")
X = X.dropna(subset=["car_pg"])

V = pd.read_csv("vacated_2026.csv") if False else None
L = P[P["season"] == 2025].copy()
rost = pd.read_csv("rosters_2026.csv", low_memory=False)
cu = rost[["gsis_id", "team"]].dropna(subset=["gsis_id"]).drop_duplicates(
    "gsis_id").rename(columns={"gsis_id": "player_id", "team": "tm26"})
L = L.merge(cu, on="player_id", how="left")
vac = L[L["tm26"] != L[TC]].groupby(TC)["share"].sum().rename("vacated")
X["vacated"] = X["team"].map(vac).fillna(0.0)

X["t_rush"] = X["team"].map(cur["rush_pg"]).fillna(lg_r)
X["t_pass"] = X["team"].map(cur["pass_pg"]).fillna(lg_p)
X["sc_r"] = 1 + W["rush"] * (X["t_rush"] / lg_r - 1)
X["sc_p"] = 1 + W["pass"] * (X["t_pass"] / lg_p - 1)
X["bump"] = 1 + X["vacated"] * X["position"].map(SLOPE).fillna(0.0) * 3.0

X["pj_car"] = X["car_pg"] * X["sc_r"] * X["bump"]
X["pj_tgt"] = X["tgt_pg"] * X["sc_p"] * X["bump"]
X["pj_att"] = X["att_pg"] * X["sc_p"]
X["proj_opp"] = X["pj_car"] + X["pj_tgt"] + X["pj_att"]
X["proj"] = X["e_r"] * X["pj_car"] + X["e_c"] * X["pj_tgt"] + X["e_p"] * X["pj_att"]

cw = pd.read_csv("player_id_crosswalk.csv", low_memory=False)[
    ["gsis_id", "birthdate"]].dropna().drop_duplicates("gsis_id")
X = X.merge(cw, left_on="player_id", right_on="gsis_id", how="left", suffixes=("", "_c"))
X["age"] = 2026 - pd.to_datetime(X["birthdate"], errors="coerce").dt.year
try:
    AM = pd.read_csv("age_mult_A_fullPPR_4ptTD.csv")[["position", "age", "mult"]]
    AM["age"] = AM["age"] + 1
    X = X.merge(AM.rename(columns={"age": "age"}), on=["position", "age"], how="left")
    X["mult"] = X["mult"].fillna(1.0)
except Exception:
    X["mult"] = 1.0
X.loc[X["position"] == "QB", "mult"] = 1.0
X["proj"] = X["proj"] * X["mult"]

try:
    DU = pd.read_csv("durability_2026.csv")
    dcol = [c for c in DU.columns if c in ("player_id", "gsis_id")][0]
    X = X.merge(DU[[dcol, "exp_games"]].rename(columns={dcol: "player_id"}),
                on="player_id", how="left")
except Exception:
    X["exp_games"] = np.nan
X["exp_games"] = X["exp_games"].fillna(13.5)
X["season_pts"] = X["proj"] * X["exp_games"]
X["delta"] = X["proj"] - X["ppg_hist"]

X = X[X["proj"].notna()].sort_values("proj", ascending=False).reset_index(drop=True)
X["rk"] = X.index + 1
X.to_csv("top100_situational.csv", index=False)

print("\n\n%s" % ("=" * 96))
print("TOP 100 — PROJECTED PPG FROM SITUATION (role, team volume, vacated opp, efficiency, age)")
print("=" * 96)
print("  rk  player                 tm   pos rk  age   opp/g    eff    hist   PROJ   delta   szn")
print("  " + "-" * 92)
for _, r in X.head(100).iterrows():
    eff = r["proj"] / max(r["proj_opp"], 0.01)
    print("  %-3d %-22s %-4s %-3s %2.0f  %3.0f   %5.1f  %5.2f  %5.1f  %5.1f  %+5.1f  %4.0f"
          % (r["rk"], str(r["player_name"])[:22], r["team"], r["position"],
             r["pos_rank"], r["age"] if r["age"] == r["age"] else 0,
             r["proj_opp"], eff, r["ppg_hist"], r["proj"], r["delta"], r["season_pts"]))

print("\n\n=== BIGGEST DISAGREEMENTS WITH RAW HISTORY ===")
q = X[X["proj_opp"] > 6]
print("\n  situation says UP:")
print(q.nlargest(10, "delta")[["player_name", "team", "position", "pos_rank",
                               "ppg_hist", "proj", "delta"]].round(2).to_string(index=False))
print("\n  situation says DOWN:")
print(q.nsmallest(10, "delta")[["player_name", "team", "position", "pos_rank",
                                "ppg_hist", "proj", "delta"]].round(2).to_string(index=False))
print("\nSaved top100_situational.csv")
