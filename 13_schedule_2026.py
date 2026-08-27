"""
Step: 2026 schedule, opponents, and bye weeks for draft-day prep.

Run with:  python3 13_schedule_2026.py
"""

import pandas as pd

schedules = pd.read_csv("schedules.csv", low_memory=False)
sched_2026 = schedules[schedules["season"] == 2026].copy()

print("2026 schedule shape:", sched_2026.shape)
print("Weeks present:", sorted(sched_2026["week"].unique()))

# One row per team per week played, with opponent and home/away.
home_side = sched_2026[["week", "home_team", "away_team"]].rename(
    columns={"home_team": "team", "away_team": "opponent"}
)
home_side["home_or_away"] = "home"

away_side = sched_2026[["week", "away_team", "home_team"]].rename(
    columns={"away_team": "team", "home_team": "opponent"}
)
away_side["home_or_away"] = "away"

team_schedule = pd.concat([home_side, away_side], ignore_index=True).sort_values(["team", "week"])

# Bye week = whichever week 1-18 has no row for that team.
bye_weeks = {}
for team in team_schedule["team"].unique():
    played = set(team_schedule[team_schedule["team"] == team]["week"])
    missing = set(range(1, 19)) - played
    bye_weeks[team] = sorted(missing)[0] if missing else None

print("\n--- Bye weeks by team ---")
for team, bye in sorted(bye_weeks.items(), key=lambda x: (x[1] is None, x[1])):
    print(f"{team}: Week {bye}")

team_schedule.to_csv("team_schedule_2026.csv", index=False)
print("\nSaved team_schedule_2026.csv")

print("\n--- Sample: full 2026 schedule for KC ---")
print(team_schedule[team_schedule["team"] == "KC"].to_string(index=False))
