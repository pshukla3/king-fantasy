import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(d):
    return d.to_pandas() if hasattr(d, "to_pandas") else d

S = pd.read_csv("pos_season_panel.csv", low_memory=False)
PLR = pl(nfl.load_players())
idc = "gsis_id" if "gsis_id" in PLR.columns else "player_id"
PLR = PLR[[idc, "draft_pick", "rookie_season"]].rename(
    columns={idc: "player_id"}).drop_duplicates("player_id")
H = S.merge(PLR, on="player_id", how="left")
H = H[H["season"] == H["rookie_season"]].copy()
SHC = {"RB": "opp_share", "WR": "tar_share",
       "TE": "tar_share"}

print("=== EFFICIENCY: RATIO vs FITTED LINE ===")
print("  ratio forces through zero and is dominated")
print("  by tiny-share rookies. a fit does not.\n")
print("  %-4s %8s %9s %9s %9s"
      % ("pos", "ratio", "intercept", "slope", "fit MAE"))
print("  " + "-" * 46)
EFF2 = {}
CAP = {}
for p in ["RB", "WR", "TE"]:
    c = SHC[p]
    d = H[(H["position"] == p) & H[c].notna()
          & (H[c] > 0)]
    ratio = float((d["ppg"] / d[c]).median())
    b = d[c].cov(d["ppg"]) / d[c].var()
    a = d["ppg"].mean() - b * d[c].mean()
    mae = ((a + b * d[c]) - d["ppg"]).abs().mean()
    EFF2[p] = (a, b)
    CAP[p] = float(d[c].quantile(0.95))
    print("  %-4s %8.2f %9.3f %9.2f %9.3f"
          % (p, ratio, a, b, mae))
    print("       share 0.10 -> %.2f | 0.25 -> %.2f"
          " | 0.40 -> %.2f ppg"
          % (a + b * 0.10, a + b * 0.25, a + b * 0.40))

print("\n=== HISTORICAL ROOKIE SHARE CEILING ===")
print("  no rookie gets projected above what the 95th")
print("  percentile rookie has actually earned\n")
for p in ["RB", "WR", "TE"]:
    c = SHC[p]
    d = H[(H["position"] == p) & H[c].notna()]
    print("  %-4s p50 %.3f | p90 %.3f | p95 %.3f | max %.3f"
          % (p, d[c].median(), d[c].quantile(0.90),
             CAP[p], d[c].max()))
np.save("rookie_cap.npy",
        np.array([CAP["RB"], CAP["WR"], CAP["TE"]]))

print("\n" + "=" * 58)
print("=== REBUILD: DEPTH CAN ONLY DEMOTE ===")
DEPTH = {1: 1.00, 2: 0.72, 3: 0.45, 4: 0.28}
O = pd.read_csv("rookie_proj_2026.csv")
out = []
for _, r in O.iterrows():
    p = r["ps"]
    dco = r["dco"]
    dm = DEPTH.get(int(dco), 0.20) if dco == dco else 0.55
    sh = min(r["base"] * dm, CAP[p], max(r["open"], 0.05))
    a, b = EFF2[p]
    out.append({"nm": r["nm"], "ps": p, "tm": r["tm"],
                "pick": r["pick"], "dco": dco,
                "share": round(sh, 4),
                "proj": round(max(a + b * sh, 0.3), 2),
                "was": r["proj"], "cur": r["cur"]})
N = pd.DataFrame(out).sort_values("proj", ascending=False)
N.to_csv("rookie_proj_2026.csv", index=False)

print("  %-22s %-3s %-4s %5s %4s %6s %6s %6s"
      % ("player", "ps", "tm", "pick", "dep",
         "share", "NEW", "was"))
print("  " + "-" * 62)
for _, r in N.head(24).iterrows():
    print("  %-22s %-3s %-4s %5s %4s %6.3f %6.2f %6.2f"
          % (str(r["nm"])[:22], r["ps"], r["tm"],
             "UDFA" if r["pick"] >= 260
             else "%.0f" % r["pick"],
             "--" if r["dco"] != r["dco"]
             else "%.0f" % r["dco"],
             r["share"], r["proj"], r["was"]))

print("\n=== SANITY vs THE VETERAN BOARD ===")
try:
    V = pd.read_csv("proj_2026.csv")
    for p in ["RB", "WR", "TE"]:
        v = V[V["position"] == p]["proj"]
        n = N[N["ps"] == p]["proj"]
        top = float(n.max())
        rk = int((v > top).sum()) + 1
        print("  %-4s best rookie %.2f ppg -> would rank"
              " %s%d among returning players"
              % (p, top, p, rk))
except IOError:
    print("  proj_2026.csv not found")
print("\n  a rookie inside the top 5 at his position is")
print("  possible but rare - if you see one, look at him")
