import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

CAND = ["game_id", "season", "fixed_drive",
        "fixed_drive_result", "posteam", "defteam",
        "home_team", "yardline_100",
        "game_seconds_remaining", "posteam_score",
        "defteam_score", "posteam_score_post",
        "defteam_score_post", "qtr", "play_id",
        "score_differential", "drive_play_count",
        "play_type"]

S = pl(nfl.load_pbp(seasons=[2025]))
print("2025 rows %d | cols %d" % (len(S), len(S.columns)))
print("\n=== DRIVE COLUMN CHECK ===")
HAVE = []
for c in CAND:
    ok = c in S.columns
    print("  %-28s %s" % (c, "yes" if ok else "MISSING"))
    if ok:
        HAVE.append(c)

if "fixed_drive_result" in S.columns:
    print("\n=== DRIVE RESULTS ===")
    print(S["fixed_drive_result"].value_counts()
          .head(12).to_string())
if "fixed_drive" in S.columns:
    g = S.groupby("game_id")["fixed_drive"].max()
    print("\ndrives per game: mean %.1f | min %d | max %d"
          % (g.mean(), g.min(), g.max()))

print("\n=== BUILDING DRIVE TABLE 2015-2025 ===")
out = []
for y in range(2015, 2026):
    d = pl(nfl.load_pbp(seasons=[y]))
    d = d[[c for c in HAVE if c in d.columns]]
    d = d[d["posteam"].notna() & d["fixed_drive"].notna()]
    d = d[d["qtr"] <= 4]
    out.append(d)
    print("  %d  %6d plays" % (y, len(d)))
P = pd.concat(out, ignore_index=True)
del out
P = P.sort_values(["game_id", "play_id"])

G = P.groupby(["game_id", "fixed_drive"])
rows = []
for (gid, dv), d in G:
    f, l = d.iloc[0], d.iloc[-1]
    t0 = f.get("game_seconds_remaining")
    t1 = l.get("game_seconds_remaining")
    y0 = f.get("yardline_100")
    if (t0 != t0) or (t1 != t1) or (y0 != y0):
        continue
    op = (l.get("posteam_score_post", 0)
          - f.get("posteam_score", 0))
    dp = (l.get("defteam_score_post", 0)
          - f.get("defteam_score", 0))
    op = 0 if op != op else float(op)
    dp = 0 if dp != dp else float(dp)
    rows.append({"gid": gid, "t0": float(t0),
                 "el": max(0.0, float(t0) - float(t1)),
                 "y0": float(y0), "op": op, "dp": dp,
                 "sd": float(f.get("score_differential")
                             or 0),
                 "res": str(f.get("fixed_drive_result"))})
D = pd.DataFrame(rows)
D.to_csv("drive_pool.csv", index=False)

print("\ndrives %d | games %d" % (len(D), D["gid"].nunique()))
print("\n=== SANITY ===")
print("  points per drive (off) %.3f  (expect ~1.9)"
      % D["op"].mean())
print("  points per drive (def) %.3f  (expect ~0.1)"
      % D["dp"].mean())
print("  seconds per drive      %.0f  (expect ~165)"
      % D["el"].mean())
print("  drives per game        %.1f  (expect ~22)"
      % (len(D) / D["gid"].nunique()))
print("  mean start yl100       %.1f  (expect ~72)"
      % D["y0"].mean())
print("\n  offense points distribution:")
print(D["op"].value_counts().head(8).to_string())
print("\n  start field position:")
for lo, hi in [(1, 20), (21, 50), (51, 75), (76, 100)]:
    k = D[(D["y0"] >= lo) & (D["y0"] <= hi)]
    print("    %3d-%-3d yl  n=%6d  pts %.2f  secs %.0f"
          % (lo, hi, len(k), k["op"].mean(),
             k["el"].mean()))
