"""
Check whether individual defensive player stats (sacks, etc.) exist for
Myles Garrett -- confirms we have what we need before building the
trade-impact estimate.

Run with:  python3 14_check_garrett_data.py
"""

import pandas as pd

df = pd.read_csv("weekly_stats_with_ids.csv", low_memory=False)

garrett = df[df["player_display_name"].str.contains("Garrett", case=False, na=False)]
print(garrett[["player_display_name", "position", "team", "season", "week",
               "def_sacks", "def_interceptions", "def_tds"]].to_string(index=False))

print("\nHis career average sacks/game in this dataset:", garrett["def_sacks"].mean().round(3))
