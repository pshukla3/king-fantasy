import pandas as pd

df = pd.read_csv("weekly_stats_with_projections.csv", low_memory=False)
cw = pd.read_csv("player_id_crosswalk.csv", low_memory=False)[["gsis_id", "birthdate"]].dropna()
cw = cw.drop_duplicates("gsis_id")

g = df.groupby(["player_id", "position", "season"])["ppr_points"].agg(ppg="mean", games="count").reset_index()
g = g[g["games"] >= 8]

g = g.merge(cw, left_on="player_id", right_on="gsis_id", how="inner")
g["birth_year"] = pd.to_datetime(g["birthdate"], errors="coerce").dt.year
g = g.dropna(subset=["birth_year"])
g["age"] = g["season"] - g["birth_year"]
g = g[(g["age"] >= 22) & (g["age"] <= 35)]

for pos in ["RB", "WR", "TE", "QB"]:
    p = g[g["position"] == pos]
    t = p.groupby("age")["ppg"].agg(mean_ppg="mean", n="count").reset_index()
    t = t[t["n"] >= 5]
    print(f"\n--- {pos} points per game by age ---")
    print(t.to_string(index=False))
