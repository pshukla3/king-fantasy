import numpy as np, pandas as pd, re
import nflreadpy as nfl

d = nfl.load_player_stats(seasons=[2023, 2024, 2025, 2026]
                          ).to_pandas()
tcol = "team" if "team" in d.columns else "recent_team"
d["tgt"] = d.get("targets", 0)
tm = (d.groupby(["season", "week", tcol])
      .agg(t=("tgt", "sum")).reset_index())
d = d.merge(tm, on=["season", "week", tcol], how="left")
d = d[(d["position"].isin(["WR", "TE"])) & (d["t"] > 0)]
d["share"] = d["tgt"] / d["t"]
d = d.sort_values(["player_id", "season", "week"])

print("finding the half-life that best predicts next game")
print("  %-10s %10s" % ("HALF-LIFE", "r vs next"))
best = (None, -1)
for hl in (2, 3, 4, 6, 8, 12, 16, 24, 999):
    preds, acts = [], []
    for pid, g in d.groupby("player_id"):
        s = g["share"].values
        if len(s) < 6:
            continue
        for i in range(4, len(s)):
            hist = s[:i]
            ago = np.arange(len(hist))[::-1]
            w = 0.5 ** (ago / hl)
            preds.append(np.sum(w * hist) / np.sum(w))
            acts.append(s[i])
    if len(preds) > 500:
        r = np.corrcoef(preds, acts)[0, 1]
        print("  %-10s %10.4f" % (hl if hl < 999 else "flat", r))
        if r > best[1]:
            best = (hl, r)
print("\n  best half-life: %s games (r=%.4f)"
      % (best[0], best[1]))
