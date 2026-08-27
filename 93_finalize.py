import pandas as pd

b = pd.read_csv("board_v9.csv", low_memory=False)
v7 = pd.read_csv("board_v7.csv", low_memory=False)

adp = v7[["player_display_name", "adp"]].dropna()
adp = adp.drop_duplicates("player_display_name")
b = b.merge(adp, on="player_display_name", how="left")
print("board_v9 rows: %d | matched to ADP: %d"
      % (len(b), int(b["adp"].notna().sum())))

b["model_rank"] = b["rank"]
b["market_rank"] = b["adp"].rank(method="min")
b["blend"] = b[["model_rank", "market_rank"]].mean(axis=1)

kd = v7[v7["position"].isin(["K", "DST"])].copy()
print("K/DST rows carried over: %d" % len(kd))

COLS = ["player_id", "player_display_name", "position", "team",
        "points", "exp_games", "vorp", "value", "adp",
        "model_rank", "market_rank", "blend", "status",
        "games_mult", "points_mult", "source"]
A = pd.concat([b.reindex(columns=COLS),
               kd.reindex(columns=COLS)], ignore_index=True)
A = A.sort_values("blend").reset_index(drop=True)
A["rank"] = A.index + 1
A["pos_rank"] = A.groupby("position")["blend"].rank(
    method="min").astype(int)
A.to_csv("board_final.csv", index=False)

print("\npositions: %s" % A["position"].value_counts().to_dict())
print("first DST rank %d | first K rank %d"
      % (int(A[A["position"] == "DST"]["rank"].min()),
         int(A[A["position"] == "K"]["rank"].min())))

gm = A["games_mult"].fillna(1.0)
pm = A["points_mult"].fillna(1.0)
inj = A[gm.lt(1.0) | pm.lt(1.0)]
print("injured players on final board: %d" % len(inj))

C = ["rank", "player_display_name", "position", "pos_rank",
     "team", "points", "exp_games", "adp", "blend", "status"]
print("\n=== BOARD FINAL: TOP 40 ===")
print(A.head(40)[C].round(1).to_string(index=False))

print("\n=== WHERE THE INJURED PLAYERS LANDED ===")
print(inj.head(25)[C].round(1).to_string(index=False))
print("\nSaved board_final.csv")
