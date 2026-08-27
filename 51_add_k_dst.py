import pandas as pd, io

KDST = """Seattle Defense|DST|SEA|83.1
Denver Defense|DST|DEN|88.1
Houston Defense|DST|HOU|97.3
LA Rams Defense|DST|LAR|108.2
Minnesota Defense|DST|MIN|108.6
Philadelphia Defense|DST|PHI|140.0
New England Defense|DST|NE|145.0
Pittsburgh Defense|DST|PIT|146.0
Jacksonville Defense|DST|JAX|152.0
Baltimore Defense|DST|BAL|158.0
LA Chargers Defense|DST|LAC|160.0
Brandon Aubrey|K|DAL|142.0
Cameron Dicker|K|LAC|155.0
Ka'imi Fairbairn|K|HOU|157.0
Cam Little|K|JAX|158.0
Jason Myers|K|SEA|163.0
Tyler Loop|K|BAL|172.0
Eddy Pineiro|K|SF|173.0
Cairo Santos|K|CHI|176.0
Evan McPherson|K|CIN|178.0
Jake Bates|K|DET|179.0"""

kd = pd.read_csv(io.StringIO(KDST), sep="|",
                 names=["player_display_name", "position", "team", "blend"])
kd["points"] = 0.0
kd["exp_games"] = 17.0
kd["value"] = 0.0
kd["adp"] = kd["blend"]
kd["model_rank"] = kd["blend"]
kd["market_rank"] = kd["blend"]
kd["source"] = "market_only"
kd["player_id"] = "KD_" + kd["player_display_name"].str.replace(" ", "_")

b = pd.read_csv("board_v6.csv", low_memory=False)
cols = [c for c in ["player_id", "player_display_name", "position", "team", "points",
                    "exp_games", "value", "adp", "model_rank", "market_rank",
                    "blend", "source"] if c in b.columns or c in kd.columns]
allp = pd.concat([b.reindex(columns=cols), kd.reindex(columns=cols)], ignore_index=True)
allp = allp.sort_values("blend").reset_index(drop=True)
allp["rank"] = allp.index + 1
allp["pos_rank"] = allp.groupby("position")["blend"].rank(method="min").astype(int)
allp.to_csv("board_v7.csv", index=False)

print("positions on board:", allp["position"].value_counts().to_dict())
print("\nfirst DST at overall rank:", int(allp[allp['position'] == 'DST']['rank'].min()))
print("first K   at overall rank:", int(allp[allp['position'] == 'K']['rank'].min()))
print("\nSaved board_v7.csv")
