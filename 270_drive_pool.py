import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

KEEP = ["game_id", "fixed_drive", "posteam",
        "yardline_100", "game_seconds_remaining",
        "posteam_score", "defteam_score",
        "posteam_score_post", "defteam_score_post",
        "qtr", "play_id", "score_differential",
        "down", "fixed_drive_result"]
out = []
for y in range(2015, 2026):
    d = pl(nfl.load_pbp(seasons=[y]))
    d = d[[c for c in KEEP if c in d.columns]]
    d = d[d["posteam"].notna() & d["fixed_drive"].notna()]
    out.append(d[d["qtr"] <= 4])
P = pd.concat(out, ignore_index=True)
del out
for c in ["yardline_100", "game_seconds_remaining",
          "posteam_score", "defteam_score",
          "posteam_score_post", "defteam_score_post",
          "score_differential", "play_id"]:
    P[c] = pd.to_numeric(P[c], errors="coerce")
P = P.sort_values(["game_id", "play_id"])
print("plays %d" % len(P))

rows = []
for (gid, dv, pt), d in P.groupby(
        ["game_id", "fixed_drive", "posteam"],
        sort=False):
    s = d[d["down"].notna()]
    if not len(s):
        continue
    f = s.iloc[0]
    t0, y0 = f["game_seconds_remaining"], f["yardline_100"]
    if (t0 != t0) or (y0 != y0):
        continue
    op = float(np.nanmax(d["posteam_score_post"].values)
               - (f["posteam_score"] or 0))
    dp = float(np.nanmax(d["defteam_score_post"].values)
               - (f["defteam_score"] or 0))
    t1 = float(np.nanmin(s["game_seconds_remaining"]
                         .values))
    rows.append({"gid": gid, "t0": float(t0),
                 "el": max(0.0, float(t0) - t1),
                 "y0": float(y0),
                 "op": 0.0 if op != op else op,
                 "dp": 0.0 if dp != dp else dp,
                 "sd": float(f["score_differential"] or 0)})
D = pd.DataFrame(rows)
D = D[(D["op"] >= 0) & (D["op"] <= 8)]
D = D[(D["dp"] >= 0) & (D["dp"] <= 8)]
D = D.sort_values(["gid", "t0"], ascending=[True, False])
D["y1"] = D.groupby("gid")["y0"].shift(-1)
D["y1"] = D["y1"].fillna(75.0)
D.to_csv("drive_pool.csv", index=False)

print("\ndrives %d | games %d"
      % (len(D), D["gid"].nunique()))
print("  off pts/drive %.3f   (expect ~1.95)"
      % D["op"].mean())
print("  def pts/drive %.3f   (expect ~0.10)"
      % D["dp"].mean())
print("  secs/drive    %.0f     | start yl %.1f"
      % (D["el"].mean(), D["y0"].mean()))
print("\n  offense points (7 should now appear):")
print(D["op"].value_counts().head(6).to_string())
print("\n  next-drive start after each outcome:")
for lo, hi, nm in [(7, 8, "TD"), (3, 3, "FG"),
                   (0, 0, "no score")]:
    k = D[(D["op"] >= lo) & (D["op"] <= hi)]
    print("    %-9s n=%6d  opp starts at yl %.1f"
          % (nm, len(k), k["y1"].mean()))
