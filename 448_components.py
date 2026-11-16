import numpy as np, pandas as pd
import nflreadpy as nfl

SEASONS = [2023, 2024, 2025, 2026]
d = nfl.load_player_stats(seasons=SEASONS).to_pandas()
print("player-weeks: %d" % len(d))
tcol = "team" if "team" in d.columns else "recent_team"

def g(c):
    return d[c] if c in d.columns else 0.0

d["tgt"] = g("targets")
d["rec"] = g("receptions")
d["ryd"] = g("receiving_yards")
d["rtd"] = g("receiving_tds")
d["car"] = g("carries")
d["rush"] = g("rushing_yards")
d["rushtd"] = g("rushing_tds")

tm = (d.groupby(["season", "week", tcol])
      .agg(t_tgt=("tgt", "sum"), t_car=("car", "sum"))
      .reset_index())
d = d.merge(tm, on=["season", "week", tcol], how="left")

d["tgt_share"] = d["tgt"] / d["t_tgt"].replace(0, np.nan)
d["car_share"] = d["car"] / d["t_car"].replace(0, np.nan)
d["catch_rate"] = d["rec"] / d["tgt"].replace(0, np.nan)
d["ypc"] = d["ryd"] / d["rec"].replace(0, np.nan)
d["td_per_tgt"] = d["rtd"] / d["tgt"].replace(0, np.nan)
d["ypcar"] = d["rush"] / d["car"].replace(0, np.nan)
d["td_per_car"] = d["rushtd"] / d["car"].replace(0, np.nan)

COMP = {
    "tgt_share": ("WR", "TE", "RB"),
    "catch_rate": ("WR", "TE", "RB"),
    "ypc": ("WR", "TE", "RB"),
    "td_per_tgt": ("WR", "TE"),
    "car_share": ("RB",),
    "ypcar": ("RB",),
    "td_per_car": ("RB",),
}

print("\n=== how stable is each component season to season? ===")
print("  higher r = more trustworthy, less shrinkage")
print("  %-14s %-5s %6s %7s %8s"
      % ("COMPONENT", "POS", "N", "r", "verdict"))
for comp, poss in COMP.items():
    for pos in poss:
        s = d[(d["position"] == pos) & d[comp].notna()]
        agg = (s.groupby(["player_id", "season"])
               .agg(v=(comp, "mean"), n=(comp, "size"))
               .reset_index())
        agg = agg[agg["n"] >= 6]
        pair = agg.merge(agg, on="player_id",
                         suffixes=("", "_n"))
        pair = pair[pair["season_n"] == pair["season"] + 1]
        if len(pair) < 25:
            continue
        r = np.corrcoef(pair["v"], pair["v_n"])[0, 1]
        verdict = ("trust it" if r >= .55 else
                   ("partial" if r >= .35 else "noise"))
        print("  %-14s %-5s %6d %7.3f  %s"
              % (comp, pos, len(pair), r, verdict))

print("\n=== week-to-week stability within a season ===")
for comp in ("tgt_share", "catch_rate", "ypc",
             "td_per_tgt"):
    s = d[(d["position"].isin(["WR", "TE"]))
          & d[comp].notna()].copy()
    s = s.sort_values(["player_id", "season", "week"])
    s["prev"] = s.groupby(["player_id", "season"])[comp].shift(1)
    s = s.dropna(subset=["prev"])
    if len(s) > 100:
        r = np.corrcoef(s[comp], s["prev"])[0, 1]
        print("  %-14s r = %.3f  (n=%d)" % (comp, r, len(s)))
