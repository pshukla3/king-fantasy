"""
Step 2b (v2): Attach the crosswalk onto our real stats -- fixed.

Bug from last run: the crosswalk file has one row PER PLAYER PER SEASON
(see the db_season column), not one row per player. Merging on gsis_id
without deduplicating first caused a "fan-out" -- each stats row matched
every season-snapshot for that player, multiplying our row count from
57,045 to 352,923. Lesson: before merging, always check whether your
join key is actually unique on the side you're joining against.

Run with:  python3 05_merge_crosswalk.py
"""

import pandas as pd

weekly = pd.read_csv("real_weekly_stats.csv", low_memory=False)
ids = pd.read_csv("player_id_crosswalk.csv", low_memory=False)

ids_slim = ids[["gsis_id", "sleeper_id", "espn_id", "yahoo_id", "merge_name", "db_season"]]

# Keep exactly one row per player: the most recent season snapshot.
ids_slim = (
    ids_slim.dropna(subset=["gsis_id"])
            .sort_values("db_season")
            .drop_duplicates(subset="gsis_id", keep="last")
)

print("Is gsis_id now unique in the crosswalk?", ids_slim["gsis_id"].is_unique)

merged = weekly.merge(ids_slim, left_on="player_id", right_on="gsis_id", how="left")

print("Weekly stats shape before merge:", weekly.shape)
print("Merged shape after merge:", merged.shape, "(row count should now match)")

unmatched = merged["sleeper_id"].isna().sum()
print(f"\nRows with no crosswalk match: {unmatched} out of {len(merged)}")

print("\nSample of matched rows:")
print(merged[["player_display_name", "player_id", "sleeper_id", "espn_id", "yahoo_id"]].dropna(subset=["sleeper_id"]).head(10))

merged.to_csv("weekly_stats_with_ids.csv", index=False)
print("\nSaved to weekly_stats_with_ids.csv")
