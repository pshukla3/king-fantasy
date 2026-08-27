import pandas as pd, os

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
H = H[H["position"].isin(["QB", "RB", "WR", "TE"])]

g = H.groupby(["player_id", "position", "season"]).size().reset_index(name="games")
g["sched"] = g["season"].apply(lambda s: 17 if s >= 2021 else 16)
g["avail"] = (g["games"] / g["sched"]).clip(upper=1.0)

print("=== Games played per season, by position ===")
print(g.groupby("position")["games"].agg(["mean", "median", "count"]).round(2).to_string())

nxt = g[["player_id", "season", "avail"]].copy()
nxt["season"] = nxt["season"] - 1
nxt = nxt.rename(columns={"avail": "avail_next"})
d = g.merge(nxt, on=["player_id", "season"], how="inner")
d = d[d["games"] >= 4]

print("\n=== Is durability repeatable? (availability year N vs N+1) ===")
rows = []
for p, x in d.groupby("position"):
    if len(x) < 50:
        continue
    r = x["avail"].corr(x["avail_next"])
    rows.append({"pos": p, "n": len(x), "persistence_r": r,
                 "mean_avail": x["avail_next"].mean()})
per = pd.DataFrame(rows)
print(per.round(3).to_string(index=False))

R = dict(zip(per["pos"], per["persistence_r"]))
M = dict(zip(per["pos"], per["mean_avail"]))

recent = g[g["season"] >= 2023].groupby(["player_id", "position"]).agg(
    avail_hist=("avail", "mean"), seasons=("avail", "size")).reset_index()
recent["r"] = recent["position"].map(R).fillna(0.2)
recent["pos_mean"] = recent["position"].map(M).fillna(0.75)
w = recent["seasons"] * recent["r"] / (1 + (recent["seasons"] - 1) * recent["r"])
recent["exp_avail"] = recent["pos_mean"] + w * (recent["avail_hist"] - recent["pos_mean"])
recent["exp_games"] = (recent["exp_avail"] * 17).clip(upper=17)
recent[["player_id", "seasons", "avail_hist", "exp_avail", "exp_games"]].to_csv(
    "durability_2026.csv", index=False)

nm = H.sort_values(["season", "week"]).groupby("player_id").tail(1)[
    ["player_id", "player_display_name"]]
board = pd.read_csv("full_rankings_2026.csv", low_memory=False)
top = board[board["source"] == "model"].head(120)[["player_id", "player_display_name", "position", "overall"]]
top = top.merge(recent[["player_id", "avail_hist", "seasons", "exp_games"]], on="player_id", how="left")

print("\n=== Most injury-discounted among our top 120 ===")
print(top.nsmallest(15, "exp_games")[
    ["overall", "player_display_name", "position", "seasons", "avail_hist", "exp_games"]
].round(2).to_string(index=False))
print("\n=== Most durable among our top 120 ===")
print(top.nlargest(12, "exp_games")[
    ["overall", "player_display_name", "position", "seasons", "avail_hist", "exp_games"]
].round(2).to_string(index=False))
print("\nSaved durability_2026.csv")
