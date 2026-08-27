import pandas as pd

crosswalk = pd.read_csv("player_id_crosswalk.csv", low_memory=False)
ff_rankings = pd.read_csv("ff_rankings.csv", low_memory=False)

ecr_overall = ff_rankings[ff_rankings["page_type"] == "redraft-overall"].copy()
print(f"Redraft-overall ECR rows: {len(ecr_overall)}")

cw_slim = crosswalk[["gsis_id", "merge_name"]].dropna(subset=["merge_name"]).drop_duplicates(subset="merge_name")
ecr_overall = ecr_overall.merge(cw_slim, left_on="mergename", right_on="merge_name", how="left")
print(f"ECR rows matched to a gsis_id: {ecr_overall['gsis_id'].notna().sum()} / {len(ecr_overall)}")

draft_board = pd.read_csv("overall_draft_rankings.csv", low_memory=False)
compare = draft_board.merge(ecr_overall[["gsis_id", "ecr"]], on="gsis_id", how="left")

compare["rank_diff"] = compare["ecr"] - compare["overall_rank"]

print("\n--- Our top 30 vs expert ECR, side by side ---")
print(compare[["overall_rank", "name", "position", "team", "ecr", "rank_diff"]].head(30).to_string(index=False))

matched = compare.dropna(subset=["ecr"])

print("\n--- Players we're MOST bullish on vs experts (we rank them much higher) ---")
bullish = matched.sort_values("rank_diff", ascending=False).head(15)
print(bullish[["overall_rank", "name", "position", "team", "ecr", "rank_diff"]].to_string(index=False))

print("\n--- Players we're MOST bearish on vs experts (we rank them much lower) ---")
bearish = matched.sort_values("rank_diff", ascending=True).head(15)
print(bearish[["overall_rank", "name", "position", "team", "ecr", "rank_diff"]].to_string(index=False))

compare.to_csv("draft_board_vs_expert_ecr.csv", index=False)
print("\nSaved draft_board_vs_expert_ecr.csv")
