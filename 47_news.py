import pandas as pd, os

SEED = [
    ("Ricky Pearsall",    "OUT_SEASON",   0.00, "PCL surgery, IR 8/1 - out for 2026"),
    ("Jayden Higgins",    "OUT_SEASON",   0.00, "torn ACL - out for 2026"),
    ("Sam LaPorta",       "CAMP_INJURY",  0.85, "hip; missed most of 2025, back surgery"),
    ("Tyler Warren",      "CAMP_INJURY",  0.92, "groin, expected back next week"),
    ("Luther Burden III", "CAMP_INJURY",  0.88, "groin, likely misses preseason"),
]

if not os.path.exists("news_overrides.csv"):
    pd.DataFrame(SEED, columns=["player", "status", "games_mult", "note"]).to_csv(
        "news_overrides.csv", index=False)
    print("created news_overrides.csv - edit this file as news breaks")

ov = pd.read_csv("news_overrides.csv")
print(f"\n{len(ov)} overrides loaded:")
print(ov.to_string(index=False))

b = pd.read_csv("board_v4.csv", low_memory=False)
b = b.merge(ov[["player", "games_mult", "status", "note"]],
            left_on="player_display_name", right_on="player", how="left")
miss = set(ov["player"]) - set(b["player"].dropna())
if miss:
    print("\nWARNING - not matched on board:", miss)

b["games_mult"] = b["games_mult"].fillna(1.0)
b["exp_games"] = b["exp_games"] * b["games_mult"]
b["season_pts"] = b["exp_games"] * b["points"]
b["value"] = b["exp_games"] * b["vorp"] * b["reliability"]
b = b.sort_values("value", ascending=False).reset_index(drop=True)
b["rank"] = b.index + 1
b["pos_rank"] = b.groupby("position")["value"].rank(ascending=False, method="min").astype(int)
b.to_csv("board_v5.csv", index=False)

print("\n=== affected players after override ===")
print(b[b["games_mult"] < 1.0][
    ["rank", "player_display_name", "position", "exp_games", "value", "status"]
].round(2).to_string(index=False))
print("\nSaved board_v5.csv")
