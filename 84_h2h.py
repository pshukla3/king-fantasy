import re, numpy as np, pandas as pd
from math import erf, sqrt
import nflreadpy as nfl

N = 20000
FIX = {"LAR": "LA", "JAC": "JAX", "AZ": "ARI", "WSH": "WAS"}
def fx(t): return FIX.get(str(t), str(t))

MINE = ["Caleb Williams", "Omarion Hampton", "Bhayshul Tuten",
        "Jaxon Smith-Njigba", "Tee Higgins", "Kyle Pitts",
        "George Pickens", "TreVeyon Henderson"]
HIS = ["Joe Burrow", "Kyren Williams", "Josh Jacobs",
       "Amon-Ra St. Brown", "A.J. Brown", "George Kittle",
       "David Montgomery", "Jameson Williams"]
MY_FLAT = [("Harrison Butker K", 8.08), ("SEA DST", 7.69)]
HIS_FLAT = [("T. Smack K", 6.39), ("DET DST", 6.44)]

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
H = H[H["season"] >= 2023].copy()
PC = "fantasy_points_ppr"
D = pd.read_csv("depth_latest.csv", low_memory=False)
B = pd.read_csv("board_situational.csv", low_memory=False)
TCC = pd.read_csv("teammate_corr.csv")
OCC = pd.read_csv("opponent_corr.csv")
try:
    NV = pd.read_csv("news_overrides_v3.csv")
except Exception:
    NV = pd.DataFrame(columns=["player", "points_mult"])

CORR, OPPC = {}, {}
for _, r in TCC.iterrows():
    a, b = [x.strip() for x in str(r["pair"]).split("/")]
    CORR[(a, b)] = float(r["r"]); CORR[(b, a)] = float(r["r"])
for _, r in OCC.iterrows():
    if abs(float(r["r"])) >= 0.05:
        OPPC[(str(r["mine"]), str(r["theirs"]))] = float(r["r"])

def norm(s): return re.sub(r"[^a-z]", "", str(s).lower())
D["k_"] = D["player_name"].map(norm)
H["k_"] = H["player_display_name"].map(norm)
B["k_"] = B["player_name"].map(norm)
NV["k_"] = NV["player"].map(norm) if len(NV) else []
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
            print("  SKIP %-22s depth=%d weeks=%d" % (nm, len(d), len(w)))
            continue
        r0 = d.sort_values("pos_rank").iloc[0]
        bb = B[B["k_"] == n]
        proj = float(bb["proj"].iloc[0]) if len(bb) else float(np.mean(w))
        pm = 1.0
        if len(NV):
            hit = NV[NV["k_"] == n]
            if len(hit):
                pm = float(hit["points_mult"].iloc[0])
        proj *= pm
        w = np.sort(w)
        scale = proj / max(w.mean(), 0.01)
        out.append({"nm": nm, "tm": fx(r0["team"]), "side": tag,
                    "role": "%s%d" % (r0["pos_abb"], int(r0["pos_rank"])),
                    "w": w * scale, "raw": w.mean(), "proj": proj,
                    "sc": scale, "pm": pm})
    return out

P = mk(MINE, "ME") + mk(HIS, "HIM")
print("\n=== LINEUPS  (proj = model ppg after injury multiplier) ===")
print("  side player                 tm   role   rawMean   proj  rescale  pMlt")
for p in P:
    print("  %-4s %-22s %-4s %-5s %7.1f %6.1f %8.2f %5.2f"
          % (p["side"], p["nm"], p["tm"], p["role"], p["raw"], p["proj"], p["sc"], p["pm"]))

k = len(P)
R = np.eye(k)
links = []
for i in range(k):
    for j in range(i + 1, k):
        a, b = P[i], P[j]
        v = 0.0; why = ""
        if a["tm"] == b["tm"]:
            v = CORR.get((a["role"], b["role"]), 0.0); why = "teammates"
        elif OPP.get(a["tm"]) == b["tm"]:
            v = OPPC.get((a["role"], b["role"]), 0.0); why = "same game"
        if abs(v) > 0.01:
            R[i, j] = R[j, i] = v
            links.append((a, b, v, why))

print("\n=== CORRELATED PAIRS IN THIS MATCHUP ===")
if not links:
    print("  none")
for a, b, v, why in sorted(links, key=lambda x: -abs(x[2])):
    cross = "ACROSS ROSTERS" if a["side"] != b["side"] else "same roster"
    print("  %-20s(%s) / %-20s(%s)  r %+.3f  %s, %s"
          % (a["nm"], a["side"], b["nm"], b["side"], v, why, cross))

ev, V = np.linalg.eigh(R)
Rp = R
if ev.min() < 1e-8:
    Rp = V @ np.diag(np.clip(ev, 1e-8, None)) @ V.T
    s = np.sqrt(np.diag(Rp)); Rp = Rp / np.outer(s, s)
L = np.linalg.cholesky(Rp)
rng = np.random.default_rng(11)
Z = (L @ rng.standard_normal((k, N))).T
Uc = np.clip(0.5 * (1.0 + _erf(Z / sqrt(2.0))), 1e-6, 1 - 1e-6)
Ui = rng.random((N, k))
SC = np.empty_like(Uc); SI = np.empty_like(Ui)
for i, p in enumerate(P):
    SC[:, i] = np.quantile(p["w"], Uc[:, i])
    SI[:, i] = np.quantile(p["w"], Ui[:, i])

me = np.array([i for i, p in enumerate(P) if p["side"] == "ME"])
him = np.array([i for i, p in enumerate(P) if p["side"] == "HIM"])
myflat = sum(v for _, v in MY_FLAT)
hisflat = sum(v for _, v in HIS_FLAT)

for lbl, M in [("CORRELATED", SC), ("independent", SI)]:
    a = M[:, me].sum(axis=1) + myflat
    b = M[:, him].sum(axis=1) + hisflat
    d = a - b
    print("\n=== %s ===" % lbl)
    print("  you    mean %6.1f  sd %5.1f   p10 %6.1f  p90 %6.1f"
          % (a.mean(), a.std(), np.percentile(a, 10), np.percentile(a, 90)))
    print("  him    mean %6.1f  sd %5.1f   p10 %6.1f  p90 %6.1f"
          % (b.mean(), b.std(), np.percentile(b, 10), np.percentile(b, 90)))
    print("  margin mean %+6.1f  sd %5.1f" % (d.mean(), d.std()))
    print("  YOUR WIN PROBABILITY: %.1f%%" % (100.0 * (d > 0).mean()))

print("\n  K/DST added as fixed constants, NOT simulated:")
for n_, v in MY_FLAT + HIS_FLAT:
    print("    %-18s %5.2f" % (n_, v))
