import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

S = pl(nfl.load_schedules(seasons=[2023, 2024, 2025]))
d = S[S["result"].notna() & S["spread_line"].notna()]
print("games %d" % len(d))
print("corr(spread_line, home margin) = %+.3f"
      % d["spread_line"].corr(d["result"]))
print("\n  %-16s %5s %12s %10s"
      % ("spread_line", "n", "home margin", "home win"))
for lo, hi in [(-99, -7), (-6.5, -3.5), (-3, -0.5),
               (0, 0), (0.5, 3), (3.5, 6.5), (7, 99)]:
    x = d[(d["spread_line"] >= lo)
          & (d["spread_line"] <= hi)]
    if len(x):
        print("  %+5.1f..%+5.1f %7d %12.2f %10.3f"
              % (lo, hi, len(x), x["result"].mean(),
                 (x["result"] > 0).mean()))
print("\n  positive corr => nflverse positive means"
      " HOME FAVORED")
print("  ESPN showed CIN -3.5 with CIN at home,"
      " so ESPN is inverted")

FIX = {"WSH": "WAS", "LAR": "LA", "JAC": "JAX",
       "AZ": "ARI"}
g = d[d["season"] == 2025].head(400)
K = {}
for _, r in g.iterrows():
    h = FIX.get(str(r["home_team"]), str(r["home_team"]))
    a = FIX.get(str(r["away_team"]), str(r["away_team"]))
    K[(a, h)] = float(r["spread_line"])
print("\nnflverse 2025 lines cached: %d" % len(K))
import json
json.dump({"%s@%s" % k: v for k, v in K.items()},
          open("nflverse_lines_2025.json", "w"))
