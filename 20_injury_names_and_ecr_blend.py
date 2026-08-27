"""
Two things in this script:

1. Fix injury_risk_scores.csv to show player names instead of raw gsis_id
   codes (just a readability fix -- the scores themselves were already
   correct).

2. Blend FantasyPros' expert consensus rankings (ECR) against our own
   model. FantasyPros bundles ~30 different ranking types into one file
   (dynasty vs redraft, overall vs per-position, best-ball vs standard,
   IDP leagues for defensive players) -- we only want page_type ==
   "redraft-overall" since that matches what our own overall_draft_rankings.csv
   is trying to be: a single overall board for a standard redraft league.

   Concept: this isn't about replacing our model with the "smarter"
   experts -- it's a sanity check. Where our model and the expert
   consensus roughly agree, that's reassuring. Where they disagree a lot,
   that's worth understanding: maybe our model is catching something
   real (like a returning-from-injury discount experts haven't priced in
   yet), or maybe it's exposing a blind spot (like a lack of "coach
   speak"/beat-reporter buzz our model has no way to see). Either way,
   the disagreement itself is useful information for you as a drafter.

Run with:  python3 20_injury_names_and_ecr_blend.py
"""

import pandas as pd

crosswalk = pd.read_csv("player_id_crosswalk.csv", low_memory=False)
names = crosswalk[["gsis_id", "name"]].dropna(subset=["gsis_id"]).drop_duplicates(subset="gsis_id")

# --- 1. Fix injury summary names ---
injury_summary = pd.read_csv("injury_risk_scores.csv")
injury_summary = injury_summary.merge(names, on="gsis_id", how="left")

print("--- Top 20 highest injury-risk players (2025 season) ---")
top_risk = injury_summary.sort_values("injury_risk_score", ascending=False).head(20)
print(top_risk[["name", "weeks_out", "weeks_doubtful", "weeks_questionable",
                 "injury_risk_score", "primary_injuries"]].to_string(index=False))

injury_summary.to_csv("injury_risk_scores.csv", index=False)
print("\nRe-saved injury_risk_scores.csv with names")

# --- 2. Blend FantasyPros ECR against our model ---
ff_rankings = pd.read_csv("ff_rankings.csv", low_memory=False)
ecr_overall = ff_rankings[ff_rankings["page_type"] == "redraft-overall"].copy()
print(f"\nredraft-overall ECR rows: {len(ecr_overall)}")
print(ecr_overall[["player", "pos", "team", "ecr", "mergename"]].head(10).to_string(index=False))

# nflreadpy ships a normalized "merge_name" / "mergename" field specifically
# so different sources' name spellings can be matched -- that's what we use
# here instead of matching on raw player-name strings, which would break on
# things like "Jr." or middle initials.
cw_slim = crosswalk[["gsis_id", "merge_name"]].dropna(subset=["merge_name"]).drop_duplicates(subset="merge_name")
ecr_overall = ecr_overall.merge(cw_slim, left_on="mergename", right_on="merge_name", how="left")
print(f"\nECR rows matched to a gsis_id: {ecr_overall['gsis_id'].notna().sum()} / {len(ecr_overall)}")

draft_board = pd.read_csv("overall_draft_rankings.csv", low_memory=False)
compare = draft_board.merge(ecr_overall[["gsis_id", "ecr"]], on="gsis_id", how="left")

# Positive rank_diff = our model ranks them HIGHER than the experts do (we're more bullish)
# Negative rank_diff = experts rank them HIGHER than we do (we're more bearish)
compare["rank_diff"] = compare["ecr"] - compare["overall_rank"]

print("\n--- Our top 30 vs expert ECR, side by side ---")
print(compare[["overall_rank", "name", "position", "team", "ecr", "rank_diff"]].head(30).to_string(index=False))

