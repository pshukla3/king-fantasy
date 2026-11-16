import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import log_loss, brier_score_loss

D = pd.read_csv("wp_train.csv")
print("plays %d | seasons %d-%d"
      % (len(D), D["season"].min(), D["season"].max()))

BASE = ["sd_t", "expt"]
FULL = ["sd_t", "expt", "score_differential", "t",
        "half", "down", "ydstogo", "yardline_100",
        "to_diff", "is4"]
MKT = FULL + ["spread_pos"]

def lr(cols):
    return Pipeline([("s", StandardScaler()),
                     ("m", LogisticRegression(
                         max_iter=2000, C=1.0))]), cols

def gb(cols):
    return HistGradientBoostingClassifier(
        max_depth=6, learning_rate=0.08,
        max_iter=300, random_state=0), cols

TESTS = [2021, 2022, 2023, 2024, 2025]
print("\n=== WALK-FORWARD, LOG LOSS (lower better) ===")
print("  %6s %8s %9s %9s %9s %9s"
      % ("test", "n", "base", "logit", "logit+mkt",
         "GBM"))
print("  " + "-" * 56)
agg = {k: [] for k in ["base", "logit", "mkt", "gbm"]}
NW = []
for T in TESTS:
    tr = D[D["season"] < T]
    te = D[D["season"] == T]
    if len(te) < 5000:
        continue
    row = []
    for nm, (mk, cols) in [
            ("base", lr(BASE)), ("logit", lr(FULL)),
            ("mkt", lr(MKT)), ("gbm", gb(FULL))]:
        m, c = mk, cols
        m.fit(tr[c].values, tr["win"].values)
        p = m.predict_proba(te[c].values)[:, 1]
        v = log_loss(te["win"].values, p)
        agg[nm].append(v)
        row.append(v)
    NW.append(len(te))
    print("  %6d %8d %9.4f %9.4f %9.4f %9.4f"
          % (T, len(te), row[0], row[1], row[2], row[3]))
print("  " + "-" * 56)
print("  %6s %8d %9.4f %9.4f %9.4f %9.4f"
      % ("mean", sum(NW), np.mean(agg["base"]),
         np.mean(agg["logit"]), np.mean(agg["mkt"]),
         np.mean(agg["gbm"])))
print("\n  logit vs base %+.2f%% | GBM vs logit %+.2f%%"
      % (100 * (1 - np.mean(agg["logit"])
                / np.mean(agg["base"])),
         100 * (1 - np.mean(agg["gbm"])
                / np.mean(agg["logit"]))))
print("  spread helps: %+.2f%%"
      % (100 * (1 - np.mean(agg["mkt"])
                / np.mean(agg["logit"]))))
