"""
Step 3 (v4): Blend recent form with season-long stability, explicitly.

BLEND_WEIGHT controls how much we trust the recent (EWM) signal vs. the
full-season average. 1.0 = pure recency (today's behavior), 0.0 = pure
season average (ignores hot/cold streaks entirely). There's no
mathematically "correct" value -- it's a real judgment call. 0.5 is a
reasonable starting point; try 0.3 or 0.7 later and see how the rankings
shift, to build intuition for how sensitive the model is to this choice.

Run with:  python3 06_usage_baseline.py
"""

import pandas as pd
from scoring import PPR, calculate_fantasy_points

BLEND_WEIGHT = 0.5  # <-- tune this and re-run to see the effect

df = pd.read_csv("weekly_stats_with_ids.csv", low_memory=False)
df = df[df["season_type"].isin(["REG", "POST"])].copy()
df["ppr_points"] = calculate_fantasy_points(df, PPR)
df = df.sort_values(["player_id", "season", "week"])

grouped = df.groupby("player_id")
df["ewm_points"] = grouped["ppr_points"].transform(lambda s: s.shift(1).ewm(span=4, min_periods=1).mean())
df["season_avg_points"] = grouped["ppr_points"].transform(lambda s: s.shift(1).expanding(min_periods=1).mean())
df["ewm_targets"] = grouped["targets"].transform(lambda s: s.shift(1).ewm(span=4, min_periods=1).mean())
df["ewm_carries"] = grouped["carries"].transform(lambda s: s.shift(1).ewm(span=4, min_periods=1).mean())

df["final_projection"] = (
    BLEND_WEIGHT * df["ewm_points"] + (1 - BLEND_WEIGHT) * df["season_avg_points"]
)

latest = df.groupby("player_id").tail(1)

print(f"--- QB check at BLEND_WEIGHT={BLEND_WEIGHT} ---")
check = latest[latest["player_display_name"].isin(["Trevor Lawrence", "Brock Purdy", "Drake Maye"])]
print(check[["player_display_name", "ewm_points", "season_avg_points", "final_projection"]].to_string(index=False))

top_qb = latest[latest["position"] == "QB"].sort_values("final_projection", ascending=False).head(10)
print("\n--- Top 10 QBs by blended final_projection ---")
print(top_qb[["player_display_name", "team", "ewm_points", "season_avg_points", "final_projection"]].to_string(index=False))

df.to_csv("weekly_stats_with_projections.csv", index=False)
latest.to_csv("latest_player_projections.csv", index=False)
print("\nSaved weekly_stats_with_projections.csv and latest_player_projections.csv")
