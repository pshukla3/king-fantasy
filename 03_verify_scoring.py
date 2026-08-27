"""
Step 1c: Check our own scoring.py against nflreadpy's built-in numbers.

If our hand-written PPR formula doesn't closely match nflreadpy's own
fantasy_points_ppr column, something in our formula is wrong. Small gaps
are expected (nflreadpy's version may include things like 2-point
conversions or fumble penalties that our simple formula skips) -- the
point is to see how close we are and understand why any gap exists.

Run with:  python3 03_verify_scoring.py
"""

import pandas as pd
from scoring import PPR, calculate_fantasy_points

real = pd.read_csv("real_weekly_stats.csv")
real["our_ppr_points"] = calculate_fantasy_points(real, PPR)

comparison = real[["player_display_name", "week", "season",
                    "our_ppr_points", "fantasy_points_ppr"]].copy()
comparison["difference"] = (comparison["our_ppr_points"] - comparison["fantasy_points_ppr"]).round(2)

print(comparison.head(10))
print("\nBiggest mismatches:")
biggest = comparison.reindex(comparison["difference"].abs().sort_values(ascending=False).index)
print(biggest.head(10))

print("\nAverage absolute difference across all rows:", comparison["difference"].abs().mean().round(3))
