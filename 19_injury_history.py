"""
Build an injury-risk score per player from 2023-2025 official injury reports.

Concept: report_status on the injury report (Out/Doubtful/Questionable) is
a public signal of how banged-up a player was that week. We weight these
(Out=3, Doubtful=2, Questionable=1) and sum across the 2025 season to get
one explainable "injury risk" number per player -- higher means more
injury flags last season. This isn't a guarantee of future injury (past
injuries don't perfectly predict future ones), but it's a real, usable
signal for draft risk that ESPN-style rankings almost always mention.

We also print the unique position/page_type values in the FantasyPros
rankings file so the NEXT script can filter it correctly instead of
guessing at its structure.

Run with:  python3 19_injury_history.py
"""

import pandas as pd
import nflreadpy as nfl

print("Pulling injury reports (2023-2025)...")
injuries = nfl.load_injuries(seasons=[2023, 2024, 2025]).to_pandas()
injuries.to_csv("injuries.csv", index=False)
print("Saved injuries.csv -- shape:", injuries.shape)

# Focus on last season only -- that's what's most predictive of near-term risk.
inj_2025 = injuries[injuries["season"] == 2025].copy()

STATUS_WEIGHTS = {"Out": 3, "Doubtful": 2, "Questionable": 1}
inj_2025["status_weight"] = inj_2025["report_status"].map(STATUS_WEIGHTS).fillna(0)

injury_summary = (
    inj_2025.groupby("gsis_id")
    .agg(
        weeks_out=("report_status", lambda s: (s == "Out").sum()),
        weeks_doubtful=("report_status", lambda s: (s == "Doubtful").sum()),
        weeks_questionable=("report_status", lambda s: (s == "Questionable").sum()),
        injury_risk_score=("status_weight", "sum"),
        primary_injuries=("report_primary_injury", lambda s: ", ".join(sorted(set(s.dropna())))),
    )
    .reset_index()
)

print(f"\n{len(injury_summary)} players had at least one 2025 injury report entry.")
print("\n--- Top 20 highest injury-risk players (2025 season) ---")
top_risk = injury_summary.sort_values("injury_risk_score", ascending=False).head(20)
print(top_risk.to_string(index=False))

injury_summary.to_csv("injury_risk_scores.csv", index=False)
print("\nSaved injury_risk_scores.csv")

# --- Peek at FantasyPros rankings structure before we try to merge it later ---
print("\n=== FantasyPros ff_rankings: what's actually in this file? ===")
ff_rankings = nfl.load_ff_rankings().to_pandas()
print("Shape:", ff_rankings.shape)
print("\nUnique page_type values:")
print(ff_rankings["page_type"].value_counts())
print("\nUnique ecr_type values:")
print(ff_rankings["ecr_type"].value_counts())
ff_rankings.to_csv("ff_rankings.csv", index=False)
print("\nSaved ff_rankings.csv")
