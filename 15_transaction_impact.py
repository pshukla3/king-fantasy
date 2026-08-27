"""
Manual transaction override + impact analysis.

Official roster data lags real news by days or weeks -- a trade can be
reported and even reshape betting lines before nflverse's feed catches up.
This script lets you log real moves the moment they happen (edit
manual_transactions.csv), then:

1. Estimates the fantasy impact using the player's own historical
   production -- explicitly a DIRECTIONAL estimate, not a precise
   forecast. It can't capture scheme fit, added attention from opposing
   coordinators, or how his presence changes teammates' one-on-one
   matchups -- only his own direct, attributable stats (sacks,
   interceptions, etc.).
2. Overrides his team in our working roster data, so every downstream
   script (rankings, player pages) sees the correct team going forward.

Run with:  python3 15_transaction_impact.py
"""

import pandas as pd
from scoring import DEFENSE_STANDARD

transactions = pd.read_csv("manual_transactions.csv")
weekly = pd.read_csv("weekly_stats_with_ids.csv", low_memory=False)
defense_latest = pd.read_csv("latest_team_defense_projections.csv", low_memory=False)
rosters = pd.read_csv("rosters_with_rankings.csv", low_memory=False)

for _, tx in transactions.iterrows():
    player, old_team, new_team = tx["player_name"], tx["old_team"], tx["new_team"]

    # Exact name match -- avoids the "Garrett Wilson" mixup from the check script.
    player_games = weekly[(weekly["player_display_name"] == player) & (weekly["season"] == 2025)]
    if player_games.empty:
        print(f"No 2025 data found for {player} -- skipping impact estimate.")
        continue

    per_game_sacks = player_games["def_sacks"].mean()
    per_game_ints = player_games["def_interceptions"].mean()
    per_game_fumbles = player_games["fumble_recovery_opp"].mean()
    per_game_tds = player_games["def_tds"].mean()
    per_game_safety = player_games["def_safeties"].mean()

    points_contribution = (
        per_game_sacks * DEFENSE_STANDARD["sack"]
        + per_game_ints * DEFENSE_STANDARD["interception"]
        + per_game_fumbles * DEFENSE_STANDARD["fumble_recovery"]
        + per_game_tds * DEFENSE_STANDARD["defensive_td"]
        + per_game_safety * DEFENSE_STANDARD["safety"]
    )

    print(f"\n=== {player}: {old_team} -> {new_team} ({tx['transaction_type']}) ===")
    print(f"2025 per-game averages: {per_game_sacks:.2f} sacks, {per_game_ints:.2f} INTs, "
          f"{per_game_fumbles:.2f} fumble rec, {per_game_tds:.2f} def TDs")
    print(f"His personal direct fantasy-point contribution to a defense: {points_contribution:.2f} pts/game")

    old_row = defense_latest.loc[defense_latest["team"] == old_team, "final_projection"]
    new_row = defense_latest.loc[defense_latest["team"] == new_team, "final_projection"]

    if not old_row.empty:
        old_val = old_row.values[0]
        print(f"{old_team} defense projection: {old_val:.2f} -> est. {old_val - points_contribution:.2f} without him")
    if not new_row.empty:
        new_val = new_row.values[0]
        print(f"{new_team} defense projection: {new_val:.2f} -> est. {new_val + points_contribution:.2f} with him added")

    print("Caveat: this only counts his OWN attributable stats. It doesn't model "
          "second-order effects like opposing offenses game-planning around him, "
          "or how his presence frees up teammates for easier matchups -- treat "
          "this as a floor estimate of the impact, not the full picture.")

    rosters.loc[rosters["full_name"] == player, "team"] = new_team

rosters.to_csv("rosters_with_rankings.csv", index=False)
print(f"\nRoster override applied and saved. {transactions['player_name'].tolist()} "
      "will now show on their new team(s) in every downstream script.")
