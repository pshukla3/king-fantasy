import re, numpy as np, pandas as pd
from math import erf, sqrt
import nflreadpy as nfl

N = 20000
BASE = ["Caleb Williams", "Omarion Hampton", "Bhayshul Tuten",
        "Jaxon Smith-Njigba", "George Pickens", "Tee Higgins", "Kyle Pitts"]
LINEUPS = {
    "A  your actual (Downs)":   BASE + ["Josh Downs"],
    "B  Henderson over Downs":  BASE + ["TreVeyon Henderson"],
    "C  Dowdle over Downs":     BASE + ["Rico Dowdle"],
    "D  Shaheed over Downs":    BASE + ["Rashid Shaheed"],
}
HIS = ["Joe Burrow", "Kyren Williams", "Josh Jacobs", "Amon-Ra St. Brown",
       "A.J. Brown", "George Kittle", "David Montgomery", "Jameson Williams"]
MY_FLAT = 9.71 + 7.00
HIS_FLAT = 6.39 + 7.78

FIX = {"LAR": "LA", "JAC": "JAX", "AZ": "ARI", "WSH": "WAS"}
def fx(t): return FIX.get(str(t), str(t))
def norm(s): return re.sub(r"[^a-z]", "", str(s).lower())

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
H = H[H["season"] >= 2023].copy()
PC = "fantasy_points_ppr"
D = pd.read_csv("depth_latest.csv", low_memory=False)
B = pd.read_csv("board_situational.csv", low_memory=False)
TCC = pd.read_csv("teammate_corr.csv")
OCC = pd.read_csv("opponent_corr.csv")
try:
    NV = pd.read_csv("news_overrides_v3.csv")
    NV["k_"] = NV["player"].map(norm)
except Exception:
    NV = pd.DataFrame(columns=["player", "points_mult", "k_"])

CORR, OPPC = {}, {}
for _, r in TCC.iterrows():
    a, b = [x.strip() for x in str(r["pair"]).split("/")]
    CORR[(a, b)] = float(r["r"]); CORR[(b, a)] = float(r["r"])
for _, r in OCC.iterrows():
    if abs(float(r["r"])) >= 0.05:
        OPPC[(str(r["mine"]), str(r["theirs"]))] = float(r["r"])

D["k_"] = D["player_name"].map(norm)
H["k_"] = H["player_display_name"].map(norm)
B["k_"] = B["player_name"].map(norm)
_erf = np.vectorize(erf)

S = nfl.load_schedules(seasons=[2026])
S = S.to_pandas() if hasattr(S, "to_pandas") else S
S = S[S["week"] == 1]
OPP = {}
for _, r in S.iterrows():
    OPP[fx(r["home_team"])] = fx(r["away_team"])
    OPP[fx(r["away_team"])] = fx(r["home_team"])

def mk(names, tag):
    out = []
    for nm in names:
        n = norm(nm)
        d = D[D["k_"].str.contains(n, na=False) & D["pos_abb"].isin(["QB","RB","WR","TE"])]
        w = H[H["k_"] == n][PC].dropna().values
        if len(w) < 8:
            w = H[H["k_"].str.contains(n, na=False)][PC].dropna().values
        if not len(d) or len(w) < 8:
            print("  SKIP %s (depth=%d weeks=%d)" % (nm, len(d), len(w)))
            continue
        r0 = d.sort_values("pos_rank").iloc[0]
        bb = B[B["k_"] == n]
        proj = float(bb["proj"].iloc[0]) if len(bb) else float(np.mean(w))
        hit = NV[NV["k_"] == n] if len(NV) else []
        if len(hit):
            proj *= float(hit["points_mult"].iloc[0])
        w = np.sort(w)
        out.append({"nm": nm, "tm": fx(r0["team"]), "side": tag,
                    "role": "%s%d" % (r0["pos_abb"], int(r0["pos_rank"])),
                    "w": w * (proj / max(w.mean(), 0.01)), "proj": proj, "n": len(w)})
    return out

THEM = mk(HIS, "HIM")

def go(P, seed=11):
    k = len(P)
    R = np.eye(k); links = []
    for i in range(k):
        for j in range(i + 1, k):
            a, b = P[i], P[j]; v = 0.0
            if a["tm"] == b["tm"]:
                v = CORR.get((a["role"], b["role"]), 0.0)
            elif OPP.get(a["tm"]) == b["tm"]:
                v = OPPC.get((a["role"], b["role"]), 0.0)
            if abs(v) > 0.01:
                R[i, j] = R[j, i] = v
                links.append((a["nm"], b["nm"], v))
    ev, V = np.linalg.eigh(R)
    if ev.min() < 1e-8:
        R = V @ np.diag(np.clip(ev, 1e-8, None)) @ V.T
        s = np.sqrt(np.diag(R)); R = R / np.outer(s, s)
    L = np.linalg.cholesky(R)
    rng = np.random.default_rng(seed)
    Z = (L @ rng.standard_normal((k, N))).T
    U = np.clip(0.5 * (1.0 + _erf(Z / sqrt(2.0))), 1e-6, 1 - 1e-6)
    SS = np.empty_like(U)
    for i, p in enumerate(P):
        SS[:, i] = np.quantile(p["w"], U[:, i])
    me = [i for i, p in enumerate(P) if p["side"] == "ME"]
    him = [i for i, p in enumerate(P) if p["side"] == "HIM"]
    a = SS[:, me].sum(axis=1) + MY_FLAT
    b = SS[:, him].sum(axis=1) + HIS_FLAT
    return a, b, links

print("=== SWAP CANDIDATES ===")
print("  player                 proj    n   sd")
for nm in ["Josh Downs", "TreVeyon Henderson", "Rico Dowdle", "Rashid Shaheed"]:
    p = mk([nm], "ME")
    if p:
        print("  %-22s %5.1f %4d %5.1f" % (nm, p[0]["proj"], p[0]["n"], p[0]["w"].std()))

print("\n=== WIN PROBABILITY BY LINEUP ===")
print("  lineup                     you    sd     him   margin  marg_sd   WIN%")
print("  " + "-" * 66)
best = None
for lbl, names in LINEUPS.items():
    P = mk(names, "ME") + THEM
    a, b, links = go(P)
    d = a - b
    wp = 100.0 * (d > 0).mean()
    print("  %-24s %6.1f %5.1f  %6.1f  %+6.1f   %5.1f   %5.1f%%"
          % (lbl, a.mean(), a.std(), b.mean(), d.mean(), d.std(), wp))
    if best is None or wp > best[1]:
        best = (lbl, wp)

print("\n  best: %s at %.1f%%" % best)
print("\n  se on a 39%% win prob at N=%d is about %.2f pts --" % (N, 100*sqrt(.39*.61/N)))
print("  ignore any gap smaller than roughly 1 point.")
P = mk(LINEUPS["A  your actual (Downs)"], "ME") + THEM
_, _, links = go(P)
print("\n=== CORRELATED PAIRS, YOUR ACTUAL LINEUP ===")
for x, y, v in sorted(links, key=lambda t: -abs(t[2])):
    print("  %-22s / %-22s  r %+.3f" % (x, y, v))
