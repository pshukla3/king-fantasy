import pandas as pd

REPL = {"QB": 17.66, "WR": 11.12, "RB": 11.05, "TE": 9.83}
REL = {"QB": 0.56, "RB": 0.709, "TE": 0.733, "WR": 0.765}

b = pd.read_csv("board_v4.csv", low_memory=False)
print("board_v4 has repl column: %s" % ("repl" in b.columns))

ov = pd.read_csv("news_overrides_v3.csv")
ov = ov.rename(columns={"name": "player"})
ov = ov[["player", "games_mult", "points_mult", "status"]]
ov = ov.drop_duplicates("player")

if "Deebo Samuel" not in set(b["player_display_name"]):
    d = {"player_id": "MANUAL_deebo",
         "player_display_name": "Deebo Samuel",
         "position": "WR", "team": "SF",
         "points": 10.0, "exp_games": 11.8,
         "reliability": REL["WR"], "source": "MANUAL"}
    b = pd.concat([b, pd.DataFrame([d])], ignore_index=True)
    print("added Deebo Samuel (10.0 ppg HAND-SET, not model)")

b = b.merge(ov, left_on="player_display_name",
            right_on="player", how="left")
b["games_mult"] = b["games_mult"].fillna(1.0)
b["points_mult"] = b["points_mult"].fillna(1.0)

old = dict(zip(b["player_display_name"], b["vorp"]))

b["repl"] = b["position"].map(REPL)
b["points"] = b["points"] * b["points_mult"]
b["exp_games"] = b["exp_games"] * b["games_mult"]
b["vorp"] = b["points"] - b["repl"]
b["season_pts"] = b["exp_games"] * b["points"]
b["value"] = b["exp_games"] * b["vorp"] * b["reliability"]
b = b.sort_values("value", ascending=False).reset_index(drop=True)
b["rank"] = b.index + 1
b["pos_rank"] = b.groupby("position")["value"].rank(
    ascending=False, method="min").astype(int)
b.to_csv("board_v9.csv", index=False)

miss = sorted(set(b[b["repl"].isna()]["position"].dropna()))
print("positions with no replacement level: %s" % miss)

CHK = ["George Kittle", "Puka Nacua", "Breece Hall",
       "Tucker Kraft", "Sam LaPorta", "Jordyn Tyson",
       "Deebo Samuel", "Jahmyr Gibbs"]
print("\n=== VORP RECOMPUTE CHECK ===")
print("  player                  old    new   rank")
print("  " + "-" * 44)
for nm in CHK:
    m = b["player_display_name"] == nm
    if not m.any():
        print("  %-22s NOT ON BOARD" % nm)
        continue
    r = b[m].iloc[0]
    print("  %-22s %+6.2f %+6.2f %6d"
          % (nm, old.get(nm, float("nan")), r["vorp"], r["rank"]))

print("\n=== BOARD v9: TOP 30 ===")
c = ["rank", "player_display_name", "position", "pos_rank",
     "team", "points", "exp_games", "vorp", "value"]
print(b.head(30)[c].round(2).to_string(index=False))
print("\nSaved board_v9.csv")
