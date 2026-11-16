import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}
W = pl(nfl.load_player_stats(seasons=list(range(2021, 2026))))
W["targets"] = pd.to_numeric(W["targets"],
                             errors="coerce").fillna(0.0)
W["team"] = W["team"].astype(str).replace(FIX)
W = W[W["position"].isin(["WR", "TE", "RB"])]

T = W.groupby(["team", "season", "player_id"]).agg(
    tar=("targets", "sum")).reset_index()
T = T[T["tar"] > 0]
T["rk"] = T.groupby(["team", "season"])["tar"].rank(
    ascending=False, method="first").astype(int)
tot = T.groupby(["team", "season"])["tar"].transform("sum")
T["sh"] = T["tar"] / tot

print("=== HOW CONCENTRATED ARE TEAM TARGETS? ===")
print("  share going to each depth slot, 2021-25\n")
print("  %5s %7s %9s" % ("slot", "share", "cumul"))
cur = 0.0
CURVE = {}
for k in range(1, 13):
    d = T[T["rk"] == k]["sh"]
    if len(d) < 20:
        break
    cur += float(d.mean())
    CURVE[k] = float(d.mean())
    print("  %5d %7.3f %9.3f" % (k, d.mean(), cur))
TOPN = 8
POOL = sum(CURVE.get(k, 0) for k in range(1, TOPN + 1))
print("\n  top %d pass-catchers take %.1f%% of targets"
      % (TOPN, 100 * POOL))
print("  everyone below that splits %.1f%%"
      % (100 * (1 - POOL)))
np.save("target_curve.npy",
        np.array([CURVE.get(k, 0.0)
                  for k in range(1, 13)]))

C = pd.read_csv("wr_rebuild_2026.csv")
C["team"] = C["team"].astype(str).replace(FIX)
C["rk"] = C.groupby("team")["score"].rank(
    ascending=False, method="first").astype(int)

top = C[C["rk"] <= TOPN].copy()
sub = C[C["rk"] > TOPN].copy()
s = top.groupby("team")["score"].transform("sum")
top["alloc"] = top["score"] / s.replace(0, np.nan) * POOL

n = sub.groupby("team")["score"].transform("count")
sub["alloc"] = (1.0 - POOL) / n.replace(0, np.nan)

C = pd.concat([top, sub], ignore_index=True)
C["tar26"] = C["alloc"] * C["tv"]
C["rec26"] = C["tar26"] * C["ctch"]
C["ppg26"] = C["rec26"] * (1.0 + 0.1 * C["ypr"]
                           + 6.0 * C["tdr"])
C.to_csv("wr_rebuild_2026.csv", index=False)

chk = C.groupby("team")["tar26"].sum()
print("\n=== SANITY ===")
print("  team target totals: mean %.1f | min %.1f | max %.1f"
      % (chk.mean(), chk.min(), chk.max()))
print("  (should be near the 28-34 tar/g team range)")
tp = C.nlargest(5, "tar26")
print("\n  most-targeted players:")
for _, r in tp.iterrows():
    print("    %-24s %-3s %5.1f tar/g"
          % (str(r["player_display_name"])[:24],
             r["position"], r["tar26"]))
print("\n  Nacua sanity: he had 9.8 tar/g in 2025")

WR = C[C["position"] == "WR"].copy()
WR["old"] = pd.to_numeric(WR["points"], errors="coerce")
WR = WR.sort_values("ppg26", ascending=False)
WR = WR.reset_index(drop=True)
print("\n=== 2026 WR RANKINGS, REALLOCATED ===")
print("  %-3s %-22s %-4s %6s %6s %7s %7s %7s"
      % ("#", "player", "tm", "tar/g", "rec/g",
         "NEW", "old", "move"))
for i, r in WR.head(36).iterrows():
    o = r["old"]
    print("  %-3d %-22s %-4s %6.1f %6.1f %7.2f %7s %+7s"
          % (i + 1, str(r["player_display_name"])[:22],
             str(r["team"])[:4], r["tar26"], r["rec26"],
             r["ppg26"],
             "--" if o != o else "%.2f" % o,
             "--" if o != o else "%.2f" % (r["ppg26"] - o)))
