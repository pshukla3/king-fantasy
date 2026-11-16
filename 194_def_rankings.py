import pandas as pd
import numpy as np
import nflreadpy as nfl

def pl(d):
    return d.to_pandas() if hasattr(d, "to_pandas") else d

YRS = list(range(2015, 2026))
W = pl(nfl.load_player_stats(seasons=YRS))
print("weekly rows: %d" % len(W))

need = ["opponent_team", "season", "week", "position",
        "targets", "receptions", "receiving_yards",
        "receiving_tds", "carries", "rushing_yards",
        "rushing_tds"]
have = [c for c in need if c in W.columns]
print("columns present: %s" % have)
for c in ["targets", "receptions", "receiving_yards",
          "receiving_tds", "carries", "rushing_yards",
          "rushing_tds"]:
    if c in W.columns:
        W[c] = pd.to_numeric(W[c], errors="coerce").fillna(0)
    else:
        W[c] = 0.0

W = W[W["position"].isin(["WR", "RB", "TE"])]
D = W.groupby(["opponent_team", "season",
               "position"]).agg(
    tar=("targets", "sum"),
    rec=("receptions", "sum"),
    cyd=("receiving_yards", "sum"),
    ctd=("receiving_tds", "sum"),
    car=("carries", "sum"),
    ryd=("rushing_yards", "sum"),
    rtd=("rushing_tds", "sum"),
    g=("week", "nunique")).reset_index()
D = D[D["g"] >= 14]

D["ypt"] = D["cyd"] / D["tar"].replace(0, np.nan)
D["ctch"] = D["rec"] / D["tar"].replace(0, np.nan)
D["tdpt"] = D["ctd"] / D["tar"].replace(0, np.nan)
D["tpg"] = D["tar"] / D["g"]
D["ypc"] = D["ryd"] / D["car"].replace(0, np.nan)
D["rtpc"] = D["rtd"] / D["car"].replace(0, np.nan)
D.to_csv("def_components.csv", index=False)
print("defense-season-position rows: %d" % len(D))

N = D.copy()
N["season"] = N["season"] - 1
REN = {c: c + "_n" for c in
       ["ypt", "ctch", "tdpt", "tpg", "ypc", "rtpc"]}
N = N.rename(columns=REN)
N = N[["opponent_team", "season", "position"]
      + list(REN.values())]
P = D.merge(N, on=["opponent_team", "season", "position"],
            how="inner")
print("\n=== DOES DEFENSIVE RATE PERSIST YEAR TO YEAR? ===")
print("  r above ~0.3 means it is worth using\n")
print("  %-4s %-6s %5s %8s %9s"
      % ("pos", "metric", "n", "r", "verdict"))
print("  " + "-" * 40)
KEEP = []
for pos in ["WR", "RB", "TE"]:
    d = P[P["position"] == pos]
    for m in ["ypt", "ctch", "tdpt", "tpg",
              "ypc", "rtpc"]:
        a, b = d[m], d[m + "_n"]
        ok = a.notna() & b.notna()
        if int(ok.sum()) < 60:
            continue
        r = float(a[ok].corr(b[ok]))
        v = "USABLE" if abs(r) > 0.30 else "noise"
        if abs(r) > 0.30:
            KEEP.append((pos, m, r))
        print("  %-4s %-6s %5d %+8.3f %9s"
              % (pos, m, int(ok.sum()), r, v))

print("\n=== 2025 DEFENSES vs WR, RANKED ===")
d = D[(D["season"] == 2025) & (D["position"] == "WR")]
d = d.sort_values("ypt")
print("  toughest 8 by yards allowed per target:")
for _, r in d.head(8).iterrows():
    print("    %-4s %5.2f ypt | %5.1f%% caught | %5.1f tar/g"
          % (r["opponent_team"], r["ypt"],
             100 * r["ctch"], r["tpg"]))
print("  softest 8:")
for _, r in d.tail(8).iterrows():
    print("    %-4s %5.2f ypt | %5.1f%% caught | %5.1f tar/g"
          % (r["opponent_team"], r["ypt"],
             100 * r["ctch"], r["tpg"]))

print("\n=== SPREAD: HOW BIG IS THE EFFECT AT ALL? ===")
for pos in ["WR", "RB"]:
    d = D[(D["season"] == 2025) & (D["position"] == pos)]
    m = "ypt" if pos == "WR" else "ypc"
    print("  %-4s %s  best %.2f | median %.2f | worst %.2f"
          % (pos, m, d[m].min(), d[m].median(), d[m].max()))
    print("       best-to-worst gap is %.0f%%"
          % (100 * (d[m].max() / d[m].min() - 1)))

print("\n  metrics that survived: %d" % len(KEEP))
for pos, m, r in KEEP:
    print("    %-4s %-6s r=%+.3f" % (pos, m, r))
