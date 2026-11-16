import json
import pickle
import numpy as np
import pandas as pd

D = json.load(open("league_data.json"))
SH = pickle.load(open("shocks.pkl", "rb"))
for k in list(SH):
    SH[k] = np.asarray(SH[k], dtype=np.float32)
Z = np.load("resid_pool.npz")
SDF = pd.read_csv("resid_sd_fit.csv").set_index("pos")

SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE",
         "FLEX", "FLEX", "K", "DEF"]
FLEX = ("RB", "WR", "TE")

def pos(p):
    q = str(p.get("pos") or "")
    return "DEF" if q in ("DST", "DEF") else q

def sdfit(q, v):
    s = q if q in SDF.index else (
        "WR" if q == "QB" else None)
    if s is None:
        return 1.0
    return max(0.5, float(SDF.loc[s, "a"])
               + float(SDF.loc[s, "b"]) * v)

def zpool(q):
    return Z[q] if q in Z.files else Z["WR"]

R = {int(t["roster_id"]): t["players"]
     for t in D["rosters"]}
NM = {int(t["roster_id"]): t["name"]
      for t in D["rosters"]}
WKS = sorted(D["weeks"], key=lambda x: int(x))
print("teams %d | weeks %d | sd fits %s"
      % (len(R), len(WKS), list(SDF.index)))

def lineup(ps, wk):
    av = [(i, p) for i, p in enumerate(ps)
          if int(p.get("bye") or 0) != wk
          and float(p.get("ppg") or 0) > 0]
    used, out = set(), []
    for s in SLOTS:
        bi, bv = -1, -1.0
        for i, p in av:
            if i in used:
                continue
            q = pos(p)
            ok = (q in FLEX) if s == "FLEX" else (q == s)
            if ok and float(p["ppg"]) > bv:
                bv, bi = float(p["ppg"]), i
        if bi >= 0:
            used.add(bi)
            out.append(bi)
    return out

TEAM = {}
for rid, ps in R.items():
    P = np.array([float(p.get("ppg") or 0)
                  for p in ps], dtype=np.float32)
    Q = [pos(p) for p in ps]
    SD = np.array([sdfit(Q[i], P[i])
                   for i in range(len(P))],
                  dtype=np.float32)
    TEAM[rid] = {"P": P, "Q": Q, "SD": SD,
                 "f": {int(w): lineup(ps, int(w))
                       for w in WKS}}
print("lineups built for %d teams" % len(TEAM))
print("roster 1 wk1 starters %d | season sd range"
      " %.2f-%.2f"
      % (len(TEAM[1]["f"][1]), TEAM[1]["SD"].min(),
         TEAM[1]["SD"].max()))

N, CH = 50000, 25
per = N // CH
rng = np.random.default_rng(11)
G = len(WKS)
ids = sorted(R)
W = {r: np.zeros(N, dtype=np.float32) for r in ids}
PF = {r: np.zeros(N, dtype=np.float32) for r in ids}

print("\nsimulating %d seasons..." % N)
for c in range(CH):
    lo, hi = c * per, (c + 1) * per
    sc = {}
    for rid in ids:
        t = TEAM[rid]
        n = len(t["P"])
        zs = np.empty((n, per), dtype=np.float32)
        for i in range(n):
            z = zpool(t["Q"][i])
            zs[i] = z[rng.integers(0, len(z), per)]
        true = np.clip(t["P"][:, None]
                       + t["SD"][:, None] * zs, 0, None)
        m = np.zeros((G, per), dtype=np.float32)
        for wi, w in enumerate(WKS):
            for i in t["f"][int(w)]:
                sp = SH.get(t["Q"][i], SH["QB"])
                m[wi] += true[i] * sp[
                    rng.integers(0, len(sp), per)]
            PF[rid][lo:hi] += m[wi]
        sc[rid] = m
    for wi, w in enumerate(WKS):
        for g in D["weeks"][w]:
            a, b = int(g["a"]), int(g["b"])
            win = sc[a][wi] > sc[b][wi]
            W[a][lo:hi] += win
            W[b][lo:hi] += ~win
    if (c + 1) % 5 == 0:
        print("  chunk %d/%d" % (c + 1, CH))

PLAY = 6
Wm = np.vstack([W[r] for r in ids])
Pm = np.vstack([PF[r] for r in ids])
ordr = np.argsort(-(Wm * 1e6 + Pm), axis=0)
seed = np.empty_like(ordr)
for s in range(len(ids)):
    seed[ordr[s], np.arange(N)] = s + 1

print("\n=== SIMULATED SEASON, %d RUNS ===" % N)
print("  %-22s %6s %7s %9s %8s %8s"
      % ("team", "W", "PF", "playoff", "1 seed", "last"))
print("  " + "-" * 66)
rows = [(NM[r], Wm[i].mean(), Pm[i].mean(),
         float((seed[i] <= PLAY).mean()),
         float((seed[i] == 1).mean()),
         float((seed[i] == len(ids)).mean()), r)
        for i, r in enumerate(ids)]
for nm, w, pf, po, s1, sl, r in sorted(
        rows, key=lambda x: -x[3]):
    me = "  <-- YOU" if r == 1 else ""
    print("  %-22s %5.1f %7.0f %8.1f%% %7.1f%% %7.1f%%%s"
          % (str(nm)[:22], w, pf, 100 * po,
             100 * s1, 100 * sl, me))

i = ids.index(1)
print("\n=== YOUR WIN DISTRIBUTION ===")
for k in range(int(Wm[i].min()), int(Wm[i].max()) + 1):
    p = float((Wm[i].round() == k).mean())
    if p > 0.005:
        print("  %2d-%-2d wins %5.1f%%  %s"
              % (k, G - k, 100 * p, "#" * int(70 * p)))
print("\n  playoff field ASSUMED at %d teams" % PLAY)
print("  MEASURED: season residual pools + weekly")
print("  shocks. ASSUMED: QB uses the WR season sd,")
print("  K/DST a flat 1.0 - neither was ever fit.")
