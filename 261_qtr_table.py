import json
import numpy as np
import pandas as pd

D = pd.read_csv("wp_train.csv")
D["qtr"] = 4 - ((D["t"] - 1) // 900).astype(int)
D["qtr"] = D["qtr"].clip(1, 4)
print("plays %d | games %d"
      % (len(D), D["game_id"].nunique()))

BK = [(-99, -17, "down 17+"), (-16, -9, "down 9-16"),
      (-8, -4, "down 4-8"), (-3, -1, "down 1-3"),
      (0, 0, "tied"), (1, 3, "up 1-3"),
      (4, 8, "up 4-8"), (9, 16, "up 9-16"),
      (17, 99, "up 17+")]

print("\n=== WIN RATE BY QUARTER AND MARGIN ===")
print("  possessing team, measured, no model\n")
print("  %-11s %8s %8s %8s %8s"
      % ("state", "Q1", "Q2", "Q3", "Q4"))
print("  " + "-" * 46)
OUT = {}
for lo, hi, nm in BK:
    row, cells = [], {}
    for q in (1, 2, 3, 4):
        d = D[(D["qtr"] == q)
              & (D["score_differential"] >= lo)
              & (D["score_differential"] <= hi)]
        if len(d) < 200:
            row.append("     --")
            continue
        v = float(d["win"].mean())
        cells[q] = {"p": round(v, 3), "n": int(len(d))}
        row.append("  %.3f" % v)
    OUT[nm] = cells
    print("  %-11s %s" % (nm, "".join(
        "%8s" % x for x in row)))

print("\n=== SAMPLE SIZES ===")
for lo, hi, nm in BK:
    ns = [OUT[nm].get(q, {}).get("n", 0)
          for q in (1, 2, 3, 4)]
    print("  %-11s %7d %7d %7d %7d" % (nm, *ns))

json.dump(OUT, open("site/_qtr.json", "w"), indent=1)
print("\nwrote site/_qtr.json")
print("  this is empirical frequency over 3,018 games,")
print("  ignoring field position and who is favored -")
print("  the model conditions on those, this does not")
