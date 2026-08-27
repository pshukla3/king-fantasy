import re, numpy as np, pandas as pd
from math import erf, sqrt
import nflreadpy as nfl

N = 20000
GAMES = [("VS", "Raachit"), ("Nemai", "Bryson"),
         ("Alex", "Charlie"), ("Daichi", "Nabeel"),
         ("Gurman", "Benji")]

L = pd.read_csv("league_week1.csv")
H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
H = H[H["season"] >= 2023].copy()
PC = "fantasy_points_ppr"
D = pd.read_csv("depth_latest.csv", low_memory=False)
TCC = pd.read_csv("teammate_corr.csv")
OCC = pd.read_csv("opponent_corr.csv")

FIX = {"LAR": "LA", "JAC": "JAX", "AZ": "ARI", "WSH": "WAS"}

def fx(t):
    return FIX.get(str(t), str(t))

def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

CORR = {}
OPPC = {}
for _, r in TCC.iterrows():
    a, b = [x.strip() for x in str(r["pair"]).split("/")]
    CORR[(a, b)] = float(r["r"])
    CORR[(b, a)] = float(r["r"])
for _, r in OCC.iterrows():
    if abs(float(r["r"])) >= 0.05:
        OPPC[(str(r["mine"]), str(r["theirs"]))] = float(r["r"])

D["k_"] = D["player_name"].map(norm)
H["k_"] = H["player_display_name"].map(norm)
_erf = np.vectorize(erf)

S = nfl.load_schedules(seasons=[2026])
S = S.to_pandas() if hasattr(S, "to_pandas") else S
S = S[S["week"] == 1]
OPP = {}
for _, r in S.iterrows():
    OPP[fx(r["home_team"])] = fx(r["away_team"])
    OPP[fx(r["away_team"])] = fx(r["home_team"])

POOL = {}
for pz in ["QB", "RB", "WR", "TE"]:
    POOL[pz] = np.sort(H[H["position"] == pz][PC].dropna().values)

print("=== BUILDING SKILL PLAYERS ===")
P = []
FLAT = {}
OFF = ["QB", "RB", "WR", "TE"]
for _, r in L.iterrows():
    tm = r["team"]
    FLAT.setdefault(tm, 0.0)
    if r["kind"] == "flat":
        FLAT[tm] += float(r["proj"])
        continue
    n = norm(r["player"])
    d = D[D["k_"].str.contains(n, na=False)]
    d = d[d["pos_abb"].isin(OFF)]
    if not len(d):
        FLAT[tm] += float(r["proj"])
        print("  NO DEPTH  %s -> flat" % r["player"])
        continue
    w = H[H["k_"] == n][PC].dropna().values
    src = ""
    if len(w) < 8:
        w = POOL[str(r["pos"])]
        src = " <- POOLED shape"
    r0 = d.sort_values("pos_rank").iloc[0]
    w = np.sort(w)
    sc = float(r["proj"]) / max(w.mean(), 0.01)
    P.append({"nm": r["player"], "own": tm,
              "tm": fx(r0["team"]),
              "role": "%s%d" % (r0["pos_abb"], int(r0["pos_rank"])),
              "w": w * sc})
    if src:
        print("  %s%s" % (r["player"], src))

k = len(P)
print("\n  %d skill players + K/DST constants" % k)

R = np.eye(k)
links = []
for i in range(k):
    for j in range(i + 1, k):
        a = P[i]
        b = P[j]
        v = 0.0
        why = ""
        if a["tm"] == b["tm"]:
            v = CORR.get((a["role"], b["role"]), 0.0)
            why = "teammates"
        elif OPP.get(a["tm"]) == b["tm"]:
            v = OPPC.get((a["role"], b["role"]), 0.0)
            why = "same game"
        if abs(v) > 0.01:
            R[i, j] = v
            R[j, i] = v
            links.append((a, b, v, why))

ev, V = np.linalg.eigh(R)
if ev.min() < 1e-8:
    R = V @ np.diag(np.clip(ev, 1e-8, None)) @ V.T
    s = np.sqrt(np.diag(R))
    R = R / np.outer(s, s)
Lc = np.linalg.cholesky(R)
rng = np.random.default_rng(2026)
Z = (Lc @ rng.standard_normal((k, N))).T
U = 0.5 * (1.0 + _erf(Z / sqrt(2.0)))
U = np.clip(U, 1e-6, 1 - 1e-6)
SS = np.empty_like(U)
for i, p in enumerate(P):
    SS[:, i] = np.quantile(p["w"], U[:, i])

TEAM = {}
for t in FLAT:
    idx = [i for i, p in enumerate(P) if p["own"] == t]
    TEAM[t] = SS[:, idx].sum(axis=1) + FLAT[t]

print("\n=== CORRELATED PAIRS (%d total) ===" % len(links))
for a, b, v, why in sorted(links, key=lambda x: -abs(x[2]))[:15]:
    if a["own"] == b["own"]:
        tag = "SAME ROSTER"
    else:
        tag = "%s vs %s" % (a["own"], b["own"])
    print("  %-19s / %-19s %+.3f %s"
          % (a["nm"][:19], b["nm"][:19], v, tag))

print("\n\n=== WEEK 1 RESULTS (%d sims) ===" % N)
for x, y in GAMES:
    a = TEAM[x]
    b = TEAM[y]
    wp = 100.0 * (a > b).mean()
    win = x if wp >= 50 else y
    show = max(wp, 100.0 - wp)
    print("  %-8s %5.1f  -  %5.1f %-8s" % (x, a.mean(), b.mean(), y))
    print("      winner %-8s %.1f%%" % (win, show))

print("\n=== WEEKLY SCORE RANKING ===")
rk = sorted(TEAM.items(), key=lambda kv: -kv[1].mean())
for i, (t, v) in enumerate(rk, 1):
    lo = np.percentile(v, 10)
    hi = np.percentile(v, 90)
    print("  %2d %-8s %6.1f  sd %5.1f  %6.1f - %6.1f"
          % (i, t, v.mean(), v.std(), lo, hi))
np.save("week1_sim.npy", SS)
