import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

KEEP = ["game_id", "season", "fixed_drive",
        "fixed_drive_result", "posteam", "defteam",
        "yardline_100", "game_seconds_remaining",
        "posteam_score", "defteam_score",
        "posteam_score_post", "defteam_score_post",
        "qtr", "play_id", "score_differential",
        "down", "play_type"]

out = []
for y in range(2015, 2026):
    d = pl(nfl.load_pbp(seasons=[y]))
    d = d[[c for c in KEEP if c in d.columns]]
    d = d[d["posteam"].notna()
          & d["fixed_drive"].notna()
          & d["down"].notna()]
    d = d[d["qtr"] <= 4]
    out.append(d)
    print("  %d  %6d scrimmage plays" % (y, len(d)))
P = pd.concat(out, ignore_index=True)
del out
P = P.sort_values(["game_id", "play_id"])
print("scrimmage plays %d" % len(P))

rows = []
for (gid, dv, pt), d in P.groupby(
        ["game_id", "fixed_drive", "posteam"]):
    f, l = d.iloc[0], d.iloc[-1]
    t0 = f["game_seconds_remaining"]
    t1 = l["game_seconds_remaining"]
    y0 = f["yardline_100"]
    if (t0 != t0) or (t1 != t1) or (y0 != y0):
        continue
    op = float((l["posteam_score_post"] or 0)
               - (f["posteam_score"] or 0))
    dp = float((l["defteam_score_post"] or 0)
               - (f["defteam_score"] or 0))
    rows.append({"gid": gid, "t0": float(t0),
                 "el": max(0.0, float(t0) - float(t1)),
                 "y0": float(y0),
                 "op": 0.0 if op != op else op,
                 "dp": 0.0 if dp != dp else dp,
                 "sd": float(f["score_differential"] or 0),
                 "res": str(f["fixed_drive_result"])})
D = pd.DataFrame(rows)
D = D[(D["op"] >= 0) & (D["op"] <= 8)]
D = D[(D["dp"] >= 0) & (D["dp"] <= 8)]
D.to_csv("drive_pool.csv", index=False)

print("\ndrives %d | games %d"
      % (len(D), D["gid"].nunique()))
print("\n=== SANITY ===")
print("  off points/drive  %.3f   (expect ~1.9)"
      % D["op"].mean())
print("  def points/drive  %.3f   (expect ~0.1)"
      % D["dp"].mean())
print("  seconds/drive     %.0f     (expect ~150)"
      % D["el"].mean())
print("  drives/game       %.1f    (expect ~22)"
      % (len(D) / D["gid"].nunique()))
print("  mean start yl100  %.1f    (expect ~72)"
      % D["y0"].mean())

print("\n  start field position distribution:")
for lo, hi in [(1, 20), (21, 40), (41, 60),
               (61, 80), (81, 100)]:
    k = D[(D["y0"] >= lo) & (D["y0"] <= hi)]
    print("    %3d-%-3d  n=%6d (%4.1f%%)  pts %.2f"
          "  secs %3.0f"
          % (lo, hi, len(k), 100.0 * len(k) / len(D),
             k["op"].mean(), k["el"].mean()))

print("\n  offense points:")
print(D["op"].value_counts().head(6).to_string())
print("\n  by time remaining:")
for lo, hi in [(0, 300), (301, 900), (901, 1800),
               (1801, 3600)]:
    k = D[(D["t0"] >= lo) & (D["t0"] <= hi)]
    print("    %4d-%-4ds  n=%6d  pts %.2f  secs %3.0f"
          % (lo, hi, len(k), k["op"].mean(),
             k["el"].mean()))
