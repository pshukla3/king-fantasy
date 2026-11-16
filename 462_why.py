import json, re, sys
import numpy as np
import nflreadpy as nfl

WHO = sys.argv[1:] or ["Bhayshul Tuten"]
def norm(s):
    s = str(s or "").lower(); s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

REL = json.load(open("reliability.json"))
PRI = json.load(open("priors.json"))
P = json.load(open("site/_projweek.json"))
d = nfl.load_player_stats(seasons=[2024, 2025, 2026]).to_pandas()
tc = "team" if "team" in d.columns else "recent_team"
for a, b in (("tgt", "targets"), ("rec", "receptions"),
             ("ryd", "receiving_yards"), ("rtd", "receiving_tds"),
             ("car", "carries"), ("rush", "rushing_yards"),
             ("rutd", "rushing_tds")):
    d[a] = d.get(b, 0)
tv = (d.groupby(["season", "week", tc])
      .agg(t_tgt=("tgt", "sum"), t_car=("car", "sum"))
      .reset_index())
d = d.merge(tv, on=["season", "week", tc], how="left")

for who in WHO:
    k = norm(who)
    g = d[d["player_display_name"].apply(norm) == k]
    g = g.sort_values(["season", "week"])
    if not len(g):
        print("%s: no rows" % who); continue
    v = P.get(k)
    print("=" * 62)
    print("%s  (%s)  projected wk3: %s"
          % (who, g.iloc[-1][tc],
             next((x["m"] for x in v["wk"] if x["w"] == 3), "-")
             if v else "NOT IN MODEL"))
    print("=" * 62)
    print("\n%-6s %-4s %5s %5s %6s %5s %5s %5s %6s"
          % ("SEASON", "WK", "CAR", "TCAR", "SHARE", "YDS",
             "TD", "TGT", "PTS"))
    for _, r in g.tail(8).iterrows():
        pts = (r["rush"] * .1 + r["rutd"] * 6 + r["rec"]
               + r["ryd"] * .1 + r["rtd"] * 6)
        print("%-6d %-4d %5.0f %5.0f %6.1f%% %5.0f %5.0f "
              "%5.0f %6.1f"
              % (r["season"], r["week"], r["car"],
                 r["t_car"], 100 * r["car"] /
                 max(r["t_car"], 1), r["rush"], r["rutd"],
                 r["tgt"], pts))

    n = len(g)
    w = 0.5 ** (np.arange(n)[::-1] / 3.0)
    ne = (w.sum() ** 2) / (w ** 2).sum()
    def wa(num, den=None):
        if den is None:
            return float(np.sum(w * num) / w.sum())
        dd = float(np.sum(w * den))
        return float(np.sum(w * num) / dd) if dd else 0.0
    cs = wa(np.nan_to_num(g["car"].values /
                          np.maximum(g["t_car"].values, 1)))
    yc = wa(g["rush"].values, g["car"].values)
    tdc = wa(g["rutd"].values, g["car"].values)
    ts = wa(np.nan_to_num(g["tgt"].values /
                          np.maximum(g["t_tgt"].values, 1)))
    print("\n  recency-weighted (half-life 3 games, "
          "effective n=%.1f):" % ne)
    print("    carry share   %.1f%%   (league RB prior %.0f%%)"
          % (100 * cs, 100 * PRI["RB"]["car_share"]))
    print("    yards/carry   %.2f    (prior %.2f)"
          % (yc, PRI["RB"]["ypcar"]))
    print("    TD/carry      %.3f   (prior %.3f)"
          % (tdc, PRI["RB"]["td_per_car"]))
    print("    target share  %.1f%%   (prior %.0f%%)"
          % (100 * ts, 100 * PRI["RB"]["tgt_share"]))
    def trust(r1):
        return ne * r1 / (1 + (ne - 1) * r1)
    print("\n  how much we trust each (measured reliability):")
    for comp in ("car_share", "ypcar", "td_per_car",
                 "tgt_share"):
        r1 = REL["RB"].get(comp, 0.1)
        print("    %-12s r=%.3f -> weight %.0f%% his, "
              "%.0f%% league"
              % (comp, r1, 100 * trust(r1),
                 100 * (1 - trust(r1))))
    tmc = float(g[g["season"] == 2026]["t_car"].mean()
                if len(g[g["season"] == 2026]) else 25)
    print("\n  his team runs %.1f times a game" % tmc)
    print("  so: %.1f carries x %.2f yds = %.0f yards"
          % (tmc * cs, yc, tmc * cs * yc))
