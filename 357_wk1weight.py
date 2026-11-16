import os, ssl, certifi, re, glob
import urllib.request as U
import numpy as np
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
R = ("https://github.com/nflverse/nflverse-data/releases/"
     "download/snap_counts/snap_counts_%d.parquet")
os.makedirs("data_usage", exist_ok=True)
for y in range(2016, 2026):
    p = "data_usage/snaps_%d.parquet" % y
    if os.path.exists(p):
        continue
    try:
        open(p, "wb").write(U.urlopen(
            U.Request(R % y, headers=H), timeout=90,
            context=CTX).read())
        print("  snaps %d ok" % y)
    except Exception as e:
        print("  snaps %d FAIL %s" % (y, str(e)[:40]))

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

W = pd.read_parquet("weekly_all.parquet")
W["k"] = W["player_display_name"].map(norm)
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
W["season"] = W["season"].astype(int)
W["week"] = W["week"].astype(int)
W = W[W["week"] <= 17]
print("weekly rows %d" % len(W))

S = pd.concat([pd.read_parquet(f) for f in
               sorted(glob.glob("data_usage/snaps_*.parquet"))],
              ignore_index=True)
S["k"] = S["player"].map(norm)
S["season"] = S["season"].astype(int)
S["week"] = S["week"].astype(int)
S1 = S[S["week"] == 1][["season", "k", "offense_pct"]]
S1 = S1.rename(columns={"offense_pct": "snap1"})
print("snap rows %d | week1 %d" % (len(S), len(S1)))

rows = []
for (sea, k), d in W.groupby(["season", "k"]):
    w1 = d[d["week"] == 1]["fp"]
    rest = d[d["week"].between(2, 17)]["fp"]
    if not len(w1) or len(rest) < 6:
        continue
    prev = W[(W["season"] == sea - 1) & (W["k"] == k)]["fp"]
    if len(prev) < 6:
        continue
    rows.append({"season": sea, "k": k,
                 "prior": float(prev.mean()),
                 "wk1": float(w1.iloc[0]),
                 "rest": float(rest.mean())})
D = pd.DataFrame(rows).merge(S1, on=["season", "k"],
                             how="left")
D["snap1"] = pd.to_numeric(
    D["snap1"].astype(str).str.rstrip("%"),
    errors="coerce")
print("player-seasons with prior + wk1 + rest: %d" % len(D))
print("snap1 coverage: %d" % int(D["snap1"].notna().sum()))

def fit(tr, te, cols):
    X = np.column_stack([tr[c].values for c in cols]
                        + [np.ones(len(tr))])
    b = np.linalg.lstsq(X, tr["rest"].values, rcond=None)[0]
    Xe = np.column_stack([te[c].values for c in cols]
                         + [np.ones(len(te))])
    p = Xe.dot(b)
    return b, float(np.abs(p - te["rest"].values).mean())

SEAS = sorted(D["season"].unique())
print("\n=== WALK-FORWARD (train on prior seasons) ===")
print("%-6s %6s %8s %8s %8s"
      % ("TEST", "N", "PRIOR", "+WK1", "+SNAP"))
A = {"prior": [], "wk1": [], "snap": []}
for s in SEAS[3:]:
    tr = D[D["season"] < s]
    te = D[D["season"] == s]
    if len(te) < 40:
        continue
    _, m1 = fit(tr, te, ["prior"])
    b2, m2 = fit(tr, te, ["prior", "wk1"])
    t3 = tr.dropna(subset=["snap1"])
    e3 = te.dropna(subset=["snap1"])
    m3 = float("nan")
    if len(t3) > 60 and len(e3) > 20:
        b3, m3 = fit(t3, e3, ["prior", "wk1", "snap1"])
    A["prior"].append(m1)
    A["wk1"].append(m2)
    if m3 == m3:
        A["snap"].append(m3)
    print("%-6d %6d %8.3f %8.3f %8.3f"
          % (s, len(te), m1, m2, m3))

print("\nmean MAE  prior only : %.3f" % np.mean(A["prior"]))
print("mean MAE  + week 1   : %.3f" % np.mean(A["wk1"]))
if A["snap"]:
    print("mean MAE  + snap pct : %.3f" % np.mean(A["snap"]))

b, _ = fit(D, D, ["prior", "wk1"])
print("\nfull-sample coefficients:")
print("  rest_ppg = %.4f*prior + %.4f*wk1 + %.4f"
      % (b[0], b[1], b[2]))
print("\n  -> one week of production carries %.1f%% of the "
      "weight that a full prior season does"
      % (100.0 * b[1] / max(b[0], 1e-9)))
