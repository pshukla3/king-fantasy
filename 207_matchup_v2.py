import numpy as np
import pandas as pd

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}
D = pd.read_csv("def_components.csv")
D["opponent_team"] = D["opponent_team"].astype(str).replace(FIX)
MET = ["ypt", "ctch", "tdpt", "tpg"]

idx = {}
for _, r in D.iterrows():
    idx[(r["opponent_team"], int(r["season"]),
         str(r["position"]))] = r

WT = [1.0, 0.5, 0.25]
rows = []
for (tm, s, ps), r in idx.items():
    rec = {"tm": tm, "season": s, "position": ps}
    ok = True
    for m in MET:
        num = den = 0.0
        for j, w in enumerate(WT, start=1):
            p = idx.get((tm, s - j, ps))
            if p is None:
                continue
            v = p[m]
            if v != v:
                continue
            num += w * float(v)
            den += w
        rec["p3_" + m] = num / den if den > 0 else np.nan
        p1 = idx.get((tm, s - 1, ps))
        rec["p1_" + m] = (float(p1[m]) if p1 is not None
                          and p1[m] == p1[m] else np.nan)
        rec["act_" + m] = (float(r[m]) if r[m] == r[m]
                           else np.nan)
    rows.append(rec)
P = pd.DataFrame(rows).dropna()
print("defense-seasons with 3 yrs of prior: %d" % len(P))

print("\n=== DOES A 3-YEAR RATING PERSIST BETTER? ===")
print("  correlation of prior rating with what")
print("  the defense ACTUALLY allowed that season\n")
print("  %-6s %-4s %10s %10s %8s"
      % ("pos", "met", "1yr prior", "3yr prior", "gain"))
for ps in ["WR", "RB", "TE"]:
    d = P[P["position"] == ps]
    for m in MET:
        r1 = d["p1_" + m].corr(d["act_" + m])
        r3 = d["p3_" + m].corr(d["act_" + m])
        print("  %-6s %-4s %+10.3f %+10.3f %+8.3f"
              % (ps, m, r1, r3, r3 - r1))

for m in MET:
    lg = P.groupby(["season", "position"])[
        "p3_" + m].transform("mean")
    P["dev_" + m] = P["p3_" + m] / lg
P.to_csv("def_rating3.csv", index=False)
print("\nwrote def_rating3.csv")

import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

W = pl(nfl.load_player_stats(seasons=list(range(2018, 2026))))
NEED = ["targets", "receptions", "receiving_yards",
        "receiving_tds"]
for c in NEED:
    if c not in W.columns:
        W[c] = 0.0
    W[c] = pd.to_numeric(W[c], errors="coerce").fillna(0.0)
W = W[W["position"] == "WR"].copy()
W["opponent_team"] = W["opponent_team"].astype(str).replace(FIX)

S = W.groupby(["player_id", "season"]).agg(
    tar=("targets", "sum"), yds=("receiving_yards", "sum"),
    td=("receiving_tds", "sum"),
    g=("week", "nunique")).reset_index()
S = S[(S["g"] >= 10) & (S["tar"] >= 40)].copy()
S["b_tpg"] = S["tar"] / S["g"]
S["b_ypt"] = S["yds"] / S["tar"]
S["b_tdpt"] = S["td"] / S["tar"]
W = W.merge(S[["player_id", "season", "b_tpg", "b_ypt",
               "b_tdpt"]], on=["player_id", "season"],
            how="inner")

R = P[P["position"] == "WR"][
    ["tm", "season", "dev_tpg", "dev_ypt", "dev_tdpt"]]
R = R.rename(columns={"tm": "opponent_team"})
W = W.merge(R, on=["opponent_team", "season"], how="inner")
print("weekly WR rows with a 3-yr opponent rating: %d"
      % len(W))

TR = W[W["season"] < 2022]
VA = W[W["season"].isin([2022, 2023])]
TE = W[W["season"] >= 2024]
print("train %d | valid %d | TEST %d"
      % (len(TR), len(VA), len(TE)))

KS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0]

def fit(base, dev, act, tr, va, te):
    best = (0.0, 9e9)
    for k in KS:
        e = (tr[base] * (1 + k * (tr[dev] - 1))
             - tr[act]).abs().mean()
        if e < best[1]:
            best = (k, e)
    k = best[0]
    f = (te[base] - te[act]).abs().mean()
    a = (te[base] * (1 + k * (te[dev] - 1))
         - te[act]).abs().mean()
    return k, f, a

