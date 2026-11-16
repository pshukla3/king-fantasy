import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

K = ["game_id", "fixed_drive", "posteam", "down",
     "ydstogo", "yardline_100", "qtr",
     "game_seconds_remaining", "score_differential",
     "posteam_score", "defteam_score",
     "posteam_score_post", "defteam_score_post"]
out = []
for yr in range(2015, 2026):
    d = pl(nfl.load_pbp(seasons=[yr]))
    d = d[[c for c in K if c in d.columns]]
    d = d[d["posteam"].notna() & d["fixed_drive"].notna()]
    out.append(d[d["qtr"] <= 4])
P = pd.concat(out, ignore_index=True)
del out
for c in K:
    if c not in ("game_id", "posteam"):
        P[c] = pd.to_numeric(P[c], errors="coerce")
P["k"] = P.groupby(["game_id", "fixed_drive",
                    "posteam"]).ngroup()
print("plays %d | drives %d" % (len(P), P["k"].nunique()))

S = P[P["down"].notna()].copy()
f = S.sort_values("game_seconds_remaining",
                  ascending=False).groupby("k").first()
mx = P.groupby("k")[["posteam_score_post",
                     "defteam_score_post"]].max()
DT = pd.DataFrame({
    "gid": f["game_id"],
    "t0": f["game_seconds_remaining"],
    "y0": f["yardline_100"],
    "op": mx["posteam_score_post"] - f["posteam_score"],
    "dp": mx["defteam_score_post"] - f["defteam_score"]})
DT = DT.dropna()
DT = DT[(DT["op"] >= 0) & (DT["op"] <= 8)
        & (DT["dp"] >= 0) & (DT["dp"] <= 8)]
DT = DT.sort_values(["gid", "t0"], ascending=[True, False])
DT["nt"] = DT.groupby("gid")["t0"].shift(-1).fillna(0.0)
DT["y1"] = DT.groupby("gid")["y0"].shift(-1).fillna(75.0)

S = S.join(DT[["op", "dp", "nt", "y1"]], on="k",
           how="inner")
S["el"] = (S["game_seconds_remaining"]
           - S["nt"]).clip(lower=1.0)
S = S[(S["el"] <= 900)
      & S["yardline_100"].notna()
      & S["ydstogo"].notna()]

np.savez_compressed(
    "play_pool.npz",
    y=S["yardline_100"].values.astype(np.float32),
    dn=S["down"].values.astype(np.int8),
    dist=S["ydstogo"].values.astype(np.float32),
    t0=S["game_seconds_remaining"].values.astype(np.float32),
    sd=S["score_differential"].values.astype(np.float32),
    op=S["op"].values.astype(np.float32),
    dp=S["dp"].values.astype(np.float32),
    el=S["el"].values.astype(np.float32),
    y1=S["y1"].values.astype(np.float32))
print("\nplay_pool.npz: %d rows" % len(S))
print("  mean drive pts from a play %.2f" % S["op"].mean())

print("\n=== THE STATE THAT WAS BROKEN ===")
print("  plays in FG range, tied, under 40s left:")
q = S[(S["yardline_100"] <= 40)
      & (S["score_differential"].abs() <= 3)
      & (S["game_seconds_remaining"] <= 40)]
print("    n=%d  drive pts %.2f  (drive-level was ~0.9)"
      % (len(q), q["op"].mean()))
print("\n  drive points by current field position:")
for lo, hi in [(1, 20), (21, 40), (41, 60),
               (61, 80), (81, 100)]:
    k = S[(S["yardline_100"] >= lo)
          & (S["yardline_100"] <= hi)]
    print("    %3d-%-3d  n=%7d  pts %.2f  secs %3.0f"
          % (lo, hi, len(k), k["op"].mean(),
             k["el"].mean()))
