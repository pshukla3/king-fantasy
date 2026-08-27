"""
Compare our official roster snapshot against Sleeper's live player database
to catch real-world moves before the official feed updates.

Second bug fix: every single "mismatch" in the last run was LA vs LAR --
nflreadpy abbreviates the Rams as "LA", Sleeper abbreviates them "LAR".
Same team, different spelling, not a real transaction. Data sources
disagreeing on team CODES (not just team assignment) is a common annoyance
when combining multiple free sources -- the fix is a small normalization
dict that maps every known alternate spelling to one canonical code before
we compare anything. This is the same "player ID crosswalk" idea from
04_player_id_crosswalk.py, just applied to team codes instead of player
IDs.

Run with:  python3 18_check_live_transactions.py
"""

import requests
import pandas as pd

# Known alternate team-code spellings across nflverse/Sleeper/others.
# Left side = what we might see, right side = the canonical code we'll
# compare everything against (nflverse's convention, since that's what
# rosters_with_rankings.csv uses everywhere else in this project).
TEAM_CODE_FIXES = {
    "LAR": "LA",
    "JAC": "JAX",
    "WSH": "WAS",
}

def normalize_team(code):
    if pd.isna(code):
        return code
    return TEAM_CODE_FIXES.get(code, code)

print("Fetching live player data from Sleeper...")
resp = requests.get("https://api.sleeper.app/v1/players/nfl", timeout=30)
sleeper_players = resp.json()  # dict keyed by sleeper player_id

sleeper_df = pd.DataFrame.from_dict(sleeper_players, orient="index")
sleeper_df = sleeper_df[["player_id", "team"]].rename(
    columns={"team": "sleeper_team_live"}
)
sleeper_df["sleeper_team_live"] = sleeper_df["sleeper_team_live"].apply(normalize_team)
print("Sleeper player count:", len(sleeper_df))

rosters = pd.read_csv("rosters_with_rankings.csv", low_memory=False)
rosters["sleeper_id"] = rosters["sleeper_id"].astype(str).str.replace(r"\.0$", "", regex=True)
rosters["team"] = rosters["team"].apply(normalize_team)
sleeper_df["player_id"] = sleeper_df["player_id"].astype(str)

merged = rosters.merge(sleeper_df, left_on="sleeper_id", right_on="player_id", how="left")

mismatches = merged[
    merged["sleeper_team_live"].notna()
    & merged["team"].notna()
    & (merged["team"] != merged["sleeper_team_live"])
]

print(f"\nFound {len(mismatches)} players where our roster data disagrees with Sleeper's live data (after normalizing team codes):")
print(mismatches[["full_name", "position", "team", "sleeper_team_live"]].drop_duplicates().to_string(index=False))

mismatches[["full_name", "position", "team", "sleeper_team_live"]].drop_duplicates().to_csv(
    "detected_team_mismatches.csv", index=False
)
print("\nSaved detected_team_mismatches.csv")
