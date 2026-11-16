import numpy as np
import pandas as pd

D = pd.read_csv("wp_h2h_plays.csv")
o, e = D["ours"].values, D["espn"].values
y, gg, qq = D["y"].values, D["g"].values, D["qtr"].values
print("plays %d | games %d" % (len(D), len(set(gg))))

def bins(p, yy, nb=10):
    out = []
    for i in range(nb):
        lo, hi = i / nb, (i + 1) / nb
        k = (p >= lo) & ((p < hi) if i < nb - 1
                         else (p <= hi))
        if k.sum():
            out.append((int(k.sum()),
                        float(p[k].mean()),
                        float(yy[k].mean())))
    return out

def ece(p, yy):
    b = bins(p, yy)
    n = sum(x[0] for x in b)
    return sum(x[0] * abs(x[1] - x[2]) for x in b) / n

def mce(p, yy):
    b = [x for x in bins(p, yy) if x[0] >= 100]
    return max(abs(x[1] - x[2]) for x in b) if b else 0.0

print("\n=== PAIRED CALIBRATION, IDENTICAL PLAYS ===")
print("  %-6s %10s %10s" % ("model", "ECE", "worst bin"))
print("  " + "-" * 30)
print("  %-6s %10.4f %10.4f" % ("ours", ece(o, y),
                                mce(o, y)))
print("  %-6s %10.4f %10.4f" % ("ESPN", ece(e, y),
                                mce(e, y)))

print("\n=== DECILES SIDE BY SIDE ===")
print("  %-9s %6s %7s %7s %7s %7s"
      % ("bucket", "n", "ours", "act", "espn", "act"))
print("  " + "-" * 48)
for i in range(10):
    lo, hi = i / 10.0, (i + 1) / 10.0
    ko = (o >= lo) & (o < hi)
    ke = (e >= lo) & (e < hi)
    if ko.sum() < 100 and ke.sum() < 100:
        continue
    print("  %.1f-%.1f %7d %7s %7s %7s %7s"
          % (lo, hi, int(ko.sum()),
             "%.3f" % o[ko].mean() if ko.sum() else "--",
             "%.3f" % y[ko].mean() if ko.sum() else "--",
             "%.3f" % e[ke].mean() if ke.sum() else "--",
             "%.3f" % y[ke].mean() if ke.sum() else "--"))

gs = sorted(set(gg))
idx = {x: np.where(gg == x)[0] for x in gs}
rng = np.random.default_rng(11)
obs = ece(e, y) - ece(o, y)
d = []
for _ in range(3000):
    pick = rng.choice(gs, size=len(gs), replace=True)
    ii = np.concatenate([idx[x] for x in pick])
    d.append(ece(e[ii], y[ii]) - ece(o[ii], y[ii]))
d = np.array(d)
print("\n=== PAIRED ECE DIFFERENCE (ESPN - ours) ===")
print("  observed %+.4f | 95%% CI %+.4f to %+.4f"
      % (obs, *np.percentile(d, [2.5, 97.5])))
print("  positive means WE are better calibrated")
print("  P(ours better calibrated) %.3f"
      % float((d > 0).mean()))

print("\n=== ECE BY QUARTER ===")
print("  %-4s %7s %9s %9s" % ("qtr", "n", "ours", "ESPN"))
for k in (1, 2, 3, 4):
    m = qq == k
    if m.sum() < 300:
        continue
    print("  %-4d %7d %9.4f %9.4f"
          % (k, int(m.sum()), ece(o[m], y[m]),
             ece(e[m], y[m])))
