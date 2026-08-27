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
