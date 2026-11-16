import numpy as np
import pandas as pd
import mc_core as M

H = pd.read_csv("wp_h2h_plays.csv")
NE = ["sd", "t", "dn", "yl", "sp", "ph",
      "ours", "espn", "y", "qtr"]
ms = [c for c in NE if c not in H.columns]
if ms:
    print("MISSING:", ms)
    raise SystemExit(1)
H = H.dropna(subset=NE).reset_index(drop=True)
print("plays %d | games %d" % (len(H), H["g"].nunique()))

A = np.stack([
    np.clip(H["sd"].values, -28, 28).round(),
    np.round(H["t"].values / 20) * 20,
    np.clip(H["dn"].values, 1, 4).round(),
    np.clip(np.round(H["yl"].values / 5) * 5, 1, 99),
    np.round(np.clip(H["sp"].values, -21, 21))],
    axis=1).astype(np.float32)
U, inv = np.unique(A, axis=0, return_inverse=True)
print("unique states %d" % len(U))

NP, B = 2000, 1000
g = np.zeros(len(U))
rng = np.random.default_rng(11)
for i in range(0, len(U), B):
    u = U[i:i + B]
    rep = np.repeat(np.arange(len(u)), NP)
    m = M.simv(u[rep, 0], np.maximum(1.0, u[rep, 1]),
               u[rep, 3], u[rep, 4], rng,
               dn0=u[rep, 2].astype(np.int64))
    w = ((m > 0) + 0.5 * (m == 0)).astype(np.float32)
    g[i:i + len(u)] = w.reshape(len(u), NP).mean(axis=1)
    print("  sims %d/%d" % (min(i + B, len(U)), len(U)))

mc = np.clip(g[inv], 0.002, 0.998)
ph = H["ph"].values.astype(bool)
H["mc"] = np.where(ph, mc, 1.0 - mc)

def ll(p, y):
    p = np.clip(np.asarray(p), 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p)
                          + (1 - y) * np.log(1 - p)))
def br(p, y):
    return float(np.mean((np.asarray(p) - y) ** 2))

y = H["y"].values.astype(float)
print("\n=== HEAD TO HEAD (all plays) ===")
print("  %-20s %9s %9s" % ("model", "logloss", "brier"))
print("  " + "-" * 41)
for nm, v in [("mkt2 (logistic)", H["ours"].values),
              ("ESPN", H["espn"].values),
              ("drive/play MC", H["mc"].values)]:
    print("  %-20s %9.4f %9.4f" % (nm, ll(v, y), br(v, y)))

print("\n=== BY QUARTER (logloss) ===")
print("  %-3s %6s %9s %9s %9s"
      % ("qtr", "n", "mkt2", "ESPN", "MC"))
for q in sorted(H["qtr"].unique()):
    k = H[H["qtr"] == q]
    if len(k) < 200:
        continue
    yy = k["y"].values.astype(float)
    print("  %-3d %6d %9.4f %9.4f %9.4f"
          % (q, len(k), ll(k["ours"], yy),
             ll(k["espn"], yy), ll(k["mc"], yy)))

print("\n=== BLEND SWEEP (mc vs mkt2) ===")
best = (9.0, 0.0)
for wt in np.arange(0, 1.01, 0.1):
    v = ll(wt * H["mc"].values
           + (1 - wt) * H["ours"].values, y)
    if v < best[0]:
        best = (v, wt)
    print("  w_mc %.1f  logloss %.4f" % (wt, v))
print("  BEST w_mc %.1f at %.4f" % (best[1], best[0]))

W = best[1]
H["bl"] = W * H["mc"] + (1 - W) * H["ours"]
gs = H["g"].unique()
rg = np.random.default_rng(3)
d1, d2 = [], []
for _ in range(2000):
    s = rg.choice(gs, len(gs), replace=True)
    k = pd.concat([H[H["g"] == x] for x in s])
    yy = k["y"].values.astype(float)
    d1.append(ll(k["ours"], yy) - ll(k["bl"], yy))
    d2.append(ll(k["espn"], yy) - ll(k["bl"], yy))
for nm, d in [("blend vs mkt2", d1), ("blend vs ESPN", d2)]:
    d = np.array(d)
    print("\n  %s: edge %+.4f" % (nm, d.mean()))
    print("    95%% CI [%+.4f, %+.4f] | P(better) %.3f"
          % (np.percentile(d, 2.5),
             np.percentile(d, 97.5), (d > 0).mean()))
H.to_csv("mc_h2h.csv", index=False)
