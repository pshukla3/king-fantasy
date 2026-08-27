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
ecr = ecr[ecr["ecr"] <= 200]

b1 = pd.read_csv("overall_draft_rankings.csv", low_memory=False)[["gsis_id", "overall_rank"]]
b2 = pd.read_csv("draft_board_v2.csv", low_memory=False)[["gsis_id", "overall_rank"]]

common = set(b1["gsis_id"]) & set(b2["gsis_id"]) & set(ecr["gsis_id"])
print("Identical pool size:", len(common))

e = ecr[ecr["gsis_id"].isin(common)].copy()
e["ecr_r"] = e["ecr"].rank()

for nm, b in [("v1", b1), ("v2", b2)]:
    s = b[b["gsis_id"].isin(common)].copy()
    s["our_r"] = s["overall_rank"].rank()
    m = s.merge(e, on="gsis_id")
    rho = m["our_r"].corr(m["ecr_r"])
    mad = (m["our_r"] - m["ecr_r"]).abs().mean()
    print(f"{nm}  n={len(m):3d}  spearman={rho:.3f}  mean|rank diff|={mad:.1f}")
