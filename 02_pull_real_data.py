"""
Step 1b (v2): Pull REAL historical NFL stats using nflreadpy.

We switched from nfl_data_py to nflreadpy because nfl_data_py pins a very
old pandas version with no installer for a brand-new Python like 3.13 --
nflreadpy is the actively maintained, modern replacement and installs
cleanly.

One real difference: nflreadpy hands back data as a Polars DataFrame (a
newer, faster alternative to pandas) instead of a pandas DataFrame. Since
we've been learning pandas, we immediately convert it with .to_pandas() so
every script after this one still works the way we've practiced.

Run with:  python3 02_pull_real_data.py
"""

import nflreadpy as nfl

weekly_polars = nfl.load_player_stats(seasons=[2023, 2024, 2025])
weekly = weekly_polars.to_pandas()

print("Shape (rows, columns):", weekly.shape)
print(weekly.head())
print("\nColumns available:", list(weekly.columns))

weekly.to_csv("real_weekly_stats.csv", index=False)
print("\nSaved to real_weekly_stats.csv")
