"""
Overall VBD (Value Based Drafting) rankings across all positions.

Two bugs fixed from the last run:
1. I forgot to filter latest_player_projections.csv down to just
   QB/RB/WR/TE before combining -- so defensive players and fullbacks
   (anyone with a nonzero receiving/rushing stat line, since our scoring
   formula doesn't check position) leaked into the draft board with
   meaningless "replacement values," since our league's replacement_ranks
   dict only defines QB/RB/WR/TE/K/DST.
2. The team fallback for unmatched players didn't actually work, because
   we never kept the original "team" column from the projections file to
   fall back to -- so anyone missing from rosters_with_rankings.csv
   (retired, ID mismatch, etc.) showed team = NaN instead of their last
   known team.

Run with:  python3 16_draft_rankings.py
"""

import pandas as pd

LEAGUE_SETTINGS = {
    "num_teams": 12,
    "starters": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DST": 1},
    "flex_rb_share": 0.5,
}

def replacement_ranks(settings):
    n = settings["num_teams"]
    starters = settings["starters"]
    flex_rb = round(starters["FLEX"] * settings["flex_rb_share"])
    flex_wr = starters["FLEX"] - flex_rb
    return {
        "QB": n * starters["QB"],
        "RB": n * (starters["RB"] + flex_rb),
        "WR": n * (starters["WR"] + flex_wr),
        "TE": n * starters["TE"],
        "K": n * starters["K"],
        "DST": n * starters["DST"],
    }

replacement_rank_by_pos = replacement_ranks(LEAGUE_SETTINGS)
print("Replacement rank per position for this league:", replacement_rank_by_pos)

# --- Current, correct team assignments (includes our manual trade/signing overrides) ---
current_teams = pd.read_csv("rosters_with_rankings.csv", low_memory=False)
current_teams = current_teams[["gsis_id", "team"]].rename(columns={"team": "current_team"})
current_teams = current_teams.dropna(subset=["gsis_id"]).drop_duplicates(subset="gsis_id")

# --- Skill position players (QB/RB/WR/TE) ONLY -- this is the position filter that was missing ---
SKILL_POSITIONS = ["QB", "RB", "WR", "TE"]

players = pd.read_csv("latest_player_projections.csv", low_memory=False)
players = players[players["position"].isin(SKILL_POSITIONS)].copy()
players = players[["player_id", "player_display_name", "position", "team", "final_projection"]].rename(
    columns={"player_id": "gsis_id", "player_display_name": "name", "team": "last_known_team"}
)
players = players.merge(current_teams, on="gsis_id", how="left")
players["team"] = players["current_team"].fillna(players["last_known_team"])
players = players.drop(columns=["current_team", "last_known_team"])

# --- Kickers ---
kickers = pd.read_csv("latest_kicker_projections.csv", low_memory=False)
kickers = kickers[["player_id", "player_display_name", "team", "final_projection"]].rename(
    columns={"player_id": "gsis_id", "player_display_name": "name", "team": "last_known_team"}
)
kickers["position"] = "K"
kickers = kickers.merge(current_teams, on="gsis_id", how="left")
kickers["team"] = kickers["current_team"].fillna(kickers["last_known_team"])
kickers = kickers.drop(columns=["current_team", "last_known_team"])

# --- Team defenses (no gsis_id to look up -- team code IS the identity) ---
defenses = pd.read_csv("latest_team_defense_projections.csv", low_memory=False)
defenses = defenses[["team", "final_projection"]].copy()
defenses["name"] = defenses["team"] + " D/ST"
defenses["position"] = "DST"
defenses["gsis_id"] = None

all_players = pd.concat(
    [players[["gsis_id", "name", "position", "team", "final_projection"]],
     kickers[["gsis_id", "name", "position", "team", "final_projection"]],
     defenses[["gsis_id", "name", "position", "team", "final_projection"]]],
    ignore_index=True,
)
all_players = all_players.dropna(subset=["final_projection"])

def get_replacement_value(group):
    pos = group.name
    rank = replacement_rank_by_pos.get(pos)
    sorted_vals = group["final_projection"].sort_values(ascending=False).reset_index(drop=True)
    if rank is None or rank > len(sorted_vals):
        return sorted_vals.iloc[-1]
    return sorted_vals.iloc[rank - 1]

replacement_values = all_players.groupby("position").apply(get_replacement_value)
print("\nReplacement-level projected points per position:")
print(replacement_values)

all_players["replacement_value"] = all_players["position"].map(replacement_values)
all_players["vorp"] = all_players["final_projection"] - all_players["replacement_value"]

draft_board = all_players.sort_values("vorp", ascending=False).reset_index(drop=True)
draft_board["overall_rank"] = draft_board.index + 1

print("\n--- Top 50 Overall Draft Rankings (VBD) ---")
print(draft_board[["overall_rank", "name", "position", "team", "final_projection", "vorp"]].head(50).to_string(index=False))

draft_board.to_csv("overall_draft_rankings.csv", index=False)
print("\nSaved to overall_draft_rankings.csv")
