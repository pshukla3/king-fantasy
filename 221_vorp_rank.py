import numpy as np
import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce").fillna(0)

DEAD = {"IR", "OUT", "OUT_SEASON", "PUP", "NFI"}
st = B["status"].astype(str).str.upper()
z = st.isin(DEAD)
B.loc[z, "pp"] = 0.0
print("zeroed by status: %d" % int(z.sum()))

TEAMS = 10
BASE = {"QB": 1, "RB": 2, "WR": 2, "TE": 1,
        "K": 1, "DST": 1}
FLEX = {"RB", "WR", "TE"}
NFLEX = 2 * TEAMS

POOL = {}
for p in BASE:
    d = B[(B["position"] == p) & (B["pp"] > 0)]
    POOL[p] = sorted(d["pp"].tolist(), reverse=True)

need = {p: BASE[p] * TEAMS for p in BASE}
print("\n=== FLEX ALLOCATION (measured, not assumed) ===")
print("  20 flex spots go to whichever position has")
print("  the better player still on the board\n")
took = {"RB": 0, "WR": 0, "TE": 0}
for _ in range(NFLEX):
    best, bv = None, -1.0
    for p in FLEX:
        i = need[p]
        if i < len(POOL[p]) and POOL[p][i] > bv:
            bv, best = POOL[p][i], p
    if best is None:
        break
    need[best] += 1
    took[best] += 1
for p in ["RB", "WR", "TE"]:
    print("  %-4s %2d starters + %2d flex = %2d"
          % (p, BASE[p] * TEAMS, took[p], need[p]))

print("\n=== REPLACEMENT LEVEL ===")
REPL = {}
for p in BASE:
    i = need[p]
    v = POOL[p][i] if i < len(POOL[p]) else 0.0
    REPL[p] = float(v)
    print("  %-4s #%-3d = %6.2f ppg" % (p, i + 1, v))

B["vorp"] = B["pp"] - B["position"].map(REPL).fillna(0)
KD = B["position"].isin(["K", "DST", "DEF"])
skill = B[~KD & (B["pp"] > 0)]
floor = float(skill["pp"].min()
              - skill["position"].map(REPL).max())
B.loc[KD, "vorp"] = (B.loc[KD, "vorp"]
                     .clip(upper=0) + floor - 1.0)
print("\n  K/DST floored below every startable\n  skill player: DST persists at r=+0.116 and\n  kickers were never modeled, so their spread\n  is fill, not signal")
B.loc[B["pp"] <= 0, "vorp"] = -99.0
B = B.sort_values(["vorp", "pp"],
                  ascending=[False, False])
B = B.reset_index(drop=True)
B["rank"] = B.index + 1
B["pos_rank"] = B.groupby("position").cumcount() + 1
B["points"] = B["pp"].round(2)
B["vorp"] = B["vorp"].round(2)

print("\n=== TOP 30 BY VALUE OVER REPLACEMENT ===")
print("  %-3s %-24s %-5s %-4s %7s %7s %7s"
      % ("#", "player", "pos", "tm", "ppg", "vorp", "ADP"))
print("  " + "-" * 64)
for _, r in B.head(30).iterrows():
    a = pd.to_numeric(pd.Series([r["adp"]]),
                      errors="coerce").iloc[0]
    print("  %-3d %-24s %-5s %-4s %7.2f %+7.2f %7s"
          % (r["rank"], str(r["player_display_name"])[:24],
             "%s%d" % (r["position"], r["pos_rank"]),
             str(r["team"])[:4], r["pp"], r["vorp"],
             "--" if a != a else "%.1f" % a))

print("\n=== WHERE THE QBs LANDED ===")
q = B[B["position"] == "QB"].head(6)
for _, r in q.iterrows():
    print("  overall #%-4d %-22s %6.2f ppg  %+.2f vorp"
          % (r["rank"], str(r["player_display_name"])[:22],
             r["pp"], r["vorp"]))
print("\n  QB1 now goes at pick %d instead of pick 1."
      % int(q.iloc[0]["rank"]))

print("\n=== POSITION COUNT IN THE TOP 50 ===")
t = B.head(50)["position"].value_counts()
for p in ["RB", "WR", "TE", "QB", "K", "DST"]:
    print("  %-4s %d" % (p, int(t.get(p, 0))))

eg = pd.to_numeric(B["exp_games"],
                   errors="coerce").fillna(17.0)
B["value"] = (B["vorp"] * eg).round(2)
B.drop(columns=["pp"]).to_csv("board_final.csv",
                              index=False)
print("\n  wrote board_final.csv (%d rows)" % len(B))
bad = int((B["vorp"].diff().dropna() > 1e-9).sum())
assert bad == 0, "rank is not monotonic in vorp"
print("  ordering verified monotonic in VORP")
