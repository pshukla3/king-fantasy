import numpy as np
import pandas as pd

R = pd.read_csv("model_residuals.csv")
print("out-of-sample rows: %d" % len(R))

print("\n=== DOES THE MISS GROW WITH THE PROJECTION? ===")
print("  if sd rises across bins, one flat sigma is wrong\n")
FITS = {}
for p in ["RB", "WR", "TE"]:
    d = R[R["pos"] == p].copy()
    d["b"] = pd.qcut(d["pred"], 5, labels=False,
                     duplicates="drop")
    print("  --- %s ---" % p)
    print("  %5s %5s %9s %9s %9s"
          % ("bin", "n", "mean pred", "sd resid", "MAE"))
    mid, sds, ws = [], [], []
    for b in sorted(d["b"].dropna().unique()):
        x = d[d["b"] == b]
        mid.append(float(x["pred"].mean()))
        sds.append(float(x["res"].std()))
        ws.append(float(len(x)))
        print("  %5d %5d %9.2f %9.3f %9.3f"
              % (b, len(x), x["pred"].mean(),
                 x["res"].std(), x["res"].abs().mean()))
    mid = np.array(mid)
    sds = np.array(sds)
    ws = np.array(ws)
    A = np.vstack([np.ones(len(mid)), mid]).T
    cf = np.linalg.lstsq(A * ws[:, None] ** 0.5,
                         sds * ws ** 0.5, rcond=None)[0]
    FITS[p] = (float(cf[0]), float(cf[1]))
    print("  fit: sd = %.3f + %.4f x pred" % (cf[0], cf[1]))
    print("  at 6 ppg sd=%.2f | at 16 ppg sd=%.2f\n"
          % (cf[0] + cf[1] * 6, cf[0] + cf[1] * 16))

print("=" * 58)
print("=== SHAPE OF THE MISS ===")
print("  z = residual / predicted sd. a bell curve")
print("  would give sd 1.00, skew 0.00\n")
POOL = {}
print("  %-4s %6s %6s %6s %7s %7s %7s %7s"
      % ("pos", "sd", "skew", "p5", "p25", "p50",
         "p75", "p95"))
for p in ["RB", "WR", "TE"]:
    a, b = FITS[p]
    d = R[R["pos"] == p].copy()
    d["sd"] = (a + b * d["pred"]).clip(lower=0.5)
    z = (d["res"] / d["sd"]).values
    sk = float(((z - z.mean()) ** 3).mean() / z.std() ** 3)
    POOL[p] = z
    print("  %-4s %6.3f %+6.2f %6.2f %7.2f %7.2f %7.2f %7.2f"
          % (p, z.std(), sk,
             np.percentile(z, 5), np.percentile(z, 25),
             np.percentile(z, 50), np.percentile(z, 75),
             np.percentile(z, 95)))

np.savez("resid_pool.npz",
         **{k: v.astype(np.float32) for k, v in POOL.items()})
pd.DataFrame([{"pos": p, "a": FITS[p][0], "b": FITS[p][1]}
              for p in FITS]).to_csv("resid_sd_fit.csv",
                                     index=False)
print("\n  saved resid_pool.npz + resid_sd_fit.csv")
print("\n  positive skew = the upside tail is longer than")
print("  the downside. if so the sim bootstraps THESE")
print("  numbers rather than drawing from a normal,")
print("  because a bell curve would understate ceilings.")
