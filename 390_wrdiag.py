import re
import numpy as np
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

W = pd.read_parquet("weekly_all.parquet")
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W["k"] = W["player_display_name"].map(norm)
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
for c in ("targets", "receptions", "receiving_yards"):
    W[c] = pd.to_numeric(W.get(c), errors="coerce")\
        .fillna(0.0)

def seas(y):
    d = W[(W["season"] == y) & (W["week"] <= 17)]
    g = d.groupby("k").agg(
        ppg=("fp", "mean"), g=("fp", "size"),
        tg=("targets", "mean"),
        yd=("receiving_yards", "mean"))
    return g[g["g"] >= 6]

S25, S24 = seas(2025), seas(2024)

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
B = B[B["position"] == "WR"].copy()
B["adp_rk"] = B["adp"].rank(method="min")
z = B[B["adp"].notna() & (B["adp_rk"] <= 60)]\
    .sort_values("adp_rk")

print("=== TOP-60 ADP RECEIVERS: OURS vs THEIR HISTORY ===")
print("%-22s %5s %6s %6s %6s %6s %6s %6s"
      % ("PLAYER", "ADP", "'24", "'25", "TGT25",
         "BASE", "CALIB", "GAP25"))
gaps = []
for _, r in z.iterrows():
    k = r["k"]
    a24 = S24["ppg"].get(k)
    a25 = S25["ppg"].get(k)
    t25 = S25["tg"].get(k)
    base = r.get("points_raw")
    cal = r.get("points")
    g = (cal - a25) if (a25 is not None
                        and pd.notna(cal)) else None
    if g is not None:
        gaps.append(g)
    print("%-22s %5.0f %6s %6s %6s %6s %6s %6s"
          % (r["player_display_name"][:22], r["adp_rk"],
             "-" if a24 is None else "%.1f" % a24,
             "-" if a25 is None else "%.1f" % a25,
             "-" if t25 is None else "%.1f" % t25,
             "-" if pd.isna(base) else "%.1f" % base,
             "-" if pd.isna(cal) else "%.1f" % cal,
             "-" if g is None else "%+.1f" % g))

print("\nmean gap vs 2025 actual: %+.2f ppg"
      % (np.mean(gaps) if gaps else 0))
print("(negative = we project them below what they "
      "already did last year)")

print("\n=== SAME CHECK FOR RUNNING BACKS ===")
B2 = pd.read_csv("board_final.csv")
B2["k"] = B2["player_display_name"].map(norm)
B2 = B2[B2["position"] == "RB"].copy()
B2["adp_rk"] = B2["adp"].rank(method="min")
g2 = []
for _, r in B2[B2["adp"].notna()
               & (B2["adp_rk"] <= 60)].iterrows():
    a25 = S25["ppg"].get(r["k"])
    if a25 is not None and pd.notna(r.get("points")):
        g2.append(r["points"] - a25)
print("mean gap vs 2025 actual: %+.2f ppg  (n=%d)"
      % (np.mean(g2) if g2 else 0, len(g2)))

print("\n=== ARE WE MISSING TARGET VOLUME? ===")
for nm in ("Alec Pierce", "Rome Odunze",
           "Terry McLaurin", "Jaylen Waddle",
           "Zay Flowers", "A.J. Brown"):
    k = norm(nm)
    print("  %-20s 2025: %s ppg on %s tgt/g | ours %s"
          % (nm,
             "-" if S25["ppg"].get(k) is None
             else "%.1f" % S25["ppg"].get(k),
             "-" if S25["tg"].get(k) is None
             else "%.1f" % S25["tg"].get(k),
             "-" if not len(B[B["k"] == k])
             else "%.1f" % B[B["k"] == k]["points"].iloc[0]))
