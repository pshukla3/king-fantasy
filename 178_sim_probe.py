import json
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

B = pd.read_csv("board_final.csv", low_memory=False)
print("=== ADP COVERAGE (AI drafters need this) ===")
for p in ["QB", "RB", "WR", "TE", "K", "DEF", "DST"]:
    d = B[B["position"] == p]
    if not len(d):
        continue
    n = int(pd.to_numeric(d["adp"], errors="coerce").notna().sum())
    print("  %-4s %3d players | %3d with ADP (%.0f%%)"
          % (p, len(d), n, 100.0 * n / len(d)))
a = pd.to_numeric(B["adp"], errors="coerce").dropna()
print("  ADP range %.1f to %.1f" % (a.min(), a.max()))

print("\n=== COMPONENT STATS FOR RE-SCORING ===")
C = json.load(open("player_cards.json"))
byp = {}
for v in C.values():
    k = v["ps"]
    byp.setdefault(k, [0, 0])
    byp[k][0] += 1
    if "p26" in v:
        byp[k][1] += 1
for k in sorted(byp):
    t, h = byp[k]
    print("  %-4s %3d cards | %3d with 2026 components (%.0f%%)"
          % (k, t, h, 100.0 * h / t))

print("\n=== IDP FEASIBILITY ===")
W = pl(nfl.load_player_stats(seasons=[2025]))
dcols = [c for c in W.columns
         if any(x in c.lower() for x in
                ["tackle", "sack", "interception", "pass_def",
                 "forced", "def_", "qb_hit"])]
print("  defensive-looking columns: %s" % dcols[:14])
if dcols:
    d = W[W["position"].isin(["LB", "DB", "DL", "CB",
                              "S", "DE", "DT"])] \
        if "position" in W.columns else W
    print("  rows with a defensive position: %d" % len(d))
else:
    print("  NONE - IDP not possible from this source")
