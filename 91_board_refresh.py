import pandas as pd

b = pd.read_csv("board_v4.csv", low_memory=False)
ov = pd.read_csv("news_overrides_v3.csv")
print("overrides loaded: %d" % len(ov))

ov = ov.rename(columns={"name": "player"})
keep = ["player", "games_mult", "points_mult", "status", "desc"]
ov = ov[[c for c in keep if c in ov.columns]]
ov = ov.drop_duplicates("player")

b = b.merge(ov, left_on="player_display_name",
            right_on="player", how="left")
b["games_mult"] = b["games_mult"].fillna(1.0)
b["points_mult"] = b["points_mult"].fillna(1.0)

FIX = {"Deebo Samuel": 10.0}
for nm, v in FIX.items():
    m = b["player_display_name"] == nm
    if m.any():
        b.loc[m, "points"] = v
        print("  patched %s -> %.1f ppg" % (nm, v))
    else:
        print("  STILL MISSING FROM BOARD: %s" % nm)

b["points"] = b["points"] * b["points_mult"]
b["exp_games"] = b["exp_games"] * b["games_mult"]
b["season_pts"] = b["exp_games"] * b["points"]
b["vorp"] = b["points"] - b["repl"] if "repl" in b.columns \
    else b["vorp"]
b["value"] = b["exp_games"] * b["vorp"] * b["reliability"]
b = b.sort_values("value", ascending=False).reset_index(drop=True)
b["rank"] = b.index + 1
b["pos_rank"] = b.groupby("position")["value"].rank(
    ascending=False, method="min").astype(int)
b.to_csv("board_v8.csv", index=False)

hit = b[(b["games_mult"] < 1.0) | (b["points_mult"] < 1.0)]
print("\nplayers moved by injury: %d" % len(hit))
cols = ["rank", "player_display_name", "position", "team",
        "points", "exp_games", "status"]
print(hit.head(30)[cols].round(2).to_string(index=False))
print("\nSaved board_v8.csv")
