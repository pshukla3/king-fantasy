import pandas as pd

WEIGHTS = {2025: 3, 2024: 2, 2023: 1}

df = pd.read_csv("weekly_stats_with_projections.csv", low_memory=False)
df = df.sort_values(["player_id", "season", "week"])

g = df.groupby(["player_id", "season"])["ppr_points"].agg(ppg="mean", games="count").reset_index()
g = g[g["games"] >= 4]
g["w"] = g["season"].map(WEIGHTS).fillna(0) * g["games"]
g = g[g["w"] > 0]

g["x"] = g["ppg"] * g["w"]
agg = g.groupby("player_id").agg(num=("x", "sum"), den=("w", "sum")).reset_index()
agg["final_projection"] = agg["num"] / agg["den"]

info = df.groupby("player_id").tail(1)[["player_id", "player_display_name", "position", "team"]]
out = agg.merge(info, on="player_id")[["player_id", "player_display_name", "position", "team", "final_projection"]]

print("--- Top 15 RBs (multi-season weighted) ---")
print(out[out["position"] == "RB"].sort_values("final_projection", ascending=False).head(15).to_string(index=False))

old = pd.read_csv("latest_player_projections.csv", low_memory=False)[["player_id", "final_projection"]]
old = old.rename(columns={"final_projection": "old_proj"})
chk = out.merge(old, on="player_id")
names = ["Jahmyr Gibbs", "Tucker Kraft", "Chase Brown", "Bijan Robinson", "Cam Skattebo", "Derrick Henry"]
print("\n--- Old vs new on the players we flagged ---")
print(chk[chk["player_display_name"].isin(names)][
    ["player_display_name", "position", "old_proj", "final_projection"]].to_string(index=False))

out.to_csv("latest_player_projections_v2.csv", index=False)
print("\nSaved latest_player_projections_v2.csv")