matched =
cat > 20_injury_names_and_ecr_blend.py << 'EOF'
"""
Two things in this script:

1. Fix injury_risk_scores.csv to show player names instead of raw gsis_id
   codes (just a readability fix -- the scores themselves were already
   correct).

2. Blend FantasyPros' expert consensus rankings (ECR) against our own
   model. FantasyPros bundles ~30 different ranking types into one file
   (dynasty vs redraft, overall vs per-position, best-ball vs standard,
   IDP leagues for defensive players) -- we only want page_type ==
   "redraft-overall" since that matches what our own overall_draft_rankings.csv
   is trying to be: a single overall board for a standard redraft league.

   Concept: this isn't about replacing our model with the "smarter"
   experts -- it's a sanity check. Where our model and the expert
   consensus roughly agree, that's reassuring. Where they disagree a lot,
   that's worth understanding: maybe our model is catching something
   real (like a returning-from-injury discount experts haven't priced in
   yet), or maybe it's exposing a blind spot (like a lack of "coach
   speak"/beat-reporter buzz our model has no way to see). Either way,
   the disagreement itself is useful information for you as a drafter.

Run with:  python3 20_injury_names_and_ecr_blend.py
"""

import pandas as pd

crosswalk = pd.read_csv("player_id_crosswalk.csv", low_memory=False)
names = crosswalk[["gsis_id", "name"]].dropna(subset=["gsis_id"]).drop_duplicates(subset="gsis_id")

# --- 1. Fix injury summary names ---
injury_summary = pd.read_csv("injury_risk_scores.csv")
injury_summary = injury_summary.merge(names, on="gsis_id", how="left")

print("--- Top 20 highest injury-risk players (2025 season) ---")
top_risk = injury_summary.sort_values("injury_risk_score", ascending=False).head(20)
print(top_risk[["name", "weeks_out", "weeks_doubtful", "weeks_questionable",
                 "injury_risk_score", "primary_injuries"]].to_string(index=False))

injury_summary.to_csv("injury_risk_scores.csv", index=False)
print("\nRe-saved injury_risk_scores.csv with names")

# --- 2. Blend FantasyPros ECR against our model ---
ff_rankings = pd.read_csv("ff_rankings.csv", low_memory=False)
ecr_overall = ff_rankings[ff_rankings["page_type"] == "redraft-overall"].copy()
print(f"\nredraft-overall ECR rows: {len(ecr_overall)}")
print(ecr_overall[["player", "pos", "team", "ecr", "mergename"]].head(10).to_string(index=False))

# nflreadpy ships a normalized "merge_name" / "mergename" field specifically
# so different sources' name spellings can be matched -- that's what we use
# here instead of matching on raw player-name strings, which would break on
# things like "Jr." or middle initials.
cw_slim = crosswalk[["gsis_id", "merge_name"]].dropna(subset=["merge_name"]).drop_duplicates(subset="merge_name")
ecr_overall = ecr_overall.merge(cw_slim, left_on="mergename", right_on="merge_name", how="left")
print(f"\nECR rows matched to a gsis_id: {ecr_overall['gsis_id'].notna().sum()} / {len(ecr_overall)}")

draft_board = pd.read_csv("overall_draft_rankings.csv", low_memory=False)
compare = draft_board.merge(ecr_overall[["gsis_id", "ecr"]], on="gsis_id", how="left")

# Positive rank_diff = our model ranks them HIGHER than the experts do (we're more bullish)
# Negative rank_diff = experts rank them HIGHER than we do (we're more bearish)
compare["rank_diff"] = compare["ecr"] - compare["overall_rank"]

print("\n--- Our top 30 vs expert ECR, side by side ---")
print(compare[["overall_rank", "name", "position", "team", "ecr", "rank_diff"]].head(30).to_string(index=False))

matched =
cat > 20a_injury_names.py << 'EOF'
import pandas as pd

crosswalk = pd.read_csv("player_id_crosswalk.csv", low_memory=False)
names = crosswalk[["gsis_id", "name"]].dropna(subset=["gsis_id"]).drop_duplicates(subset="gsis_id")

injury_summary = pd.read_csv("injury_risk_scores.csv")
injury_summary = injury_summary.merge(names, on="gsis_id", how="left")

print("--- Top 20 highest injury-risk players (2025 season) ---")
top_risk = injury_summary.sort_values("injury_risk_score", ascending=False).head(20)
print(top_risk[["name", "weeks_out", "weeks_doubtful", "weeks_questionable",
                 "injury_risk_score", "primary_injuries"]].to_string(index=False))

injury_summary.to_csv("injury_risk_scores.csv", index=False)
print("\nRe-saved injury_risk_scores.csv with names")
