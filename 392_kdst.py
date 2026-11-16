import json
import numpy as np
import pandas as pd

W = pd.read_parquet("weekly_all.parquet")
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)

def tbl(y, pos):
    d = W[(W["season"] == y) & (W["position"] == pos)]
    a = d.groupby("player_display_name")["fp"]\
        .agg(["mean", "count"]).reset_index()
    return a[a["count"] >= 8].sort_values(
        "mean", ascending=False)

print("=== EX-ANTE VALUE OF DRAFTING THE TOP KICKER ===")
print("(rank by last season, score this season, "
      "10-team replacement = K11)")
vals, reps = [], []
for s in range(2017, 2026):
    prev, cur = tbl(s - 1, "K"), tbl(s, "K")
    if len(prev) < 12 or len(cur) < 12:
        continue
    cm = dict(zip(cur["player_display_name"], cur["mean"]))
    v = list(cur["mean"].values)
    rep = v[10]
    reps.append(rep)
    got = []
    for nm in list(prev["player_display_name"])[:3]:
        x = cm.get(nm)
        got.append((x if x is not None else rep) - rep)
    vals.append(float(np.mean(got)))
    print("  %d  top-3 prior kickers returned %+.2f "
          "over replacement (%.2f)"
          % (s, np.mean(got), rep))
kv = float(np.mean(vals)) if vals else 0.0
print("\nkicker: %+.2f ppg over replacement (n=%d seasons)"
      % (kv, len(vals)))

print("\n=== SEASON-TO-SEASON PERSISTENCE ===")
for pos in ("K",):
    xs, ys = [], []
    for s in range(2017, 2026):
        a, b = tbl(s - 1, pos), tbl(s, pos)
        m = dict(zip(b["player_display_name"], b["mean"]))
        for _, r in a.iterrows():
            v = m.get(r["player_display_name"])
            if v is not None:
                xs.append(r["mean"])
                ys.append(v)
    if len(xs) > 30:
        print("  %-4s r = %.3f  (n=%d)"
              % (pos, np.corrcoef(xs, ys)[0, 1], len(xs)))

RB = 7.24  # measured earlier: ex-ante value of a top RB
kmult = max(0.0, min(1.0, kv / RB))
print("\nkicker multiplier = %.2f / %.2f = %.3f"
      % (kv, RB, kmult))
print("defense: week-1 correlation 0.023, "
      "season persistence 0.295 -> multiplier 0.05")

M = json.load(open("pos_mult.json"))
M["K"] = round(max(0.03, kmult), 3)
M["DST"] = 0.05
json.dump(M, open("pos_mult.json", "w"), indent=1)
print("\nupdated pos_mult.json:")
print(json.dumps(M, indent=1))
