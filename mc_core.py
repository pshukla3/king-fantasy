import numpy as np

Z = np.load("play_pool.npz")
OP, DPT = Z["op"], Z["dp"]
EL = np.maximum(1.0, Z["el"])
Y1 = Z["y1"]
N = len(OP)

YB = [20, 40, 60, 80]
TB = [15, 40, 90, 180, 420, 900, 1800]
SB = [-8.5, -0.5, 0.5, 8.5]
NT = len(TB) + 1
TC = np.array([0, 0, 0, 1, 1, 2, 2, 3])
MIN = 60

def yb(y):
    return np.digitize(y, YB)
def tb(t):
    return np.digitize(t, TB)
def sb(s):
    return np.digitize(s, SB)

CY, CT = yb(Z["y"]), tb(Z["t0"])
CS, CD = sb(Z["sd"]), np.clip(Z["dn"], 1, 4) - 1
CC = TC[CT]
ALL = np.arange(N)
LN = ["y+dn+t+s", "y+dn+t", "y+t+s", "y+t",
      "y+tc+s", "y+tc", "y only", "ALL"]
KEY = {}
LVL = np.zeros(8, dtype=int)
for a in range(5):
    ma = CY == a
    for d in range(4):
        md = ma & (CD == d)
        for b in range(NT):
            cc = TC[b]
            mt = ma & (CT == b)
            mdt = md & (CT == b)
            mc_ = ma & (CC == cc)
            for c in range(5):
                cand = [mdt & (CS == c), mdt,
                        mt & (CS == c), mt,
                        mc_ & (CS == c), mc_, ma]
                got, lv = ALL, 7
                for L, m in enumerate(cand):
                    v = np.where(m)[0]
                    if len(v) >= MIN:
                        got, lv = v, L
                        break
                KEY[((a * 4 + d) * NT + b) * 5 + c] = got
                LVL[lv] += 1

def _key(y, d, t, s):
    return (((yb(y) * 4 + np.clip(d, 1, 4) - 1) * NT
             + tb(t)) * 5 + sb(s)).astype(np.int32)

def simv(sd0, t0, y0, sp, rng, dn0=None, cap=80,
         half=True):
    n = len(sd0)
    sd = np.asarray(sd0, dtype=np.float32).copy()
    t = np.asarray(t0, dtype=np.float32).copy()
    y = np.asarray(y0, dtype=np.float32).copy()
    sp = np.asarray(sp, dtype=np.float32)
    d = (np.ones(n, dtype=np.int64) if dn0 is None
         else np.asarray(dn0, dtype=np.int64).copy())
    sgn = np.ones(n, dtype=np.float32)
    s0 = sgn.copy()
    done = t <= 1800.0
    for _ in range(cap):
        ia = np.where(t > 0)[0]
        if len(ia) == 0:
            break
        k = _key(y[ia], d[ia], t[ia], sd[ia] * sgn[ia])
        o = np.argsort(k, kind="stable")
        ia, k = ia[o], k[o]
        uk, st = np.unique(k, return_index=True)
        bd = list(st) + [len(k)]
        for q in range(len(uk)):
            j = ia[bd[q]:bd[q + 1]]
            p = KEY[int(uk[q])]
            pk = p[rng.integers(0, len(p), len(j))]
            el = EL[pk]
            sd[j] += (sgn[j] * (OP[pk] - DPT[pk])
                      + sp[j] * el / 3600.0)
            t[j] -= el
            y[j] = Y1[pk]
            sgn[j] = -sgn[j]
        d[:] = 1
        if half:
            h = (~done) & (t <= 1800.0) & (t > 0)
            sgn[h] = -s0[h]
            y[h] = 75.0
            done |= (t <= 1800.0)
    return sd

def wp(sd0, t0, y0, sp=0.0, dn=1, n=20000, seed=0):
    rng = np.random.default_rng(seed)
    m = simv(np.full(n, sd0), np.full(n, t0),
             np.full(n, y0), np.full(n, sp), rng,
             dn0=np.full(n, dn))
    return (float((m > 0).mean())
            + 0.5 * float((m == 0).mean())), m
