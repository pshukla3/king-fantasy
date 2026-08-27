import pandas as pd, engine

W_REC, W_RUSH = 0.92, 0.45
LEAGUE = {"teams": 10,
          "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"],
          "scoring": {"pass_yd": 0.04, "pass_td": 4, "pass_int": -2, "rush_yd": 0.1,
                      "rush_td": 6, "rec": 1.0, "rec_yd": 0.1, "rec_td": 6, "fum_lost": -2}}

proj = pd.read_csv("stat_projections_2026.csv", low_memory=False)
o = pd.read_csv("ff_opportunity.csv", low_memory=False)
o = o[o["season"] >= 2023]
g = o.groupby("player_id").agg(
    gm=("week", "size"),
    rec_td=("rec_touchdown", "sum"), rec_td_exp=("rec_touchdown_exp", "sum"),
    rush_td=("rush_touchdown", "sum"), rush_td_exp=("rush_touchdown_exp", "sum")).reset_index()
g = g[g["gm"] >= 10]
g["rec_td_adj"] = (W_REC * g["rec_td_exp"] + (1 - W_REC) * g["rec_td"]) / g["gm"]
g["rush_td_adj"] = (W_RUSH * g["rush_td_exp"] + (1 - W_RUSH) * g["rush_td"]) / g["gm"]

proj = proj.merge(g[["player_id", "rec_td_adj", "rush_td_adj"]], on="player_id", how="left")
proj["receiving_tds"] = proj["rec_td_adj"].fillna(proj["receiving_tds"])
proj["rushing_tds"] = proj["rush_td_adj"].fillna(proj["rushing_tds"])
print("TD-regressed players:", proj["rec_td_adj"].notna().sum())

hist = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
birth = pd.read_csv("player_id_crosswalk.csv", low_memory=False)[["gsis_id", "birthdate"]]
birth = birth.dropna().drop_duplicates("gsis_id")
b, rel, repl = engine.build_board(proj, LEAGUE, hist, birth)

POSAVAIL = {"QB": 0.619, "RB": 0.654, "TE": 0.654, "WR": 0.694}
dur = pd.read_csv("durability_2026.csv", low_memory=False)[["player_id", "exp_games", "avail_hist"]]
b = b.merge(dur, on="player_id", how="left")
b["exp_games"] = b["exp_games"].fillna(b["position"].map(POSAVAIL) * 17)
b["source"] = "model"

rk = pd.read_csv("rookie_projections_2026.csv", low_memory=False)
rk = rk[rk["ppg_expected"] > 0].rename(columns={
    "gsis_id": "player_id", "full_name": "player_display_name", "ppg_expected": "points"})
rk["repl"] = rk["position"].map(repl)
rk["vorp"] = rk["points"] - rk["repl"]
rk["reliability"] = rk["position"].map(rel).fillna(0.5)
rk["exp_games"] = rk["position"].map(POSAVAIL) * 17
rk["avail_hist"] = float("nan")
rk["source"] = "draft_capital"

keep = ["player_id", "player_display_name", "position", "team", "points", "vorp",
        "reliability", "exp_games", "avail_hist", "source"]
allp = pd.concat([b[keep], rk[keep]], ignore_index=True)
allp["season_pts"] = allp["exp_games"] * allp["points"]
allp["value"] = allp["exp_games"] * allp["vorp"] * allp["reliability"]
allp = allp.sort_values("value", ascending=False).reset_index(drop=True)
allp["rank"] = allp.index + 1
allp["pos_rank"] = allp.groupby("position")["value"].rank(ascending=False, method="min").astype(int)
allp.to_csv("board_v4.csv", index=False)

print("\nreplacement ppg:", {k: round(v, 2) for k, v in repl.items()})
print("\n=== BOARD v4 (TD-regressed + durability-weighted): TOP 50 ===")
print(allp.head(50)[["rank", "player_display_name", "position", "pos_rank", "team",
                     "points", "exp_games", "vorp", "value", "source"]].round(2).to_string(index=False))
print("\nSaved board_v4.csv")
