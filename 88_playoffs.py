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

ev, V = np.linalg.eigh(R)
if ev.min() < 1e-8:
    R = V @ np.diag(np.clip(ev, 1e-8, None)) @ V.T
    sd = np.sqrt(np.diag(R))
    R = R / np.outer(sd, sd)
CH = np.linalg.cholesky(R)

TEAMS = sorted(FLAT)
NT = len(TEAMS)
IDX = {}
for t in TEAMS:
    IDX[t] = [i for i, p in enumerate(P) if p["own"] == t]
TGT = {}
for _, r in S.iterrows():
    TGT[(int(r["week"]), r["home"])] = float(r["proj_home"])
    TGT[(int(r["week"]), r["away"])] = float(r["proj_away"])

HEAL = {}
for t in TEAMS:
    HEAL[t] = sum(TGT[(w, t)] for w in [1, 2, 3, 4]) / 4.0
print("\nplayoff baseline = wk1-4 mean (bye-free):")
for t in sorted(HEAL, key=lambda x: -HEAL[x]):
    print("  %-8s %6.1f" % (t, HEAL[t]))

rng = np.random.default_rng(2026)

def draw(target):
    Z = (CH @ rng.standard_normal((k, N))).T
    U = 0.5 * (1.0 + _erf(Z / sqrt(2.0)))
    U = np.clip(U, 1e-6, 1 - 1e-6)
    X = np.empty_like(U)
    for i, p in enumerate(P):
        X[:, i] = np.quantile(p["w"], U[:, i])
    out = {}
    for t in TEAMS:
        raw = X[:, IDX[t]].sum(axis=1)
        tg = target[t] - FLAT[t]
        out[t] = raw * (tg / max(BASE[t], 0.01)) + FLAT[t]
    return out

WN = {t: np.zeros(N) for t in TEAMS}
PF = {t: np.zeros(N) for t in TEAMS}
WKS = sorted(S["week"].unique())
print("\nsimulating %d weeks + 3 playoff rounds..." % len(WKS))
for wk in WKS:
    TS = draw({t: TGT[(wk, t)] for t in TEAMS})
    for t in TEAMS:
        PF[t] += TS[t]
    for _, r in S[S["week"] == wk].iterrows():
        WN[r["home"]] += (TS[r["home"]] > TS[r["away"]])
        WN[r["away"]] += (TS[r["away"]] > TS[r["home"]])

D15 = draw(HEAL)
D16 = draw(HEAL)
D17 = draw(HEAL)
A15 = np.stack([D15[t] for t in TEAMS], axis=1)
A16 = np.stack([D16[t] for t in TEAMS], axis=1)
A17 = np.stack([D17[t] for t in TEAMS], axis=1)

M = np.stack([WN[t] for t in TEAMS], axis=1)
F = np.stack([PF[t] for t in TEAMS], axis=1)
order = np.argsort(-(M + F * 1e-6), axis=1)
POS = np.empty_like(order)
ar = np.arange(NT)
for s in range(N):
    POS[s, order[s]] = ar

champ = np.zeros(NT)
fin = np.zeros(NT)
semi = np.zeros(NT)
tbw = np.zeros(NT)
lastp = np.zeros(NT)
bye = np.zeros(NT)

for s in range(N):
    o = order[s]
    s1, s2, s3, s4, s5, s6 = o[0], o[1], o[2], o[3], o[4], o[5]
    s7, s8, s9, s10 = o[6], o[7], o[8], o[9]
    bye[s1] += 1
    bye[s2] += 1
    w36 = s3 if A15[s, s3] > A15[s, s6] else s6
    w45 = s4 if A15[s, s4] > A15[s, s5] else s5
    if POS[s, w36] > POS[s, w45]:
        lo, hi = w36, w45
    else:
        lo, hi = w45, w36
    semi[lo] += 1
    semi[hi] += 1
    a = s1 if A16[s, s1] > A16[s, lo] else lo
    b = s2 if A16[s, s2] > A16[s, hi] else hi
    fin[a] += 1
    fin[b] += 1
    ch = a if A17[s, a] > A17[s, b] else b
    champ[ch] += 1
    t1 = s7 if A15[s, s7] > A15[s, s10] else s10
    t2 = s8 if A15[s, s8] > A15[s, s9] else s9
    tbw[t1 if A16[s, t1] > A16[s, t2] else t2] += 1
    l1 = s10 if t1 == s7 else s7
    l2 = s9 if t2 == s8 else s8
    lastp[l1 if A16[s, l1] < A16[s, l2] else l2] += 1

rows = []
for i, t in enumerate(TEAMS):
    rows.append((100 * champ[i] / N, t, M[:, i].mean(), M[:, i].std(),
                 F[:, i].mean(), 100 * (POS[:, i] < 6).mean(),
                 100 * bye[i] / N, 100 * fin[i] / N,
                 100 * tbw[i] / N, 100 * lastp[i] / N))
rows.sort(reverse=True)
print("\n%s" % ("=" * 74))
print("FULL SEASON + PLAYOFFS   (%d simulated seasons)" % N)
print("=" * 74)
print("  team       W -  L    PF    make%  bye%  final%  CHAMP%")
print("  " + "-" * 62)
for c, t, w, sd, pf, mkp, byp, fnp, tw, lp in rows:
    print("  %-8s %4.1f-%4.1f %5.0f   %5.1f %5.1f  %5.1f   %5.1f%%"
          % (t, w, len(WKS) - w, pf, mkp, byp, fnp, c))
print("\n  TOILET BOWL (seeds 7-10)")
print("  team       win%   LAST PLACE%")
for c, t, w, sd, pf, mkp, byp, fnp, tw, lp in sorted(rows, key=lambda x: -x[8]):
    if tw > 0.5 or lp > 0.5:
        print("  %-8s %5.1f%%      %5.1f%%" % (t, tw, lp))
