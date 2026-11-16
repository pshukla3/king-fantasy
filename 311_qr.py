import json
import numpy as np
import pandas as pd

W = pd.read_pickle("matchup_weekly.pkl")
CP = "fantasy_points_ppr"
W = W[W[CP].notna()].copy()
act = W[["carries", "targets", "attempts",
         "receptions"]].fillna(0).sum(axis=1)
n0 = len(W)
W = W[act > 0]
print("player-weeks: %d (dropped %d inactive)"
      % (len(W), n0 - len(W)))

avg = W.groupby("player_id")[CP].transform("mean")
W = W[avg > 3.0]
W["ratio"] = W[CP] / avg[avg > 3.0]
W["ratio"] = W["ratio"].clip(0, 4.0)

Q = {}
for p in ["QB", "RB", "WR", "TE", "K"]:
    d = W[W["position"] == p]["ratio"].values
    if len(d) < 400:
        continue
    Q[p] = [round(float(x), 3) for x in
            np.percentile(d, np.arange(1, 100))]
    a = np.array(Q[p])
    print("  %-3s n=%6d  p10 %.2f  p50 %.2f  p90 %.2f "
          "| sd %.2f" % (p, len(d), a[9], a[49], a[89],
                         d.std()))
Q["DST"] = Q.get("K", Q["WR"])
json.dump(Q, open("site/_qr.json", "w"))
print("\nwrote site/_qr.json (%d positions)" % len(Q))

def pw(ga, pa, gb, pb, n=40000):
    qa = np.array(Q.get(pa, Q["WR"]))
    qb = np.array(Q.get(pb, Q["WR"]))
    r = np.random.default_rng(3)
    x = ga * qa[r.integers(0, len(qa), n)]
    y = gb * qb[r.integers(0, len(qb), n)]
    return float((x > y).mean() + 0.5 * (x == y).mean())

print("\n=== SANITY: P(A outscores B) ===")
for na, ga, pa, nb, gb, pb in [
        ("Josh Allen", 22.9, "QB", "Lamar Jackson", 20.0, "QB"),
        ("Jahmyr Gibbs", 17.0, "RB", "Bijan Robinson", 16.5, "RB"),
        ("Puka Nacua", 17.9, "WR", "Ja'Marr Chase", 16.2, "WR"),
        ("Trey McBride", 13.1, "TE", "Kyle Pitts", 8.9, "TE"),
        ("Gibbs 17.0", 17.0, "RB", "a 8.0 ppg RB", 8.0, "RB")]:
    print("  %-16s over %-16s  %.1f%%"
          % (na, nb, 100 * pw(ga, pa, gb, pb)))
