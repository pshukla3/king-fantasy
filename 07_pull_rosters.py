"""
Step 4: Pull current 2026 team rosters.

One caveat worth knowing now: it's July, so this is the OFFSEASON roster --
every player currently signed, including many who'll get cut before final
53-man rosters are set in late August/September. That's fine for now (we
want to see the whole pipeline work), but don't be surprised if this list
shrinks and shifts some before the season actually starts. We'll just
re-run this same script closer to kickoff to get the final version -- no
code changes needed, another payoff of building this as a pipeline.

Run with:  python3 07_pull_rosters.py
"""

import nflreadpy as nfl

rosters_polars = nfl.load_rosters(seasons=[2026])
rosters = rosters_polars.to_pandas()

print("Shape:", rosters.shape)
print("Columns:", list(rosters.columns))
print(rosters.head(10))
print("\nTeams found:", sorted(rosters["team"].dropna().unique()))
print("\nRows per team (sample):")
print(rosters["team"].value_counts().head(10))

rosters.to_csv("rosters_2026.csv", index=False)
print("\nSaved to rosters_2026.csv")
