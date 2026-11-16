import glob, re
import numpy as np
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

I = pd.concat([pd.read_parquet(f) for f in
               sorted(glob.glob("data_inj/inj_*.parquet"))],
              ignore_index=True)
NM = next((c for c in ("full_name", "player_name",
                       "player_display_name", "name")
           if c in I.columns), None)
assert NM, "no name column: %s" % list(I.columns)
I = I[I["report_status"].notna()].copy()
I["k"] = I[NM].map(norm)
I = I[["season", "week", "k", "report_status",
       "report_primary_injury"]]
print("injury rows %d | seasons %s-%s"
      % (len(I), I.season.min(), I.season.max()))

W = pd.read_csv("real_weekly_stats.csv")
WN = next((c for c in ("player_display_name", "player_name",
                       "full_name", "name")
           if c in W.columns), None)
PT = next((c for c in ("fantasy_points_ppr", "fantasy_points",
                       "ppr", "points")
           if c in W.columns), None)
assert WN and PT, "cols: %s" % list(W.columns)[:20]
print("weekly rows %d | name=%s pts=%s" % (len(W), WN, PT))
W = W[W[WN].notna()].copy()
W["k"] = W[WN].map(norm)
W[PT] = pd.to_numeric(W[PT], errors="coerce").fillna(0.0)

# season baseline per player, excluding the week measured
g = W.groupby(["season", "k"])[PT]
W["ssum"] = g.transform("sum")
W["scnt"] = g.transform("count")
W["base"] = (W["ssum"] - W[PT]) / (W["scnt"] - 1).clip(lower=1)
W = W[W["scnt"] >= 4]

# universe = players who appear as skill players that
# season. Injury reports cover all 53; the stats file
# only has QB/RB/WR/TE, so an unfiltered denominator
# measures roster composition, not injury.
W["season"] = W["season"].astype(int)
W["week"] = W["week"].astype(int)
I["season"] = I["season"].astype(int)
I["week"] = I["week"].astype(int)
UNIV = set(zip(W["season"], W["k"]))
n0 = len(I)
I = I[[(a, b) in UNIV
       for a, b in zip(I["season"], I["k"])]].copy()
print("injury rows %d -> %d after skill-player filter"
      % (n0, len(I)))

J = I.merge(W[["season", "week", "k", PT, "base"]],
            on=["season", "week", "k"], how="left")
J["played"] = J[PT].notna()
print("\njoined %d | matched to a stat line %d (%.0f%%)"
      % (len(J), int(J.played.sum()),
         100.0 * J.played.mean()))

print("\n%-14s %6s %7s %8s %8s %8s"
      % ("STATUS", "N", "PLAY%", "RATIO", "EXP MULT",
         "vs base"))
print("-" * 58)
ROWS = {}
for st in ("Questionable", "Doubtful", "Out"):
    d = J[J.report_status == st]
    if len(d) < 50:
        continue
    pr = float(d.played.mean())
    p = d[d.played & (d.base > 2.0)]
    ratio = float((p[PT] / p["base"]).clip(0, 4).mean())
    mult = pr * ratio
    ROWS[st] = {"exp": mult, "play": pr, "ratio": ratio}
    print("%-14s %6d %6.1f%% %8.3f %8.3f %8s"
          % (st, len(d), 100 * pr, ratio, mult,
             "%+.0f%%" % (100 * (mult - 1))))

print("\n=== QUESTIONABLE BY INJURY TYPE ===")
q = J[J.report_status == "Questionable"]
out = []
for ty, d in q.groupby("report_primary_injury"):
    if len(d) < 120:
        continue
    pr = float(d.played.mean())
    p = d[d.played & (d.base > 2.0)]
    if len(p) < 40:
        continue
    r = float((p[PT] / p["base"]).clip(0, 4).mean())
    out.append((ty, len(d), pr, r, pr * r))
out.sort(key=lambda x: x[4])
print("%-14s %6s %7s %8s %8s"
      % ("INJURY", "N", "PLAY%", "RATIO", "MULT"))
for ty, n, pr, r, m in out:
    print("%-14s %6d %6.1f%% %8.3f %8.3f"
          % (str(ty)[:14], n, 100 * pr, r, m))

import json
json.dump({"status": ROWS,
           "by_type": {t: {"exp": m, "play": pr,
                           "ratio": r}
                       for t, n, pr, r, m in out}},
          open("inj_mult.json", "w"), indent=1)
print("\nwrote inj_mult.json")
