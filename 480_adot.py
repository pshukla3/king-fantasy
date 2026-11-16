import numpy as np
import nflreadpy as nfl

d = nfl.load_player_stats([2023, 2024, 2025]).to_pandas()
cols = [c for c in d.columns if "air" in c.lower()]
print("air-yard columns available:", cols)
for c in ("targets", "receptions", "receiving_yards",
          "receiving_air_yards"):
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)

d = d[(d["position"].isin(["WR", "TE"])) & (d["targets"] >= 3)]
d["adot"] = d["receiving_air_yards"] / d["targets"]
d["ypr"] = np.where(d["receptions"] > 0,
                    d["receiving_yards"] / d["receptions"], 0)
d["ypt"] = d["receiving_yards"] / d["targets"]
d["crate"] = d["receptions"] / d["targets"]
d["ord"] = d["season"] * 100 + d["week"]

def auto(col, lag=1):
    xs, ys = [], []
    for pid, g in d.groupby("player_id"):
        v = g.sort_values("ord")[col].values
        for i in range(len(v) - lag):
            if np.isfinite(v[i]) and np.isfinite(v[i + lag]):
                xs.append(v[i]); ys.append(v[i + lag])
    if len(xs) < 50:
        return 0.0, 0
    return float(np.corrcoef(xs, ys)[0, 1]), len(xs)

print("\n=== WEEK-TO-WEEK RELIABILITY (WR/TE) ===")
print("%-22s %8s %9s" % ("COMPONENT", "r", "N"))
for lbl, c in (("aDOT (air yds/tgt)", "adot"),
               ("yards per target", "ypt"),
               ("yards per reception", "ypr"),
               ("catch rate", "crate"),
               ("target share", "tshare")):
    if c not in d.columns:
        continue
    r, n = auto(c)
    print("%-22s %8.3f %9d%s" % (lbl, r, n,
          "   <-- STABLE" if r > 0.35 else ""))

print("\n=== does aDOT explain ypr? ===")
s = d[(d["adot"] > 0) & (d["ypr"] > 0)]
print("corr(aDOT, ypr) within week: %.3f (n=%d)"
      % (np.corrcoef(s["adot"], s["ypr"])[0, 1], len(s)))
print("corr(aDOT, catch rate):      %.3f"
      % np.corrcoef(s["adot"], s["crate"])[0, 1])

print("\n=== 2026 aDOT, the players in question ===")
c = nfl.load_player_stats([2026]).to_pandas()
for x in ("targets", "receptions", "receiving_yards",
          "receiving_air_yards", "receiving_tds"):
    if x not in c.columns:
        c[x] = 0.0
    c[x] = c[x].fillna(0.0).astype(float)
a = c.groupby("player_display_name", as_index=False).agg(
    t=("targets", "sum"), r=("receptions", "sum"),
    y=("receiving_yards", "sum"),
    ay=("receiving_air_yards", "sum"),
    td=("receiving_tds", "sum"), g=("targets", "size"))
a = a[a["t"] >= 12]
for n in ("Jaxon Smith-Njigba", "Ja'Marr Chase",
          "Amon-Ra St. Brown", "Puka Nacua", "Chris Olave",
          "Zay Flowers", "CeeDee Lamb"):
    x = a[a["player_display_name"] == n]
    if not len(x):
        continue
    x = x.iloc[0]
    print("  %-22s aDOT %5.1f  catch%% %4.0f  ypr %5.1f"
          "  ypt %5.1f  TD %d"
          % (n[:22], x["ay"] / x["t"], x["r"] / x["t"] * 100,
             x["y"] / max(1, x["r"]), x["y"] / x["t"], x["td"]))
print("\nleague ypr 11.18, catch rate 67.4%% -- what we"
      " currently assign everyone")
