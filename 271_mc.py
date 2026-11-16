import numpy as np
import pandas as pd

D = pd.read_csv("drive_pool.csv")
OP = D["op"].values.astype(np.float32)
DPT = D["dp"].values.astype(np.float32)
EL = D["el"].values.astype(np.float32)
Y1 = D["y1"].values.astype(np.float32)
print("pool %d drives" % len(D))

def yb(y):
    return np.digitize(y, [40, 60, 80])
def tb(t):
    return np.digitize(t, [120, 300, 900, 1800])
def sb(s):
    return np.digitize(s, [-8.5, -0.5, 0.5, 8.5])

CY, CT, CS = yb(D["y0"].values), tb(D["t0"].values), \
    sb(D["sd"].values)
CELL, THIN = {}, 0
for a in range(4):
    for b in range(5):
        for c in range(5):
            m = (CY == a) & (CT == b) & (CS == c)
            if m.sum() >= 150:
                CELL[(a, b, c)] = np.where(m)[0]
            else:
                THIN += 1
FB2 = {}
for a in range(4):
    for b in range(5):
        m = (CY == a) & (CT == b)
        if m.sum() >= 150:
            FB2[(a, b)] = np.where(m)[0]
FB1 = {b: np.where(CT == b)[0] for b in range(5)}
ALL = np.arange(len(D))
print("full cells %d | thin (fell back) %d"
      % (len(CELL), THIN))

def pool(a, b, c):
    v = CELL.get((a, b, c))
    if v is None:
        v = FB2.get((a, b))
    if v is None:
        v = FB1.get(b, ALL)
    return v

def sim(sd0, t0, y0, n=20000, seed=0):
    rng = np.random.default_rng(seed)
    sd = np.full(n, float(sd0), dtype=np.float32)
    t = np.full(n, float(t0), dtype=np.float32)
    y = np.full(n, float(y0), dtype=np.float32)
    sgn = np.ones(n, dtype=np.float32)
    for _ in range(40):
        act = t > 0
        if not act.any():
            break
        ia = np.where(act)[0]
        key = (yb(y[ia]) * 100 + tb(t[ia]) * 10
               + sb(sd[ia] * sgn[ia]))
        for k in np.unique(key):
            j = ia[key == k]
            a, b, c = k // 100, (k // 10) % 10, k % 10
            p = pool(int(a), int(b), int(c))
            pick = p[rng.integers(0, len(p), len(j))]
            sd[j] += sgn[j] * (OP[pick] - DPT[pick])
            t[j] -= EL[pick]
            y[j] = Y1[pick]
            sgn[j] = -sgn[j]
    return (float((sd > 0).mean())
            + 0.5 * float((sd == 0).mean())), sd

print("\n=== SANITY (home team perspective) ===")
print("  %-34s %8s" % ("state", "win %"))
print("  " + "-" * 44)
for nm, a, b, c in [
        ("kickoff, tied, own 25", 0, 3600, 75),
        ("halftime, tied, own 25", 0, 1800, 75),
        ("up 7, 2:00 left, own 25", 7, 120, 75),
        ("down 7, 2:00 left, own 25", -7, 120, 75),
        ("down 3, 2:00 left, opp 30", -3, 120, 30),
        ("up 3, 0:30 left, own 25", 3, 30, 75),
        ("down 14, 5:00 left, own 25", -14, 300, 75),
        ("up 17, Q4 start, own 25", 17, 900, 75)]:
    p, _ = sim(a, b, c)
    print("  %-34s %7.1f%%" % (nm, 100 * p))

p, marg = sim(0, 3600, 75, n=40000)
print("\n=== FULL-GAME MARGIN DISTRIBUTION ===")
print("  from a tied kickoff, 40k sims")
print("  mean margin %+.2f | sd %.2f"
      % (marg.mean(), marg.std()))
print("  P(tie -> OT) %.3f" % float((marg == 0).mean()))
print("  mean total swing vs real NFL sd ~13.5")
