import json
import os
import numpy as np
import pandas as pd
import nflreadpy as nfl

SEASON = 2026

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

try:
    W = pl(nfl.load_player_stats(seasons=[SEASON]))
    print("nflreadpy %d: %d rows" % (SEASON, len(W)))
except Exception as e:
    print("nflreadpy %d unavailable: %s" % (SEASON, str(e)[:70]))
    W = pd.DataFrame()

if not len(W):
    print("\nno %d results yet - this is expected before "
          "Week 1 kicks off" % SEASON)
    print("plumbing verified: script runs clean on empty data")
    json.dump({"season": SEASON, "weeks": [], "players": {}},
              open("site/_wk.json", "w"))
    print("wrote empty site/_wk.json")
    raise SystemExit(0)

CP = ("fantasy_points_ppr" if "fantasy_points_ppr"
      in W.columns else "fantasy_points")
W[CP] = pd.to_numeric(W[CP], errors="coerce").fillna(0)
wks = sorted(int(x) for x in W["week"].dropna().unique())
print("weeks with results: %s" % wks)

B = pd.read_csv("board_final.csv")
PROJ = {}
for _, r in B.iterrows():
    try:
        PROJ[str(r["player_id"])] = float(r["points"])
    except Exception:
        pass

OUT = {}
for _, r in W.iterrows():
    pid = str(r.get("player_id", ""))
    if not pid:
        continue
    d = OUT.setdefault(pid, {
        "nm": r.get("player_display_name", ""),
        "ps": r.get("position", ""),
        "tm": r.get("team", ""), "wk": {}})
    d["wk"][str(int(r["week"]))] = round(float(r[CP]), 2)

hit = 0
for pid, d in OUT.items():
    v = list(d["wk"].values())
    d["avg"] = round(sum(v) / len(v), 2) if v else 0.0
    p = PROJ.get(pid)
    if p:
        d["proj"] = round(p, 2)
        d["diff"] = round(d["avg"] - p, 2)
        hit += 1
json.dump({"season": SEASON, "weeks": wks, "players": OUT},
          open("site/_wk.json", "w"))
print("\nwrote site/_wk.json: %d players, %d matched to "
      "projections" % (len(OUT), hit))

sc = [d for d in OUT.values() if "diff" in d
      and d["avg"] >= 5]
sc.sort(key=lambda x: -x["diff"])
print("\n=== BIGGEST OVERPERFORMERS (proj vs actual) ===")
for d in sc[:8]:
    print("  %-22s %-3s proj %5.1f  actual %5.1f  %+5.1f"
          % (d["nm"][:22], d["ps"], d["proj"], d["avg"],
             d["diff"]))
print("\n=== BIGGEST UNDERPERFORMERS ===")
for d in sc[-8:]:
    print("  %-22s %-3s proj %5.1f  actual %5.1f  %+5.1f"
          % (d["nm"][:22], d["ps"], d["proj"], d["avg"],
             d["diff"]))

err = np.array([d["diff"] for d in sc])
if len(err):
    print("\n=== MODEL ERROR SO FAR ===")
    print("  players scored   %d" % len(err))
    print("  mean error       %+.2f ppg (bias)" % err.mean())
    print("  mean abs error    %.2f ppg" % np.abs(err).mean())
    print("  (MAE near 4-5 is normal this early; a large "
          "mean error means the board is systematically "
          "off, not just noisy)")
