import re, numpy as np, pandas as pd
from math import erf, sqrt
import nflreadpy as nfl

N = 10000
PLAYOFF = 6

L = pd.read_csv("league_week1.csv")
S = pd.read_csv("league_schedule.csv")
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

SC = nfl.load_schedules(seasons=[2026])
SC = SC.to_pandas() if hasattr(SC, "to_pandas") else SC
SC = SC[SC["week"] == 1]
OPP = {}
for _, r in SC.iterrows():
    OPP[fx(r["home_team"])] = fx(r["away_team"])
    OPP[fx(r["away_team"])] = fx(r["home_team"])

POOL = {}
for pz in ["QB", "RB", "WR", "TE"]:
    POOL[pz] = np.sort(H[H["position"] == pz][PC].dropna().values)

P = []
FLAT = {}
BASE = {}
OFF = ["QB", "RB", "WR", "TE"]
for _, r in L.iterrows():
    tm = r["team"]
    FLAT.setdefault(tm, 0.0)
    BASE.setdefault(tm, 0.0)
    if r["kind"] == "flat":
        FLAT[tm] += float(r["proj"])
        continue
    n = norm(r["player"])
    d = D[D["k_"].str.contains(n, na=False)]
    d = d[d["pos_abb"].isin(OFF)]
    if not len(d):
        FLAT[tm] += float(r["proj"])
        continue
    w = H[H["k_"] == n][PC].dropna().values
    if len(w) < 8:
        w = H[H["k_"].str.startswith(n, na=False)][PC]
        w = w.dropna().values
    if len(w) < 8:
        w = POOL[str(r["pos"])]
    r0 = d.sort_values("pos_rank").iloc[0]
    w = np.sort(w)
    sc = float(r["proj"]) / max(w.mean(), 0.01)
    BASE[tm] += float(r["proj"])
    P.append({"nm": r["player"], "own": tm,
              "tm": fx(r0["team"]),
              "role": "%s%d" % (r0["pos_abb"], int(r0["pos_rank"])),
              "w": w * sc})
print("skill players: %d" % len(P))

k = len(P)
R = np.eye(k)
nlink = 0
for i in range(k):
    for j in range(i + 1, k):
        a = P[i]
        b = P[j]
        v = 0.0
        if a["tm"] == b["tm"]:
            v = CORR.get((a["role"], b["role"]), 0.0)
        elif OPP.get(a["tm"]) == b["tm"]:
            v = OPPC.get((a["role"], b["role"]), 0.0)
        if abs(v) > 0.01:
            R[i, j] = v
            R[j, i] = v
            nlink += 1
print("correlated pairs: %d" % nlink)

ev, V = np.linalg.eigh(R)
if ev.min() < 1e-8:
    R = V @ np.diag(np.clip(ev, 1e-8, None)) @ V.T
    s = np.sqrt(np.diag(R))
    R = R / np.outer(s, s)
CH = np.linalg.cholesky(R)

TEAMS = sorted(FLAT)
IDX = {}
for t in TEAMS:
    IDX[t] = [i for i, p in enumerate(P) if p["own"] == t]
TGT = {}
for _, r in S.iterrows():
    TGT[(int(r["week"]), r["home"])] = float(r["proj_home"])
    TGT[(int(r["week"]), r["away"])] = float(r["proj_away"])

rng = np.random.default_rng(2026)
WN = {t: np.zeros(N) for t in TEAMS}
PF = {t: np.zeros(N) for t in TEAMS}
WKS = sorted(S["week"].unique())
print("simulating %d weeks x %d seasons..." % (len(WKS), N))

for wk in WKS:
    Z = (CH @ rng.standard_normal((k, N))).T
    U = 0.5 * (1.0 + _erf(Z / sqrt(2.0)))
    U = np.clip(U, 1e-6, 1 - 1e-6)
    X = np.empty_like(U)
    for i, p in enumerate(P):
        X[:, i] = np.quantile(p["w"], U[:, i])
    TS = {}
    for t in TEAMS:
        raw = X[:, IDX[t]].sum(axis=1)
        tgt = TGT[(wk, t)] - FLAT[t]
        TS[t] = raw * (tgt / max(BASE[t], 0.01)) + FLAT[t]
        PF[t] += TS[t]
    for _, r in S[S["week"] == wk].iterrows():
        a = TS[r["home"]]
        b = TS[r["away"]]
        WN[r["home"]] += (a > b)
        WN[r["away"]] += (b > a)

M = np.stack([WN[t] for t in TEAMS], axis=1)
F = np.stack([PF[t] for t in TEAMS], axis=1)
key = M + F * 1e-6
order = np.argsort(-key, axis=1)
POS = np.empty_like(order)
ar = np.arange(len(TEAMS))
for s in range(N):
    POS[s, order[s]] = ar
made = (POS < PLAYOFF).mean(axis=0)
first = (POS == 0).mean(axis=0)

rows = []
for i, t in enumerate(TEAMS):
    rows.append((M[:, i].mean(), t, M[:, i].std(),
                 F[:, i].mean(), 100 * made[i], 100 * first[i]))
rows.sort(reverse=True)
print("\n%s" % ("=" * 66))
print("PROJECTED FINAL STANDINGS  (%d simulated seasons)" % N)
print("=" * 66)
print("  rk team       W- L    sd     PF     playoff%   1seed%")
print("  " + "-" * 60)
for i, (w, t, sd, pf, mk, f1) in enumerate(rows, 1):
    print("  %2d %-9s %4.1f-%4.1f  %.1f  %6.0f     %5.1f%%   %5.1f%%"
          % (i, t, w, len(WKS) - w, sd, pf, mk, f1))
print("\n  playoff cut = top %d" % PLAYOFF)
