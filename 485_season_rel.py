import json
import numpy as np
import nflreadpy as nfl

YR = [2021, 2022, 2023, 2024, 2025]
d = nfl.load_player_stats(YR).to_pandas()
need = ["targets", "receptions", "receiving_yards",
        "receiving_air_yards", "receiving_yards_after_catch",
        "receiving_tds"]
for c in need:
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)
d = d[d["position"].isin(["WR", "TE"])]

a = d.groupby(["player_id", "season"], as_index=False).agg(
    t=("targets", "sum"), r=("receptions", "sum"),
    y=("receiving_yards", "sum"),
    ay=("receiving_air_yards", "sum"),
    yac=("receiving_yards_after_catch", "sum"),
    td=("receiving_tds", "sum"), g=("targets", "size"))
a = a[(a["t"] >= 40) & (a["g"] >= 8)]
a["adot"] = a["ay"] / a["t"]
a["yacr"] = a["yac"] / a["r"].clip(lower=1)
a["crate"] = a["r"] / a["t"]
a["ypr"] = a["y"] / a["r"].clip(lower=1)
a["tdt"] = a["td"] / a["t"]

def yoy(col):
    xs, ys = [], []
    for pid, g in a.groupby("player_id"):
        g = g.sort_values("season")
        s = g["season"].values
        v = g[col].values
        for i in range(len(v) - 1):
            if s[i + 1] == s[i] + 1:
                xs.append(v[i]); ys.append(v[i + 1])
    if len(xs) < 40:
        return 0.0, len(xs)
    return float(np.corrcoef(xs, ys)[0, 1]), len(xs)

print("=== SEASON-TO-SEASON RELIABILITY (WR/TE) ===")
print("%-22s %8s %8s   %s" % ("COMPONENT", "r", "N", "vs WEEKLY"))
wk = {"adot": .333, "yacr": .115, "crate": .104,
      "ypr": .085, "tdt": .010}
OUT = {}
for lbl, c in (("aDOT", "adot"), ("YAC per rec", "yacr"),
               ("catch rate", "crate"),
               ("yards per rec", "ypr"),
               ("TD per target", "tdt")):
    r, n = yoy(c)
    OUT[c] = round(max(0.0, r), 4)
    print("%-22s %8.3f %8d   %.3f  (%.1fx)"
          % (lbl, r, n, wk[c],
             r / wk[c] if wk[c] else 0))
json.dump(OUT, open("seasonrel.json", "w"), indent=1)
print("\nwrote seasonrel.json")
