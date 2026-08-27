import pandas as pd, engine

LEAGUE = {"teams": 10,
          "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"],
          "scoring": {"pass_yd": 0.04, "pass_td": 4, "pass_int": -2, "rush_yd": 0.1,
                      "rush_td": 6, "rec": 1.0, "rec_yd": 0.1, "rec_td": 6, "fum_lost": -2}}

proj = pd.read_csv("stat_projections_2026.csv", low_memory=False)
hist = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
birth = pd.read_csv("player_id_crosswalk.csv", low_memory=False)[["gsis_id", "birthdate"]]
birth = birth.dropna().drop_duplicates("gsis_id")

vet, rel, repl = engine.build_board(proj, LEAGUE, hist, birth)
vet["source"] = "model"
vet["confidence"] = 1.0
keep = ["player_id", "player_display_name", "position", "team", "points", "vorp",
        "reliability", "value", "source", "confidence"]
vet = vet[keep]

rk = pd.read_csv("rookie_projections_2026.csv", low_memory=False)
rk = rk[rk["ppg_expected"] > 0].copy()
rk = rk.rename(columns={"gsis_id": "player_id", "full_name": "player_display_name",
                        "ppg_expected": "points", "pct_10g": "confidence"})
rk["reliability"] = rk["position"].map(rel).fillna(0.5)
rk["vorp"] = rk["points"] - rk["position"].map(repl)
rk["value"] = rk["vorp"] * rk["reliability"]
rk["source"] = "draft_capital"
rk = rk[keep]

allp = pd.concat([vet, rk], ignore_index=True)

cw = pd.read_csv("player_id_crosswalk.csv", low_memory=False)
fp = cw[["gsis_id", "fantasypros_id"]].dropna()
fp["fantasypros_id"] = fp["fantasypros_id"].astype(int).astype(str)
fp = fp.drop_duplicates("fantasypros_id")
ff = pd.read_csv("ff_rankings.csv", low_memory=False)
e = ff[ff["page_type"] == "redraft-overall"].dropna(subset=["id"]).copy()
e["id"] = e["id"].astype(int).astype(str)
e = e.merge(fp, left_on="id", right_on="fantasypros_id", how="left")
e = e[["gsis_id", "ecr"]].dropna(subset=["gsis_id"]).rename(columns={"gsis_id": "player_id"})
allp = allp.merge(e, on="player_id", how="left")

pr = pd.read_csv("player_profile.csv", low_memory=False)[
    ["player_id", "td_luck", "tgt_share", "sd"]]
allp = allp.merge(pr, on="player_id", how="left")

allp = allp.sort_values("value", ascending=False).reset_index(drop=True)
allp["overall"] = allp.index + 1
allp["pos_rank"] = allp.groupby("position")["value"].rank(ascending=False, method="min").astype(int)
allp["ecr_gap"] = allp["ecr"] - allp["overall"]
allp.to_csv("full_rankings_2026.csv", index=False)

cols = ["pos_rank", "overall", "player_display_name", "team", "points", "value",
        "ecr", "ecr_gap", "td_luck", "tgt_share", "sd", "source"]
for pos, n in [("RB", 30), ("WR", 35), ("QB", 20), ("TE", 20)]:
    print(f"\n{'='*95}\n{pos} RANKINGS — 10-team full PPR, 2 FLEX\n{'='*95}")
    print(allp[allp["position"] == pos].head(n)[cols].round(2).to_string(index=False))
print("\nSaved full_rankings_2026.csv")
