import pandas as pd
import numpy as np
import nflreadpy as nfl

CO = {"ppg": 3.045, "age": -0.645, "opp_share": 0.488,
      "draft_pick": -0.473, "cpg": 0.426, "moved": -0.326,
      "tpg": 0.250, "ypc": 0.240, "car_share": -0.219,
      "rtdr": -0.217, "ctch": -0.208, "g": 0.140}

S = pd.read_csv("pos_season_panel.csv", low_memory=False)
S = S[(S["season"] == 2025) & (S["position"] == "RB")]
PL = nfl.load_players()
PL = PL.to_pandas() if hasattr(PL, "to_pandas") else PL
idc = "gsis_id" if "gsis_id" in PL.columns else "player_id"
PL = PL[[idc, "display_name", "birth_date",
         "draft_pick"]].rename(columns={idc: "player_id"})
PL["age"] = 2026 - pd.to_datetime(
    PL["birth_date"], errors="coerce").dt.year
S = S.merge(PL.drop_duplicates("player_id"),
            on="player_id", how="left")
S["draft_pick"] = S["draft_pick"].fillna(260.0)
S["moved"] = 0.0

pool = S[S["ppg"] > 8].copy()
print("2025 RBs above 8 ppg: %d" % len(pool))
cb = S[S["display_name"].astype(str)
       .str.contains("Chase Brown", na=False)]
assert len(cb), "Chase Brown not in the 2025 panel"
cb = cb.iloc[0]

print("\n=== WHERE HE SITS IN EACH INPUT ===")
print("  pct = his percentile among those RBs")
print("  contrib = z x the ridge coefficient\n")
print("  %-11s %9s %7s %8s %9s"
      % ("feature", "his val", "pct", "coef", "contrib"))
print("  " + "-" * 50)
rows = []
for f, c in CO.items():
    if f not in S.columns:
        continue
    v = pd.to_numeric(pd.Series([cb[f]]),
                      errors="coerce").iloc[0]
    col = pd.to_numeric(pool[f], errors="coerce").dropna()
    if v != v or len(col) < 10 or col.std() == 0:
        continue
    z = (v - col.mean()) / col.std()
    rows.append((f, v, 100.0 * (col < v).mean(), c, z * c))
for f, v, p, c, k in sorted(rows, key=lambda x: x[4]):
    print("  %-11s %9.3f %6.0f%% %+8.3f %+9.3f"
          % (f, v, p, c, k))
print("\n  most negative contrib = what is docking him")

print("\n=== HIM vs THE RBs THE MARKET LIKES MORE ===")
NM = ["Chase Brown", "Saquon Barkley", "Derrick Henry",
      "Kyren Williams", "De'Von Achane", "James Cook"]
cols = ["ppg", "cpg", "tpg", "car_share", "opp_share",
        "ypc", "rtdr", "ctch", "g", "age", "draft_pick"]
print("  %-20s" % "player"
      + "".join("%8s" % c[:8] for c in cols))
print("  " + "-" * (20 + 8 * len(cols)))
for nm in NM:
    h = S[S["display_name"].astype(str)
          .str.contains(nm, na=False)]
    if not len(h):
        print("  %-20s not in 2025 panel" % nm[:20])
        continue
    r = h.iloc[0]
    print("  %-20s" % nm[:20]
          + "".join("%8.2f" % pd.to_numeric(
              pd.Series([r[c]]), errors="coerce").iloc[0]
              for c in cols))

P = pd.read_csv("proj_2026.csv")
print("\n=== WHAT THE MODEL OUTPUTS ===")
for nm in NM:
    h = P[P["player_display_name"].astype(str)
          .str.contains(nm, na=False)]
    if not len(h):
        continue
    r = h.iloc[0]
    print("  %-20s %5.2f -> %5.2f (%+.0f%%)"
          " | p10 %5.2f p90 %5.2f"
          % (nm[:20], r["ppg25"], r["proj"],
             100 * (r["proj"] / r["ppg25"] - 1),
             r["p10"], r["p90"]))
