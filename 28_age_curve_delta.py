import nflreadpy as nfl
import pandas as pd

SEASONS = list(range(2014, 2026))
print("Pulling", len(SEASONS), "seasons of weekly stats...")
s = nfl.load_player_stats(seasons=SEASONS).to_pandas()
s = s[s["season_type"] == "REG"]
s.to_csv("weekly_stats_long_history.csv", index=False)
print("Rows:", len(s))

cw = pd.read_csv("player_id_crosswalk.csv", low_memory=False)[["gsis_id", "birthdate"]]
cw = cw.dropna().drop_duplicates("gsis_id")

g = s.groupby(["player_id", "position", "season"])["fantasy_points_ppr"].agg(
    ppg="mean", games="count").reset_index()
g = g[g["games"] >= 8]

g = g.merge(cw, left_on="player_id", right_on="gsis_id", how="inner")
g["age"] = g["season"] - pd.to_datetime(g["birthdate"], errors="coerce").dt.year
g = g.dropna(subset=["age"])

nxt = g[["player_id", "season", "ppg"]].copy()
nxt["season"] = nxt["season"] - 1
nxt = nxt.rename(columns={"ppg": "ppg_next"})

d = g.merge(nxt, on=["player_id", "season"], how="inner")
d["delta"] = d["ppg_next"] - d["ppg"]

for pos in ["RB", "WR", "TE", "QB"]:
    p = d[(d["position"] == pos) & (d["age"] >= 22) & (d["age"] <= 34)]
    t = p.groupby("age")["delta"].agg(mean_delta="mean", n="count").reset_index()
    t = t[t["n"] >= 8]
    print(f"\n--- {pos}: PPG change from age N to N+1 ---")
    print(t.round(2).to_string(index=False))

d.to_csv("age_deltas.csv", index=False)
print("\nSaved age_deltas.csv and weekly_stats_long_history.csv")
