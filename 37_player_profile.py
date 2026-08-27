import pandas as pd

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
H = H[H["season"].isin([2024, 2025])]
print("air_yards col:", "receiving_air_yards" in H.columns,
      "| yac col:", "receiving_yards_after_catch" in H.columns)

g = H.groupby("player_id")
prof = pd.DataFrame({
    "games": g.size(),
    "ppg": g["fantasy_points_ppr"].mean(),
    "sd": g["fantasy_points_ppr"].std(),
    "boom_rate": g["fantasy_points_ppr"].apply(lambda s: (s >= 20).mean()),
    "bust_rate": g["fantasy_points_ppr"].apply(lambda s: (s <= 5).mean()),
    "tgt": g["targets"].sum(),
    "rec": g["receptions"].sum(),
    "rec_yds": g["receiving_yards"].sum(),
}).reset_index()

for c, nm in [("receiving_air_yards", "air"), ("receiving_yards_after_catch", "yac")]:
    if c in H.columns:
        prof = prof.merge(g[c].sum().rename(nm).reset_index(), on="player_id", how="left")

prof["ypt"] = prof["rec_yds"] / prof["tgt"].replace(0, float("nan"))
if "air" in prof.columns:
    prof["aypt"] = prof["air"] / prof["tgt"].replace(0, float("nan"))
if "yac" in prof.columns:
    prof["yac_per_rec"] = prof["yac"] / prof["rec"].replace(0, float("nan"))
prof["cv"] = prof["sd"] / prof["ppg"].replace(0, float("nan"))

opp = pd.read_csv("ff_opportunity.csv", low_memory=False)
opp = opp[opp["season"].isin([2024, 2025])]
o = opp.groupby("player_id").agg(
    td=("total_touchdown", "sum"), td_exp=("total_touchdown_exp", "sum"),
    fp=("total_fantasy_points", "sum"), fp_exp=("total_fantasy_points_exp", "sum"),
    tgts=("rec_attempt", "sum"), tgts_team=("rec_attempt_team", "sum"),
    og=("week", "size")).reset_index()
o["td_luck"] = o["td"] - o["td_exp"]
o["fp_luck_pg"] = (o["fp"] - o["fp_exp"]) / o["og"]
o["tgt_share"] = o["tgts"] / o["tgts_team"].replace(0, float("nan"))

prof = prof.merge(o[["player_id", "td", "td_exp", "td_luck", "fp_luck_pg", "tgt_share"]],
                  on="player_id", how="left")
prof.to_csv("player_profile.csv", index=False)
print("Saved player_profile.csv:", prof.shape)

nm = H.sort_values(["season", "week"]).groupby("player_id").tail(1)[
    ["player_id", "player_display_name", "position"]]
p = prof.merge(nm, on="player_id").query("position == 'WR' and games >= 15")

print("\n--- WRs most likely to REGRESS (scored way above expected TDs) ---")
print(p.nlargest(10, "td_luck")[["player_display_name", "games", "td", "td_exp", "td_luck", "fp_luck_pg"]].round(2).to_string(index=False))
print("\n--- WRs due to BOUNCE BACK (scored below expected TDs) ---")
print(p.nsmallest(10, "td_luck")[["player_display_name", "games", "td", "td_exp", "td_luck", "fp_luck_pg"]].round(2).to_string(index=False))
print("\n--- Highest target share ---")
print(p.nlargest(10, "tgt_share")[["player_display_name", "tgt_share", "ypt", "ppg", "sd"]].round(3).to_string(index=False))
