import pandas as pd

df = pd.read_csv("weekly_stats_with_projections.csv", low_memory=False)
k = pd.read_csv("kicker_weekly_with_projections.csv", low_memory=False)
k = k.rename(columns={"k_points": "ppr_points"})
k["position"] = "K"

cols = ["player_id", "position", "season", "ppr_points"]
df = pd.concat([df[cols], k[cols]], ignore_index=True)

g = df.groupby(["player_id", "position", "season"])["ppr_points"].agg(["mean", "count"]).reset_index()
g = g[g["count"] >= 8]

rows = []
for pos in ["QB", "RB", "WR", "TE", "K"]:
    p = g[g["position"] == pos]
    for s in [2023, 2024]:
        a = p[p["season"] == s][["player_id", "mean"]].rename(columns={"mean": "y1"})
        b = p[p["season"] == s + 1][["player_id", "mean"]].rename(columns={"mean": "y2"})
        m = a.merge(b, on="player_id")
        if len(m) > 10:
            rows.append({"pos": pos, "pair": f"{s}->{s+1}", "n": len(m), "r": round(m["y1"].corr(m["y2"]), 3)})

print(pd.DataFrame(rows).to_string(index=False))
