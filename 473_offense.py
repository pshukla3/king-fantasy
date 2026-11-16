import json
import numpy as np
import nflreadpy as nfl

sc = nfl.load_schedules([2024, 2025, 2026]).to_pandas()
sc = sc[sc["total_line"].notna() & sc["spread_line"].notna()]

# confirm the sign convention empirically
d = sc[sc["home_score"].notna()]
c1 = np.corrcoef(d["total_line"] / 2 + d["spread_line"] / 2,
                 d["home_score"])[0, 1]
c2 = np.corrcoef(d["total_line"] / 2 - d["spread_line"] / 2,
                 d["home_score"])[0, 1]
PLUS = c1 > c2
print("spread sign check:  +%.3f  vs  -%.3f  -> home uses %s"
      % (c1, c2, "PLUS" if PLUS else "MINUS"))

def implied(row, home):
    t, s = row["total_line"], row["spread_line"]
    h = t / 2 + (s / 2 if PLUS else -s / 2)
    return h if home else t - h

IMP = {}
for _, g in sc.iterrows():
    w, yr = int(g["week"]), int(g["season"])
    IMP[(yr, w, g["home_team"])] = implied(g, True)
    IMP[(yr, w, g["away_team"])] = implied(g, False)

# how much does QB scoring actually track implied total?
ps = nfl.load_player_stats([2024, 2025]).to_pandas()
ps = ps[(ps["position"] == "QB") & (ps["attempts"] >= 15)].copy()
ps["imp"] = [IMP.get((s, w, t)) for s, w, t
             in zip(ps["season"], ps["week"], ps["team"])]
ps = ps[ps["imp"].notna()]
ps["fp"] = (ps["passing_yards"] * .04 + ps["passing_tds"] * 4
            - ps["passing_interceptions"]
            + ps["rushing_yards"] * .1 + ps["rushing_tds"] * 6)
r = np.corrcoef(ps["imp"], ps["fp"])[0, 1]
b = np.polyfit(ps["imp"], ps["fp"], 1)
print("QB pts vs implied total:  r = %.3f   slope = %.2f pts"
      " per implied point  (n=%d)" % (r, b[0], len(ps)))

LGT = float(ps["imp"].mean())
print("league mean implied total: %.2f" % LGT)

cur = sc[sc["season"] == 2026]
TT = {}
for _, g in cur.iterrows():
    w = int(g["week"])
    TT.setdefault(g["home_team"], {})[w] = implied(g, True)
    TT.setdefault(g["away_team"], {})[w] = implied(g, False)
avg = {t: float(np.mean(list(v.values()))) for t, v in TT.items()}
json.dump({"wk": {t: {str(k): round(x, 2)
                      for k, x in v.items()}
                  for t, v in TT.items()},
           "avg": {t: round(v, 2) for t, v in avg.items()},
           "lg": round(LGT, 2),
           "slope": round(float(b[0]), 3)},
          open("teamtotal.json", "w"))

o = sorted(avg.items(), key=lambda x: -x[1])
print("\n=== BEST OFFENSES (mean implied total 2026) ===")
for t, v in o[:8]:
    print("   %-5s %6.2f" % (t, v))
print("   ...")
for t, v in o[-6:]:
    print("   %-5s %6.2f" % (t, v))

print("\n=== LAMAR JACKSON game log ===")
g = nfl.load_player_stats([2025, 2026]).to_pandas()
g = g[g["player_display_name"] == "Lamar Jackson"]
g = g.sort_values(["season", "week"]).tail(12)
print("  %-6s %-4s %6s %6s %6s %6s %6s"
      % ("SEASON", "WK", "ATT", "PYD", "CAR", "RYD", "RTD"))
for _, r2 in g.iterrows():
    print("  %-6d %-4d %6.0f %6.0f %6.0f %6.0f %6.0f"
          % (r2["season"], r2["week"], r2["attempts"],
             r2["passing_yards"], r2["carries"],
             r2["rushing_yards"], r2["rushing_tds"]))
