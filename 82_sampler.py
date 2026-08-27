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

ROSTER = ["Caleb Williams", "Omarion Hampton", "TreVeyon Henderson",
          "Jaxon Smith-Njigba", "George Pickens", "Kyle Pitts",
          "Tee Higgins", "Rico Dowdle", "Josh Downs"]

D["k_"] = D["player_name"].map(norm)
H["k_"] = H["player_display_name"].map(norm)
OFF = ["QB", "RB", "WR", "TE"]

P = []
for nm in ROSTER:
    n = norm(nm)
    d = D[D["k_"].str.contains(n, na=False) & D["pos_abb"].isin(OFF)]
    w = H[H["k_"] == n][PC].dropna().values
    if len(w) < 8:
        w = H[H["k_"].str.contains(n, na=False)][PC].dropna().values
    if not len(d) or len(w) < 8:
        print("  SKIP %-22s depth=%d weeks=%d" % (nm, len(d), len(w)))
        continue
    r0 = d.sort_values("pos_rank").iloc[0]
    P.append({"name": nm, "team": r0["team"],
              "role": "%s%d" % (r0["pos_abb"], int(r0["pos_rank"])),
              "w": np.sort(w)})

print("\n=== LINEUP ===")
for p in P:
    print("  %-22s %-4s %-5s  n=%3d  mean %5.1f  sd %5.1f"
          % (p["name"], p["team"], p["role"], len(p["w"]),
             p["w"].mean(), p["w"].std()))

k = len(P)
R = np.eye(k)
for i in range(k):
    for j in range(i + 1, k):
        if P[i]["team"] == P[j]["team"]:
            R[i, j] = R[j, i] = CORR.get((P[i]["role"], P[j]["role"]), 0.0)

ev, V = np.linalg.eigh(R)
if ev.min() < 1e-8:
    R = V @ np.diag(np.clip(ev, 1e-8, None)) @ V.T
    s = np.sqrt(np.diag(R))
    R = R / np.outer(s, s)
L = np.linalg.cholesky(R)

N = 20000
rng = np.random.default_rng(7)
Z = (L @ rng.standard_normal((k, N))).T
_erf = np.vectorize(erf)
Uq = np.clip(0.5 * (1.0 + _erf(Z / sqrt(2.0))), 1e-6, 1 - 1e-6)
S = np.empty_like(Uq)
for i, p in enumerate(P):
    S[:, i] = np.quantile(p["w"], Uq[:, i])

print("\n=== VERIFY: did the copula impose the target correlation? ===")
C2 = np.corrcoef(S.T)
any_ = False
for i in range(k):
    for j in range(i + 1, k):
        if abs(R[i, j]) > 0.01:
            any_ = True
            print("  %-20s / %-20s  target %+.3f  realized %+.3f"
                  % (P[i]["name"], P[j]["name"], R[i, j], C2[i, j]))
if not any_:
    print("  no correlated pairs in this lineup (no QB stacked with his own receivers)")

Si = np.empty_like(S)
for i, p in enumerate(P):
    Si[:, i] = rng.choice(p["w"], N)

tot, ti = S.sum(axis=1), Si.sum(axis=1)
print("\n=== WEEKLY TEAM SCORE, %d simulated weeks ===" % N)
print("                  mean     sd    p10    p50    p90")
print("  correlated    %6.1f %6.1f %6.1f %6.1f %6.1f"
      % (tot.mean(), tot.std(), np.percentile(tot, 10),
         np.percentile(tot, 50), np.percentile(tot, 90)))
print("  independent   %6.1f %6.1f %6.1f %6.1f %6.1f"
      % (ti.mean(), ti.std(), np.percentile(ti, 10),
         np.percentile(ti, 50), np.percentile(ti, 90)))
print("\n  correlation changes the mean by %+.2f and the sd by %+.2f"
      % (tot.mean() - ti.mean(), tot.std() - ti.std()))
np.save("sim_weekly.npy", S)
print("\nSaved sim_weekly.npy")
