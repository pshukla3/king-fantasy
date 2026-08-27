import pandas as pd

o = pd.read_csv("ff_opportunity.csv", low_memory=False)
print("touchdown cols:", [c for c in o.columns if "touchdown" in c])
print("has week:", "week" in o.columns, "| has season:", "season" in o.columns)

agg = {"td": ("total_touchdown", "sum"), "td_exp": ("total_touchdown_exp", "sum")}
if "week" in o.columns:
    agg["g"] = ("week", "nunique")
g = o.groupby(["player_id", "season"]).agg(**agg).reset_index()
if "g" not in g.columns:
    g["g"] = 17
g = g[g["g"] >= 8].copy()
g["td_rate"] = g["td"] / g["g"]
g["exp_rate"] = g["td_exp"] / g["g"]

nxt = g[["player_id", "season", "td_rate"]].copy()
nxt["season"] = nxt["season"] - 1
nxt = nxt.rename(columns={"td_rate": "td_rate_next"})
d = g.merge(nxt, on=["player_id", "season"], how="inner")

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
pos = H.sort_values(["season", "week"]).groupby("player_id").tail(1)[["player_id", "position"]]
d = d.merge(pos, on="player_id", how="left")
print(f"\nconsecutive-season pairs: {len(d)}")

print("\n=== Does expected TD rate predict next year better than actual TD rate? ===")
rows = []
for p, x in d.groupby("position"):
    if p not in ("RB", "WR", "TE") or len(x) < 40:
        continue
    ca = x["td_rate"].corr(x["td_rate_next"])
    ce = x["exp_rate"].corr(x["td_rate_next"])
    best_w, best_r = 0.0, -1.0
    for i in range(21):
        w = i / 20
        b = w * x["exp_rate"] + (1 - w) * x["td_rate"]
        r = b.corr(x["td_rate_next"])
        if r > best_r:
            best_r, best_w = r, w
    rows.append({"pos": p, "n": len(x), "actual_r": ca, "expected_r": ce,
                 "best_w_exp": best_w, "blend_r": best_r})
print(pd.DataFrame(rows).round(3).to_string(index=False))
print("\nw_exp = how much weight to put on EXPECTED tds vs what actually happened.")