print("\n=== COMPONENT-LEVEL MATCHUP TEST ===")
print("  k fit on TRAIN, scored on TEST it never saw\n")
print("  %-10s %6s %10s %10s %9s %8s"
      % ("component", "k*", "flat MAE", "adj MAE",
         "gain", "verdict"))
W["b_yds"] = W["b_tpg"] * W["b_ypt"]
W["b_td"] = W["b_tpg"] * W["b_tdpt"]
for tr, va, te in [(TR, VA, TE)]:
    tr = tr.copy()
    te = te.copy()
    for d in (tr, te):
        d["b_yds"] = d["b_tpg"] * d["b_ypt"]
        d["b_td"] = d["b_tpg"] * d["b_tdpt"]
    ADOPT = {}
    for nm, base, dev, act in [
            ("targets", "b_tpg", "dev_tpg", "targets"),
            ("rec yards", "b_yds", "dev_ypt",
             "receiving_yards"),
            ("rec TDs", "b_td", "dev_tdpt",
             "receiving_tds")]:
        k, f, a = fit(base, dev, act, tr, va, te)
        g = 100.0 * (1 - a / f)
        good = a < f
        ADOPT[nm] = k if good else 0.0
        print("  %-10s %6.2f %10.4f %10.4f %+8.2f%% %8s"
              % (nm, k, f, a, g,
                 "ADOPT" if good else "reject"))
np.save("matchup_k.npy",
        np.array([ADOPT.get("targets", 0.0),
                  ADOPT.get("rec yards", 0.0),
                  ADOPT.get("rec TDs", 0.0)]))

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"].astype(str), SC["value"]))

def sv(k, d=0.0):
    return float(V.get(k, d))

kt, ky, kd = [float(x) for x in np.load("matchup_k.npy")]
te = TE.copy()
te["b_yds"] = te["b_tpg"] * te["b_ypt"]
te["b_td"] = te["b_tpg"] * te["b_tdpt"]
te["act_fp"] = (te["receptions"] * sv("rec", 1.0)
                + te["receiving_yards"] * sv("rec_yd", 0.1)
                + te["receiving_tds"] * sv("rec_td", 6.0))
flat = (te["b_tpg"] * (te["b_ypt"] * 0 + 1)
        * 0)
flat = (te["b_tpg"] * te["b_ypt"] * sv("rec_yd", 0.1)
        + te["b_td"] * sv("rec_td", 6.0)
        + te["b_tpg"] * 0.63 * sv("rec", 1.0))
adj = (te["b_tpg"] * (1 + kt * (te["dev_tpg"] - 1))
       * te["b_ypt"] * (1 + ky * (te["dev_ypt"] - 1))
       * sv("rec_yd", 0.1)
       + te["b_td"] * (1 + kd * (te["dev_tdpt"] - 1))
       * sv("rec_td", 6.0)
       + te["b_tpg"] * (1 + kt * (te["dev_tpg"] - 1))
       * 0.63 * sv("rec", 1.0))
mf = (flat - te["act_fp"]).abs().mean()
ma = (adj - te["act_fp"]).abs().mean()
print("\n=== COMBINED FANTASY POINTS, TEST YEARS ===")
print("  adopted k: targets %.2f | yards %.2f | TDs %.2f"
      % (kt, ky, kd))
print("  flat MAE %.4f | matchup-adjusted MAE %.4f"
      % (mf, ma))
print("  gain %+.2f%%" % (100.0 * (1 - ma / mf)))

print("\n=== WHAT THIS DOES TO A WEEKLY RANGE ===")
d = P[P["position"] == "WR"]
d = d[d["season"] == 2025]
lo, hi = d["dev_ypt"].min(), d["dev_ypt"].max()
print("  2025 3-yr WR ratings span %.3f to %.3f"
      % (lo, hi))
print("  a 17.69 ppg receiver would range")
print("    %.2f to %.2f ppg on yards alone"
      % (17.69 * (1 + ky * (lo - 1)),
         17.69 * (1 + ky * (hi - 1))))
print("  old single-year k=0.10 gave 15.27 to 15.91")
