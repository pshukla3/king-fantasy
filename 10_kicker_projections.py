"""
Step: Kicker projections. Also switches to including playoff games
(REG + POST) instead of regular season only, per your request.

Run with:  python3 10_kicker_projections.py
"""

import pandas as pd
from scoring import KICKER_STANDARD, calculate_kicker_points

df = pd.read_csv("weekly_stats_with_ids.csv", low_memory=False)

# Now includes playoffs -- more data for players/teams that made a run.
df = df[df["season_type"].isin(["REG", "POST"])].copy()

kickers = df[df["position"] == "K"].copy()
kickers = kickers.sort_values(["player_id", "season", "week"])
kickers["k_points"] = calculate_kicker_points(kickers, KICKER_STANDARD)

grouped = kickers.groupby("player_id")
kickers["ewm_points"] = grouped["k_points"].transform(lambda s: s.shift(1).ewm(span=4, min_periods=1).mean())
kickers["season_avg_points"] = grouped["k_points"].transform(lambda s: s.shift(1).expanding(min_periods=1).mean())

BLEND_WEIGHT = 0.5
kickers["final_projection"] = (
    BLEND_WEIGHT * kickers["ewm_points"] + (1 - BLEND_WEIGHT) * kickers["season_avg_points"]
)

latest_k = kickers.groupby("player_id").tail(1)
top_k = latest_k.sort_values("final_projection", ascending=False).head(15)

print("--- Top 15 Kickers by final_projection ---")
print(top_k[["player_display_name", "team", "final_projection", "ewm_points", "season_avg_points"]].to_string(index=False))

kickers.to_csv("kicker_weekly_with_projections.csv", index=False)
latest_k.to_csv("latest_kicker_projections.csv", index=False)
print("\nSaved kicker_weekly_with_projections.csv and latest_kicker_projections.csv")
