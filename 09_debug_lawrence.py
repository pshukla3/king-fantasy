"""
Debug: why is Trevor Lawrence ranked #1 QB? Look at the raw games behind it.
"""

import pandas as pd

df = pd.read_csv("weekly_stats_with_projections.csv", low_memory=False)

lawrence = df[(df["player_display_name"] == "Trevor Lawrence") & (df["season"] == 2025)]
lawrence = lawrence.sort_values("week")

print("Week-by-week 2025 season:")
print(lawrence[["week", "passing_yards", "passing_tds", "passing_interceptions",
                 "rushing_yards", "rushing_tds", "ppr_points", "roll4_points"]].to_string(index=False))

print("\nFull 2025 season average PPR points:", lawrence["ppr_points"].mean().round(2))
print("His final roll4_points (last-4-game average):", lawrence["roll4_points"].iloc[-1])
