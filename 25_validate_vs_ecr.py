import pandas as pd

cw = pd.read_csv("player_id_crosswalk.csv", low_memory=False)
ff = pd.read_csv("ff_rankings.csv", low_memory=False)

ecr = ff[ff["page_type"] == "redraft-overall"].dropna(subset=["id"]).copy()
ecr["id"] = ecr["id"].astype(int).astype(str)

cw = cw[["gsis_id", "fantasypros_id"]].dropna()
cw["fantasypros_id"] = cw["fantasypros_id"].astype(int).astype(str)
cw = cw.drop_duplicates("fantasypros_id")

ecr = ecr.merge(cw, left_on="id", right_on="fantasypros_id", how="left")
ecr = ecr[["gsis_id", "ecr"]].dropna(subset=["gsis_id"])

for f in ["overall_draft_rankings.csv", "draft_board_v2.csv"]:
    b = pd.read_csv(f, low_memory=False)
    m = b.merge(ecr, on="gsis_id", how="inner")
    m = m[m["overall_rank"] <= 200]
    rho = m["overall_rank"].rank().corr(m["ecr"].rank())
    mad = (m["overall_rank"] - m["ecr"]).abs().mean()
    print(f"{f:32s} n={len(m):4d}  spearman={rho:.3f}  mean|rank diff|={mad:.1f}")
