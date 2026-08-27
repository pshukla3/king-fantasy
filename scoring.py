import pandas as pd

STANDARD = {
    "reception": 0.0,
    "rushing_yard": 0.1,
    "receiving_yard": 0.1,
    "passing_yard": 0.04,        # 1 point per 25 passing yards (common default)
    "rushing_td": 6.0,
    "receiving_td": 6.0,
    "passing_td": 4.0,           # some leagues use 6 -- change here for those
    "passing_interception": -2.0,
}

HALF_PPR = {**STANDARD, "reception": 0.5}
PPR = {**STANDARD, "reception": 1.0}


def calculate_fantasy_points(df: pd.DataFrame, rules: dict) -> pd.Series:
    return (
        df["receptions"] * rules["reception"]
        + df["rushing_yards"] * rules["rushing_yard"]
        + df["receiving_yards"] * rules["receiving_yard"]
        + df["passing_yards"] * rules["passing_yard"]
        + df["rushing_tds"] * rules["rushing_td"]
        + df["receiving_tds"] * rules["receiving_td"]
        + df["passing_tds"] * rules["passing_td"]
        + df["passing_interceptions"] * rules["passing_interception"]
    )


# --- Kicker scoring -- completely different stat categories than skill
# positions, so this is a separate function rather than an extension of
# calculate_fantasy_points.
KICKER_STANDARD = {
    "fg_0_39": 3.0,
    "fg_40_49": 4.0,
    "fg_50_plus": 5.0,
    "pat_made": 1.0,
    "fg_missed": 0.0,  # some leagues penalize misses (-1) -- change here if yours does
}


def calculate_kicker_points(df: pd.DataFrame, rules: dict) -> pd.Series:
    fg_0_39 = df["fg_made_0_19"] + df["fg_made_20_29"] + df["fg_made_30_39"]
    fg_50_plus = df["fg_made_50_59"] + df["fg_made_60_"]
    fg_missed_total = (
        df["fg_missed_0_19"] + df["fg_missed_20_29"] + df["fg_missed_30_39"]
        + df["fg_missed_40_49"] + df["fg_missed_50_59"] + df["fg_missed_60_"]
    )
    return (
        fg_0_39 * rules["fg_0_39"]
        + df["fg_made_40_49"] * rules["fg_40_49"]
        + fg_50_plus * rules["fg_50_plus"]
        + df["pat_made"] * rules["pat_made"]
        + fg_missed_total * rules["fg_missed"]
    )


# --- Team defense / special teams scoring -- also a separate function,
# since it operates on team-level game data, not individual player stats.
import numpy as np

DEFENSE_STANDARD = {
    "sack": 1.0,
    "interception": 2.0,
    "fumble_recovery": 2.0,
    "defensive_td": 6.0,
    "safety": 2.0,
}

# Points-allowed bonus tiers -- a very common standard scale. Adjust the
# thresholds/values here if your league uses a different scale.
def _points_allowed_bonus(points_allowed):
    conditions = [
        points_allowed == 0,
        (points_allowed >= 1) & (points_allowed <= 6),
        (points_allowed >= 7) & (points_allowed <= 13),
        (points_allowed >= 14) & (points_allowed <= 20),
        (points_allowed >= 21) & (points_allowed <= 27),
        (points_allowed >= 28) & (points_allowed <= 34),
        points_allowed >= 35,
    ]
    choices = [10, 7, 4, 1, 0, -1, -4]
    return np.select(conditions, choices, default=0)


def calculate_defense_points(df: pd.DataFrame, rules: dict) -> pd.Series:
    """df must already have a 'points_allowed' column (see 12_team_defense.py)."""
    base = (
        df["def_sacks"] * rules["sack"]
        + df["def_interceptions"] * rules["interception"]
        + df["fumble_recovery_opp"] * rules["fumble_recovery"]
        + (df["def_tds"] + df["special_teams_tds"]) * rules["defensive_td"]
        + df["def_safeties"] * rules["safety"]
    )
    return base + _points_allowed_bonus(df["points_allowed"])
