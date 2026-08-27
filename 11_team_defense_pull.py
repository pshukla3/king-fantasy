"""
Step: Pull team-level stats and schedule data for defense/ST scoring
(and for the bye-week/opponent view coming right after).

Run with:  python3 11_team_defense_pull.py
"""

import nflreadpy as nfl

team_stats = nfl.load_team_stats(seasons=[2023, 2024, 2025]).to_pandas()
print("Team stats shape:", team_stats.shape)
print("Team stats columns:", list(team_stats.columns))
print(team_stats.head())

# Pull 2026 too -- we need this same file for the schedule/bye-week task next.
schedules = nfl.load_schedules(seasons=[2023, 2024, 2025, 2026]).to_pandas()
print("\nSchedules shape:", schedules.shape)
print("Schedules columns:", list(schedules.columns))
print(schedules.head())

team_stats.to_csv("team_stats.csv", index=False)
schedules.to_csv("schedules.csv", index=False)
print("\nSaved team_stats.csv and schedules.csv")
