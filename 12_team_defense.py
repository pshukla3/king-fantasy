"""
Step: Team defense / special teams projections.

Points allowed is the biggest single factor in most leagues' defense
scoring, but it isn't a "defensive stat" in team_stats -- it's the
OTHER team's score in that game. We get it by joining onto the schedule
and picking whichever score wasn't this team's own.

Note on data completeness: we don't have a clean "blocked kick" column
for the defending team, so that scoring category is left out here --
a known, minor gap (blocked kicks are rare) rather than a bug.

Run with:  python3 12_team_defense.py
"""

import pandas as pd
from scoring import DEFENSE_STANDARD, calculate_defense_points

team_stats = pd.read_csv("team_stats.csv", low_memory=False)
schedules = pd.read_csv("schedules.csv", low_memory=False)

team_stats = team_stats[team_stats["season_type"].isin(["REG", "POST"])].copy()

games = schedules[["game_id", "home_team", "away_team", "home_score", "away_score"]]
merged = team_stats.merge(games, on="game_id", how="left")

merged["points_allowed"] = merged.apply(
    lambda row: row["away_score"] if row["team"] == row["home_team"] else row["home_score"],
    axis=1,
)

print("Rows missing points_allowed (should be ~0):", merged["points_allowed"].isna().sum())

merged = merged.sort_values(["team", "season", "week"])
merged["def_points"] = calculate_defense_points(merged, DEFENSE_STANDARD)

grouped = merged.groupby("team")
merged["ewm_points"] = grouped["def_points"].transform(lambda s: s.shift(1).ewm(span=4, min_periods=1).mean())
merged["season_avg_points"] = grouped["def_points"].transform(lambda s: s.shift(1).expanding(min_periods=1).mean())

BLEND_WEIGHT = 0.5
merged["final_projection"] = (
    BLEND_WEIGHT * merged["ewm_points"] + (1 - BLEND_WEIGHT) * merged["season_avg_points"]
)

latest_def = merged.groupby("team").tail(1)
top_def = latest_def.sort_values("final_projection", ascending=False)

print("\n--- All 32 Team Defenses ranked by final_projection ---")
print(top_def[["team", "final_projection", "ewm_points", "season_avg_points"]].to_string(index=False))

merged.to_csv("team_defense_weekly_with_projections.csv", index=False)
latest_def.to_csv("latest_team_defense_projections.csv", index=False)
print("\nSaved team_defense_weekly_with_projections.csv and latest_team_defense_projections.csv")
