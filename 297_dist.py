import numpy as np
import pandas as pd

W = pd.read_pickle("matchup_weekly.pkl")
print("matchup_weekly: %d rows" % len(W))
print("columns: %s" % list(W.columns)[:18])

def pick(*c):
    for x in c:
        if x in W.columns:
            return x
    return None

CP = pick("fantasy_points_ppr", "points", "pts",
          "fantasy_points", "fpts")
CI = pick("player_id", "gsis_id", "id")
CO = pick("position", "pos")
print("using points=%s id=%s pos=%s" % (CP, CI, CO))
if not (CP and CI and CO):
    print("MISSING required columns - stopping")
    raise SystemExit(1)

USE = [c for c in ["carries", "targets", "attempts",
                   "receptions", "rushing_attempts"]
       if c in W.columns]
print("activity columns: %s" % USE)
if USE:
    act = W[USE].fillna(0).sum(axis=1)
    n0 = len(W)
    W = W[act > 0]
    print("dropped %d inactive player-weeks (%.1f%%)"
          % (n0 - len(W), 100.0 * (n0 - len(W)) / n0))
W = W[[CI, CO, CP]].dropna()
W[CP] = pd.to_numeric(W[CP], errors="coerce")
W = W[W[CP].notna()]
avg = W.groupby(CI)[CP].transform("mean")
W = W[avg > 3.0].copy()
W["ratio"] = W[CP] / avg[avg > 3.0]

print("\n=== WEEKLY RATIO QUANTILES (actual / season avg) ===")
Q = {}
for p in ["QB", "RB", "WR", "TE", "K"]:
    d = W[W[CO] == p]["ratio"]
    if len(d) < 500:
        continue
    q10, q50, q90 = np.percentile(d, [10, 50, 90])
    Q[p] = (q10, q50, q90)
    print("  %-3s n=%6d  p10 %.2f  p50 %.2f  p90 %.2f"
          % (p, len(d), q10, q50, q90))
if not Q:
    print("no positions had enough data - stopping")
    raise SystemExit(1)

DFLT = Q.get("WR", (0.35, 0.9, 1.9))
B = pd.read_csv("board_final.csv")
B["points"] = pd.to_numeric(B["points"], errors="coerce")
n = 0
for i, r in B.iterrows():
    v = r["points"]
    if v != v or v <= 0:
        continue
    q = Q.get(str(r["position"]), DFLT)
    B.at[i, "p10"] = round(v * q[0], 2)
    B.at[i, "p50"] = round(v * q[1], 2)
    B.at[i, "p90"] = round(v * q[2], 2)
    n += 1

ok = B[["p10", "p50", "p90"]].notna().all(axis=1).sum()
print("\nfilled %d rows | coverage %d / %d" % (n, ok, len(B)))
bad = int((B["p10"] > B["p50"]).sum()
          + (B["p50"] > B["p90"]).sum())
print("ordering violations (must be 0): %d" % bad)
assert bad == 0, "p10/p50/p90 out of order"
med = B["p50"].median()
print("median p50 %.2f (should track ppg ~5-6)" % med)
assert 2 < med < 12, "p50 implausible"
B.to_csv("board_final.csv", index=False)
print("wrote board_final.csv")

for nm in ["Ja'Marr Chase", "Josh Allen", "Bhayshul Tuten"]:
    r = B[B["player_display_name"] == nm]
    if len(r):
        r = r.iloc[0]
        print("  %-18s ppg %.1f | p10 %.1f p50 %.1f p90 %.1f"
              % (nm, r["points"], r["p10"], r["p50"],
                 r["p90"]))
