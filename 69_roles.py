import pandas as pd, re

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
TC = next(c for c in ["team", "recent_team"] if c in H.columns)
PC = "fantasy_points_ppr"
H = H[H["position"].isin(["RB", "WR", "TE"])].copy()
for c in ["carries", "targets"]:
    if c not in H.columns:
        H[c] = 0.0
H["opp"] = H["carries"].fillna(0) + H["targets"].fillna(0)

S = H.groupby(["player_id", "position", TC, "season"]).agg(
    g=("week", "nunique"), pts=(PC, "sum"), opp=("opp", "sum")).reset_index()
S = S[S["g"] >= 4].copy()
S["ppg"] = S["pts"] / S["g"]
S["opg"] = S["opp"] / S["g"]
S["eff"] = S["pts"] / S["opp"].replace(0, float("nan"))
S["role"] = S.groupby([TC, "season", "position"])["opp"].rank(
    ascending=False, method="first")

B = S[S["role"] <= 5].groupby(["position", "role"]).agg(
    n=("opg", "size"), opg=("opg", "mean"), ppg=("ppg", "mean"),
    eff=("eff", "mean")).reset_index()

print("=== WHAT EACH ROLE ACTUALLY GETS (2014-2025) ===")
print("  opg = opportunities/game (carries + targets) | eff = pts per opportunity")
print("  " + "-" * 56)
print("  pos  role     n     opg     ppg    eff")
for _, r in B.iterrows():
    print("  %-4s  %d   %5d   %5.1f   %5.1f   %.3f"
          % (r["position"], r["role"], r["n"], r["opg"], r["ppg"], r["eff"]))

nxt = S[["player_id", "season", "ppg", "role", "g"]].copy()
nxt["season"] = nxt["season"] - 1
nxt = nxt.rename(columns={"ppg": "ppg_next", "role": "role_next", "g": "g_next"})
D = S.merge(nxt, on=["player_id", "season"], how="inner")
D = D[(D["g_next"] >= 8) & (D["opp"] >= 20)].copy()
D = D.merge(B[["position", "role", "opg"]].rename(
    columns={"role": "role_next", "opg": "opg_role"}),
    on=["position", "role_next"], how="left").dropna(subset=["opg_role", "eff"])
D["pred_role"] = D["eff"] * D["opg_role"]

print("\n\n=== DOES ROLE-AWARE PRICING BEAT RAW PPG? ===")
print("  raw   = last year's ppg predicting next year's ppg")
print("  role  = (his efficiency) x (opportunity his NEW role gets)")
print("  " + "-" * 56)
print("  pos     n     raw    role   best_blend   w_role")
for pos, x in D.groupby("position"):
    if len(x) < 40:
        continue
    ra = x["ppg"].corr(x["ppg_next"])
    rr = x["pred_role"].corr(x["ppg_next"])
    bw, br = 0.0, -1.0
    for i in range(21):
        w = i / 20.0
        r = (w * x["pred_role"] + (1 - w) * x["ppg"]).corr(x["ppg_next"])
        if r > br:
            br, bw = r, w
    print("  %-4s %5d   %.3f   %.3f      %.3f      %.2f"
          % (pos, len(x), ra, rr, br, bw))

R = S[S["season"].isin([2024, 2025])].groupby(
    ["player_id", "position"]).agg(pts=("pts", "sum"), opp=("opp", "sum"),
                                   g=("g", "sum")).reset_index()
R["eff"] = R["pts"] / R["opp"].replace(0, float("nan"))
R["ppg_hist"] = R["pts"] / R["g"]

DC = pd.read_csv("depth_latest.csv", low_memory=False)
DC = DC[DC["pos_abb"].isin(["RB", "WR", "TE"])][
    ["gsis_id", "player_name", "team", "pos_abb", "pos_rank"]].dropna(subset=["gsis_id"])
DC = DC.sort_values("pos_rank").drop_duplicates("gsis_id")

P = R.merge(DC, left_on=["player_id", "position"],
            right_on=["gsis_id", "pos_abb"], how="inner")
P = P.merge(B[["position", "role", "opg"]].rename(
    columns={"role": "pos_rank", "opg": "opg_role"}),
    on=["position", "pos_rank"], how="left")
P["pred_role"] = P["eff"] * P["opg_role"]
P["gap"] = P["pred_role"] - P["ppg_hist"]
P.to_csv("role_projections.csv", index=False)

MINE = ["Tuten", "Hampton", "Henderson", "Dowdle", "Mitchell", "Smith-Njigba",
        "Pickens", "Higgins", "Downs", "Samuel", "Shaheed", "Pitts"]
print("\n\n=== YOUR ROSTER: HISTORICAL PPG vs ROLE-IMPLIED PPG ===")
print("  ppg_hist = what the model uses now | pred = efficiency x role opportunity")
print("  " + "-" * 66)
print("  player                  tm  pos rk    eff    opg   ppg_hist   pred    gap")
for nm in MINE:
    h = P[P["player_name"].astype(str).str.contains(nm, na=False)]
    if not len(h):
        print("  %-22s  no depth-chart match" % nm)
        continue
    r = h.iloc[0]
    print("  %-22s %-4s %-3s %2.0f  %.3f  %5.1f    %5.1f    %5.1f  %+5.1f"
          % (r["player_name"], r["team"], r["position"], r["pos_rank"],
             r["eff"], r["opg_role"], r["ppg_hist"], r["pred_role"], r["gap"]))

print("\n\n=== LEAGUE-WIDE: BIGGEST ROLE-DRIVEN CORRECTIONS ===")
q = P[(P["opp"] >= 60) & P["pred_role"].notna()]
print("\n  model is TOO LOW (earned a bigger role than his history shows)")
print(q.nlargest(12, "gap")[["player_name", "team", "position", "pos_rank",
                             "ppg_hist", "pred_role", "gap"]].round(2).to_string(index=False))
print("\n  model is TOO HIGH (lost the job)")
print(q.nsmallest(12, "gap")[["player_name", "team", "position", "pos_rank",
                              "ppg_hist", "pred_role", "gap"]].round(2).to_string(index=False))
print("\nSaved role_projections.csv")
