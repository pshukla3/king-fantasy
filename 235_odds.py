import json
import pickle
import numpy as np

D = json.load(open("league_data.json"))
SH = pickle.load(open("shocks.pkl", "rb"))
for k in list(SH):
    SH[k] = np.asarray(SH[k], dtype=np.float32)
print("shock pools: %s"
      % {k: len(SH[k]) for k in sorted(SH)})

SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE",
         "FLEX", "FLEX", "K", "DEF"]
FLEX = ("RB", "WR", "TE")

def pos(p):
    q = str(p.get("pos") or "")
    return "DEF" if q in ("DST", "DEF") else q

def lineup(ps, wk):
    av = [p for p in ps
          if int(p.get("bye") or 0) != wk
          and float(p.get("ppg") or 0) > 0]
    used = set()
    out = []
    for s in SLOTS:
        bi, bv = -1, -1.0
        for i, p in enumerate(av):
            if i in used:
                continue
            q = pos(p)
            ok = (q in FLEX) if s == "FLEX" else (q == s)
            if ok and float(p["ppg"]) > bv:
                bv, bi = float(p["ppg"]), i
        if bi >= 0:
            used.add(bi)
            out.append((pos(av[bi]), bv))
    return out

R = {int(t["roster_id"]): t["players"]
     for t in D["rosters"]}
f = lineup(R[1], 1)
print("rosters %d | wk1 roster 1: %d starters, %.2f"
      % (len(R), len(f), sum(x[1] for x in f)))

N = 200000
rng = np.random.default_rng(7)

def sim(fill):
    t = np.zeros(N, dtype=np.float32)
    for q, ppg in fill:
        z = SH.get(q, SH["QB"])
        t += np.float32(ppg) * z[
            rng.integers(0, len(z), N)]
    return t

EW = {r: 0.0 for r in R}
print("\n=== WEEKLY WIN PROBABILITY ===")
print("  %3s %9s %7s %7s %7s"
     % ("wk", "matchup", "projA", "projB", "P(A)"))
for wk in sorted(D["weeks"], key=lambda x: int(x)):
    for g in D["weeks"][wk]:
        a, b = int(g["a"]), int(g["b"])
        ta = sim(lineup(R[a], int(wk)))
        tb = sim(lineup(R[b], int(wk)))
        p = float((ta > tb).mean())
        g["pa"] = round(float(ta.mean()), 2)
        g["pb"] = round(float(tb.mean()), 2)
        g["wp"] = round(p, 4)
        EW[a] += p
        EW[b] += 1.0 - p
        if int(wk) == 1:
            print("  %3s %4d v%-3d %7.1f %7.1f %6.1f%%"
                  % (wk, a, b, g["pa"], g["pb"],
                     100 * p))
print("  simulated %d weeks x %d sims"
      % (len(D["weeks"]), N))

NM = {int(t["roster_id"]): t["name"]
      for t in D["rosters"]}
G = len(D["weeks"])
print("\n=== PROJECTED RECORD (%d WEEKS) ===" % G)
print("  %-24s %10s" % ("team", "exp W-L"))
for rid, w in sorted(EW.items(), key=lambda x: -x[1]):
    me = "  <-- YOU" if rid == 1 else ""
    print("  %-24s %5.1f-%-4.1f%s"
          % (str(NM[rid])[:24], w, G - w, me))

for grp in ("teams", "rosters"):
    for t in D[grp]:
        t["ew"] = round(EW.get(int(t["roster_id"]),
                               0.0), 2)
json.dump(D, open("league_data.json", "w"), indent=1)
print("\nwrote league_data.json (wp per game, ew per team)")
print("\n  MEASURED: per-position weekly shock pools")
print("  from 48,499 player-weeks (193_weekly_sim).")
print("  ASSUMED: K and DST reuse the QB pool -")
print("  their own weekly variance was never fit.")
