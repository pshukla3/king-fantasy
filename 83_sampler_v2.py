import re, numpy as np, pandas as pd
from math import erf, sqrt

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
H = H[H["season"] >= 2023].copy()
PC = "fantasy_points_ppr"
D = pd.read_csv("depth_latest.csv", low_memory=False)
TCC = pd.read_csv("teammate_corr.csv")

CORR = {}
for _, r in TCC.iterrows():
    a, b = [x.strip() for x in str(r["pair"]).split("/")]
    CORR[(a, b)] = float(r["r"])
    CORR[(b, a)] = float(r["r"])

def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

D["k_"] = D["player_name"].map(norm)
H["k_"] = H["player_display_name"].map(norm)
OFF = ["QB", "RB", "WR", "TE"]
_erf = np.vectorize(erf)

def wk(n):
    w = H[H["k_"] == n][PC].dropna().values
    if len(w) < 8:
        w = H[H["k_"].str.contains(n, na=False)][PC].dropna().values
    return np.sort(w)

def build(names):
    P = []
    for nm in names:
        n = norm(nm)
        d = D[D["k_"].str.contains(n, na=False) & D["pos_abb"].isin(OFF)]
        w = wk(n)
        if not len(d) or len(w) < 8:
            print("  SKIP %-22s depth=%d weeks=%d" % (nm, len(d), len(w)))
            continue
        r0 = d.sort_values("pos_rank").iloc[0]
        flag = "  <-- THIN" if len(w) < 20 else ""
        print("  %-22s %-4s %-5s n=%3d  mean %5.1f%s"
              % (nm, r0["team"], "%s%d" % (r0["pos_abb"], int(r0["pos_rank"])),
                 len(w), w.mean(), flag))
        P.append({"name": nm, "team": r0["team"],
                  "role": "%s%d" % (r0["pos_abb"], int(r0["pos_rank"])), "w": w})
    return P

def run(P, N=20000, seed=7):
    k = len(P)
    R = np.eye(k)
    for i in range(k):
        for j in range(i + 1, k):
            if P[i]["team"] == P[j]["team"]:
                R[i, j] = R[j, i] = CORR.get((P[i]["role"], P[j]["role"]), 0.0)
    ev, V = np.linalg.eigh(R)
    Rp = R
    if ev.min() < 1e-8:
        Rp = V @ np.diag(np.clip(ev, 1e-8, None)) @ V.T
        s = np.sqrt(np.diag(Rp))
        Rp = Rp / np.outer(s, s)
    L = np.linalg.cholesky(Rp)
    rng = np.random.default_rng(seed)
    Z = (L @ rng.standard_normal((k, N))).T
    Uc = np.clip(0.5 * (1.0 + _erf(Z / sqrt(2.0))), 1e-6, 1 - 1e-6)
    Ui = rng.random((N, k))
    S = np.empty_like(Uc)
    Si = np.empty_like(Ui)
    for i, p in enumerate(P):
        S[:, i] = np.quantile(p["w"], Uc[:, i])
        Si[:, i] = np.quantile(p["w"], Ui[:, i])
    return R, S, Si

def report(P, R, S, Si, label):
    print("\n=== %s ===" % label)
    C2 = np.corrcoef(S.T)
    hit = False
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            if abs(R[i, j]) > 0.01:
                hit = True
                print("  %-20s / %-20s  target %+.3f  realized %+.3f"
                      % (P[i]["name"], P[j]["name"], R[i, j], C2[i, j]))
    if not hit:
        print("  (no correlated pairs)")
    t, u = S.sum(axis=1), Si.sum(axis=1)
    print("                  mean     sd    p10    p90")
    print("  correlated    %6.1f %6.1f %6.1f %6.1f"
          % (t.mean(), t.std(), np.percentile(t, 10), np.percentile(t, 90)))
    print("  independent   %6.1f %6.1f %6.1f %6.1f"
          % (u.mean(), u.std(), np.percentile(u, 10), np.percentile(u, 90)))
    print("  delta:  mean %+.2f   sd %+.2f" % (t.mean() - u.mean(), t.std() - u.std()))

print("=== FINDING A REAL QB STACK TO TEST THE COPULA ===")
stack = None
for _, q in D[(D["pos_abb"] == "QB") & (D["pos_rank"] == 1)].iterrows():
    tm = q["team"]
    w1 = D[(D["team"] == tm) & (D["pos_abb"] == "WR") & (D["pos_rank"] == 1)]
    t1 = D[(D["team"] == tm) & (D["pos_abb"] == "TE") & (D["pos_rank"] == 1)]
    if not len(w1) or not len(t1):
        continue
    nm = [q["player_name"], w1.iloc[0]["player_name"], t1.iloc[0]["player_name"]]
    if min(len(wk(norm(x))) for x in nm) >= 20:
        stack = nm
        break

if stack:
    print("  using %s + %s + %s" % tuple(stack))
    Ps = build(stack)
    Rs, Ss, Sis = run(Ps)
    report(Ps, Rs, Ss, Sis, "STACK TEST")
else:
    print("  no qualifying stack found")

ROSTER = ["Caleb Williams", "Omarion Hampton", "TreVeyon Henderson",
          "Jaxon Smith-Njigba", "George Pickens", "Kyle Pitts",
          "Tee Higgins", "Rico Dowdle", "Josh Downs"]
print("\n=== YOUR LINEUP ===")
Pr = build(ROSTER)
Rr, Sr, Sir = run(Pr)
report(Pr, Rr, Sr, Sir, "YOUR LINEUP")
np.save("sim_weekly.npy", Sr)
print("\nSaved sim_weekly.npy")
