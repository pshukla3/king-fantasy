"""
Step: Rebuild position rankings using the blended final_projection.

Run with:  python3 08_position_rankings.py
"""

import pandas as pd

rosters = pd.read_csv("rosters_2026.csv", low_memory=False)
proj = pd.read_csv("latest_player_projections.csv", low_memory=False)

rosters = rosters.sort_values("week").drop_duplicates(subset="gsis_id", keep="last")

proj_slim = proj[["player_id", "final_projection", "ewm_points", "season_avg_points",
                   "ewm_targets", "ewm_carries", "season", "week"]]
proj_slim = proj_slim.rename(columns={"season": "last_data_season", "week": "last_data_week"})

merged = rosters.merge(proj_slim, left_on="gsis_id", right_on="player_id", how="left")

has_data = merged["final_projection"].notna()
print(f"Rostered players WITH prior performance data: {has_data.sum()} / {len(merged)}")
print(f"Rostered players with NO prior data (rookies/new entrants): {(~has_data).sum()}")

merged["position_rank"] = merged.groupby("position")["final_projection"].rank(ascending=False, method="min")

for pos in ["QB", "RB", "WR", "TE"]:
    print(f"\n--- Top 10 {pos}s by final_projection ---")
    subset = merged[merged["position"] == pos].sort_values("position_rank").head(10)
    print(subset[["full_name", "team", "position_rank", "final_projection",
                   "ewm_points", "season_avg_points"]].to_string(index=False))

merged.to_csv("rosters_with_rankings.csv", index=False)
print("\nSaved to rosters_with_rankings.csv")
