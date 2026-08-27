import pandas as pd

cw = pd.read_csv("player_id_crosswalk.csv", low_memory=False)
ff = pd.read_csv("ff_rankings.csv", low_memory=False)
ecr = ff[ff["page_type"] == "redraft-overall"].dropna(subset=["id"]).copy()
ecr["id"] = ecr["id"].astype(int).astype(str)

cw = cw[["gsis_id", "fantasypros_id"]].dropna(subset=["fantasypros_id", "gsis_id"])
cw["fantasypros_id"] = cw["fantasypros_id"].astype(int).astype(str)
cw = cw.drop_duplicates(subset="fantasypros_id")

ecr = ecr.merge(cw, left_on="id", right_on="fantasypros_id", how="left")
print(f"Matched: {ecr['gsis_id'].notna().sum()} / {len(ecr)}")

db = pd.read_csv("overall_draft_rankings.csv", low_memory=False)
c = db.merge(ecr[["gsis_id", "ecr"]].dropna(subset=["gsis_id"]), on="gsis_id", how="left")
c["rank_diff"] = c["ecr"] - c["overall_rank"]
cols = ["overall_rank", "name", "position", "team", "ecr", "rank_diff"]

print("\n--- Top 30 vs expert ECR ---")
print(c[cols].head(30).to_string(index=False))

m = c.dropna(subset=["ecr"])
print("\n--- We're most BULLISH vs experts ---")
print(m.sort_values("rank_diff", ascending=False).head(15)[cols].to_string(index=False))
print("\n--- We're most BEARISH vs experts ---")
print(m.sort_values("rank_diff").head(15)[cols].to_string(index=False))

c.to_csv("draft_board_vs_expert_ecr.csv", index=False)
print("\nSaved draft_board_vs_expert_ecr.csv")
