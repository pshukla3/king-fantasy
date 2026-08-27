"""
Step: Pull additional free data sources -- injuries, expert consensus
rankings, and an expected-points opportunity model -- plus a quick look
at Jahmyr Gibbs's actual game log.

Wrapped in try/except per source: these are functions we haven't used
yet, so if one has a different signature than expected, we still get the
others instead of the whole script dying on the first surprise.

Run with:  python3 17_pull_more_sources.py
"""

import nflreadpy as nfl
import pandas as pd

print("=== Injuries ===")
try:
    injuries = nfl.load_injuries(seasons=[2023, 2024, 2025]).to_pandas()
    print("Shape:", injuries.shape)
    print("Columns:", list(injuries.columns))
    print(injuries.head())
    injuries.to_csv("injuries.csv", index=False)
except Exception as e:
    print("load_injuries failed:", e)

print("\n=== FantasyPros consensus expert rankings ===")
try:
    ff_rankings = nfl.load_ff_rankings().to_pandas()
    print("Shape:", ff_rankings.shape)
    print("Columns:", list(ff_rankings.columns))
    print(ff_rankings.head())
    ff_rankings.to_csv("ff_rankings.csv", index=False)
except Exception as e:
    print("load_ff_rankings failed:", e)

print("\n=== Expected fantasy points (opportunity model) ===")
try:
    opportunity = nfl.load_ff_opportunity(seasons=[2023, 2024, 2025]).to_pandas()
    print("Shape:", opportunity.shape)
    print("Columns:", list(opportunity.columns))
    print(opportunity.head())
    opportunity.to_csv("ff_opportunity.csv", index=False)
except Exception as e:
    print("load_ff_opportunity failed:", e)

print("\n=== Jahmyr Gibbs 2025 game log (why isn't he top 3?) ===")
gibbs_source = pd.read_csv("weekly_stats_with_projections.csv", low_memory=False)
gibbs = gibbs_source[(gibbs_source["player_display_name"] == "Jahmyr Gibbs") & (gibbs_source["season"] == 2025)]
print(gibbs[["week", "carries", "rushing_yards", "targets", "receiving_yards",
             "ppr_points", "ewm_points", "season_avg_points", "final_projection"]].to_string(index=False))
