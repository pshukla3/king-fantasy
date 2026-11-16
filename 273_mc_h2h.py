import numpy as np
import pandas as pd
import mc_core as M

H = pd.read_csv("wp_h2h_plays.csv")
print("cols:", list(H.columns))

def pick(*c):
    for x in c:
        if x in H.columns:
            return x
    return None

CW = pick("win", "y", "label", "posteam_win")
CO = pick("ours", "p_ours", "our_wp", "mkt2", "p_mkt2")
CE = pick("espn", "p_espn", "espn_wp")
CS = pick("score_differential", "sd")
CT = pick("game_seconds_remaining", "t")
CY = pick("yardline_100", "y2e")
CP = pick("spread_pos", "sp")
CQ = pick("qtr", "quarter")
need = {"win": CW, "ours": CO, "espn": CE,
        "sd": CS, "t": CT, "y": CY}
miss = [k for k, v in need.items() if v is None]
if miss:
    print("MISSING:", miss)
    raise SystemExit(1)

H = H[H[CT] <= 1800].copy()
H = H.dropna(subset=[CW, CO, CE, CS, CT, CY])
sp = (H[CP].values if CP else np.zeros(len(H)))
print("\nsecond-half plays %d" % len(H))

qs = (np.clip(H[CS].values, -28, 28).astype(int),
      (np.round(H[CT].values / 20) * 20).astype(int),
      (np.round(H[CY].values / 10) * 10).astype(int),
      np.round(np.nan_to_num(sp)).astype(int))
S = pd.DataFrame({"a": qs[0], "b": qs[1],
                  "c": qs[2], "d": qs[3]})
U, inv = np.unique(S.values, axis=0, return_inverse=True)
NP = 2500
print("unique states %d -> %d sims"
      % (len(U), len(U) * NP))

rng = np.random.default_rng(7)
rep = np.repeat(np.arange(len(U)), NP)
m = M.simv(U[rep, 0], np.maximum(1, U[rep, 1]),
           np.clip(U[rep, 2], 1, 99), U[rep, 3], rng)
w = ((m > 0).astype(np.float32)
     + 0.5 * (m == 0).astype(np.float32))
g = w.reshape(len(U), NP).mean(axis=1)
g = np.clip(g, 0.002, 0.998)
H["mc"] = g[inv]

def ll(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p)
                          + (1 - y) * np.log(1 - p)))
def br(p, y):
    return float(np.mean((p - y) ** 2))

y = H[CW].values.astype(float)
print("\n=== SECOND HALF HEAD-TO-HEAD ===")
print("  %-22s %9s %9s" % ("model", "logloss", "brier"))
print("  " + "-" * 43)
for nm, col in [("mkt2 (logistic)", H[CO].values),
                ("ESPN", H[CE].values),
                ("drive Monte Carlo", H["mc"].values),
                ("50/50 blend", 0.5 * H[CO].values
                 + 0.5 * H["mc"].values)]:
    print("  %-22s %9.4f %9.4f"
          % (nm, ll(col, y), br(col, y)))

print("\n=== BY QUARTER (logloss) ===")
if CQ:
    print("  %-4s %6s %9s %9s %9s"
          % ("qtr", "n", "mkt2", "ESPN", "MC"))
    for q in sorted(H[CQ].dropna().unique()):
        k = H[H[CQ] == q]
        if len(k) < 200:
            continue
        yy = k[CW].values.astype(float)
        print("  %-4d %6d %9.4f %9.4f %9.4f"
              % (q, len(k), ll(k[CO].values, yy),
                 ll(k[CE].values, yy),
                 ll(k["mc"].values, yy)))

print("\n=== BLEND WEIGHT SWEEP ===")
best = (9, 0)
for wt in np.arange(0, 1.01, 0.1):
    v = ll(wt * H["mc"].values
           + (1 - wt) * H[CO].values, y)
    if v < best[0]:
        best = (v, wt)
    print("  w_mc %.1f  logloss %.4f" % (wt, v))
print("  best w_mc %.1f at %.4f" % (best[1], best[0]))
H.to_csv("mc_h2h.csv", index=False)
