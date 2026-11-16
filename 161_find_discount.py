import glob
import re

pat = re.compile(r"exp_games|games_mult|/\s*17\.0|/\s*17\b")
print("=== exp_games / 17-game divisor USAGE ===")
hits = 0
for f in sorted(glob.glob("*.py")) + ["deploy.sh"]:
    try:
        lines = open(f, errors="ignore").read().split("\n")
    except Exception:
        continue
    out = []
    for i, l in enumerate(lines, 1):
        if pat.search(l) and not l.strip().startswith("#"):
            out.append((i, l.strip()[:74]))
    if out:
        hits += len(out)
        print("\n  %s" % f)
        for i, l in out:
            print("    %4d| %s" % (i, l))
print("\ntotal hits: %d" % hits)

print("\n=== board_final columns using games ===")
import pandas as pd
B = pd.read_csv("board_final.csv", low_memory=False)
print("  columns: %s" % [c for c in B.columns
                         if "game" in c or "mult" in c
                         or c in ("value", "vorp",
                                  "points")])
d = B[B["points"].notna() & (B["points"] > 0)].head(6)
print("\n  sample rows:")
print(d[["player_display_name", "position", "points",
         "exp_games", "vorp", "value"]].round(2)
      .to_string(index=False))
