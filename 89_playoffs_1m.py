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

import time

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
    sdv = np.sqrt(np.diag(R))
    R = R / np.outer(sdv, sdv)
CHOL = np.linalg.cholesky(R)

for p in P:
    p["g"] = np.linspace(0.0, 1.0, len(p["w"]))

TEAMS = sorted(FLAT)
NT = len(TEAMS)
TI = {t: i for i, t in enumerate(TEAMS)}
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

def ncdf(z):
    t = 1.0 / (1.0 + 0.2316419 * np.abs(z))
    d = 0.3989422804014327 * np.exp(-0.5 * z * z)
    q = 0.319381530 + t * (-0.356563782 + t * (
        1.781477937 + t * (-1.821255978 + t * 1.330274429)))
    q = d * t * q
    return np.where(z >= 0.0, 1.0 - q, q)

rng = np.random.default_rng(2026)

def draw(target, n):
    Z = (CHOL @ rng.standard_normal((k, n))).T
    U = np.clip(ncdf(Z), 1e-9, 1.0 - 1e-9)
    X = np.empty_like(U)
    for i, p in enumerate(P):
        X[:, i] = np.interp(U[:, i], p["g"], p["w"])
    out = {}
    for t in TEAMS:
        raw = X[:, IDX[t]].sum(axis=1)
        tg = target[t] - FLAT[t]
        out[t] = raw * (tg / max(BASE[t], 0.01)) + FLAT[t]
    return out

NSIM = 1000000
CS = 25000
NCH = NSIM // CS
ix = np.arange(CS)

WKS = sorted(S["week"].unique())
GM = []
for wk in WKS:
    g = S[S["week"] == wk]
    GM.append((wk, [(r["home"], r["away"]) for _, r in g.iterrows()]))

sW = np.zeros(NT)
sW2 = np.zeros(NT)
sPF = np.zeros(NT)
cMk = np.zeros(NT)
cBy = np.zeros(NT)
cFn = np.zeros(NT)
cCh = np.zeros(NT)
cTb = np.zeros(NT)
cLs = np.zeros(NT)

print("\n%d sims  =  %d chunks x %d" % (NSIM, NCH, CS))
t0 = time.time()
for ch in range(NCH):
    WN = np.zeros((CS, NT))
    PFc = np.zeros((CS, NT))
    for wk, gs in GM:
        TS = draw({t: TGT[(wk, t)] for t in TEAMS}, CS)
        for t in TEAMS:
            PFc[:, TI[t]] += TS[t]
        for h, aw in gs:
            WN[:, TI[h]] += (TS[h] > TS[aw])
            WN[:, TI[aw]] += (TS[aw] > TS[h])
    order = np.argsort(-(WN + PFc * 1e-6), axis=1)
    D1 = draw(HEAL, CS)
    D2 = draw(HEAL, CS)
    D3 = draw(HEAL, CS)
    B1 = np.take_along_axis(
        np.stack([D1[t] for t in TEAMS], axis=1), order, axis=1)
    B2 = np.take_along_axis(
        np.stack([D2[t] for t in TEAMS], axis=1), order, axis=1)
    B3 = np.take_along_axis(
        np.stack([D3[t] for t in TEAMS], axis=1), order, axis=1)
    w36 = np.where(B1[:, 2] > B1[:, 5], 2, 5)
    w45 = np.where(B1[:, 3] > B1[:, 4], 3, 4)
    lo = np.maximum(w36, w45)
    hi = np.minimum(w36, w45)
    sa = np.where(B2[:, 0] > B2[ix, lo], 0, lo)
    sb = np.where(B2[:, 1] > B2[ix, hi], 1, hi)
    sc = np.where(B3[ix, sa] > B3[ix, sb], sa, sb)
    t1 = np.where(B1[:, 6] > B1[:, 9], 6, 9)
    t2 = np.where(B1[:, 7] > B1[:, 8], 7, 8)
    tw = np.where(B2[ix, t1] > B2[ix, t2], t1, t2)
    l1 = 15 - t1
    l2 = 15 - t2
    lz = np.where(B2[ix, l1] < B2[ix, l2], l1, l2)
    sW += WN.sum(axis=0)
    sW2 += (WN * WN).sum(axis=0)
    sPF += PFc.sum(axis=0)
    cMk += np.bincount(order[:, :6].ravel(), minlength=NT)
    cBy += np.bincount(order[:, :2].ravel(), minlength=NT)
    cFn += np.bincount(order[ix, sa], minlength=NT)
    cFn += np.bincount(order[ix, sb], minlength=NT)
    cCh += np.bincount(order[ix, sc], minlength=NT)
    cTb += np.bincount(order[ix, tw], minlength=NT)
    cLs += np.bincount(order[ix, lz], minlength=NT)
    if (ch + 1) % 5 == 0 or ch == 0:
        el = time.time() - t0
        eta = el / (ch + 1) * (NCH - ch - 1)
        print("  chunk %2d/%d   %5.0fs elapsed   ~%.0fs left"
              % (ch + 1, NCH, el, eta))

mW = sW / NSIM
sdW = np.sqrt(np.maximum(sW2 / NSIM - mW * mW, 0.0))
mPF = sPF / NSIM
se = 100.0 * np.sqrt(
    np.maximum(cCh / NSIM * (1 - cCh / NSIM), 0.0) / NSIM)

rows = []
for i, t in enumerate(TEAMS):
    rows.append((100 * cCh[i] / NSIM, t, mW[i], sdW[i], mPF[i],
                 100 * cMk[i] / NSIM, 100 * cBy[i] / NSIM,
                 100 * cFn[i] / NSIM, 100 * cTb[i] / NSIM,
                 100 * cLs[i] / NSIM, se[i]))
rows.sort(reverse=True)

print("\n%s" % ("=" * 76))
print("FULL SEASON + PLAYOFFS   (%d simulated seasons)" % NSIM)
print("=" * 76)
print("  team       W -  L    PF    make%  bye%  final%   CHAMP% +/- 95%")
print("  " + "-" * 68)
for c, t, w, sd, pf, mk, by, fn, tb, ls, e in rows:
    print("  %-8s %4.1f-%4.1f %5.0f   %5.1f %5.1f  %5.1f   %6.2f%% +-%.2f"
          % (t, w, len(WKS) - w, pf, mk, by, fn, c, 1.96 * e))
print("\n  TOILET BOWL (seeds 7-10)")
print("  team       win%    LAST PLACE%")
for c, t, w, sd, pf, mk, by, fn, tb, ls, e in sorted(
        rows, key=lambda x: -x[9]):
    if tb > 0.5 or ls > 0.5:
        print("  %-8s %6.2f%%      %6.2f%%" % (t, tb, ls))

print("\n  checksums (should be 100 / 600 / 200 / 100):")
print("    champ  %7.2f" % (100 * cCh.sum() / NSIM))
print("    make   %7.2f" % (100 * cMk.sum() / NSIM))
print("    bye    %7.2f" % (100 * cBy.sum() / NSIM))
print("    last   %7.2f" % (100 * cLs.sum() / NSIM))
print("\n  total runtime %.0fs" % (time.time() - t0))
