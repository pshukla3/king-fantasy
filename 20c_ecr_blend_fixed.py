import pandas as pd

crosswalk = pd.read_csv("player_id_crosswalk.csv", low_memory=False)
ff_rankings = pd.read_csv("ff_rankings.csv", low_memory=False)

ecr_overall = ff_rankings[ff_rankings["page_type"] == "redraft-overall"].copy()
print(f"Redraft-overall ECR rows: {len(ecr_overall)}")

# Quick sanity check: do these two ID columns actually look alike?
print("\nSample ff_rankings 'id' values:", ecr_overall["id"].dropna().unique()[:5])
print("Sample crosswalk 'fantasypros_id' values:", crosswalk["fantasypros_id"].dropna().unique()[:5])

# Drop rows with a missing key on EITHER side before merging. This matters:
# pandas treats NaN == NaN as a match during a merge (unlike SQL), so if we
# don't drop them first, every row missing an ID on one side joins to every
# row missing an ID on the other side -- a many-to-many blowup. That's
# exactly what happened last run with the D/ST rows.
cw_slim = crosswalk[["gsis_id", "fantasypros_id"]].dropna(subset=["fantasypros_id"])
cw_slim["fantasypros_id"] = cw_slim["fantasypros_id"].astype(int).astype(str)
cw_slim = cw_slim.drop_duplicates(subset="fantasypros_id")

ecr_overall = ecr_overall.dropna(subset=["id"]).copy()
cat > 20c_ecr.py << 'EOF'
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
