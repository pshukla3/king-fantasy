import json
import pandas as pd

D = json.load(open("site/_slteams.json"))
SLOTS = [s for s in D["slots"] if s != "BN"]
NT = len(D["teams"])
FLEXOK = {"FLEX": {"RB", "WR", "TE"},
          "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
          "WRRB_FLEX": {"RB", "WR"},
          "REC_FLEX": {"WR", "TE"}}
base, flex = {}, []
for s in SLOTS:
    if s in FLEXOK:
        flex.append(FLEXOK[s])
    else:
        p = "DST" if s in ("DEF", "DST") else s
        base[p] = base.get(p, 0) + 1
print("league: %d teams | slots %s" % (NT, SLOTS))
print("fixed starters per team: %s | flex: %d"
      % (base, len(flex)))

B = pd.read_csv("board_final.csv")
COL = "proj_live" if "proj_live" in B.columns else "points"
B[COL] = pd.to_numeric(B[COL], errors="coerce")
B = B[B[COL].notna()].copy()

SOS = json.load(open("site/_sos.json"))["sos"]
def sosadj(r):
    m = SOS.get(str(r["position"]), {})
    return float(m.get(str(r.get("team") or ""), 0.0))
B["sos"] = B.apply(sosadj, axis=1)
B["proj_sch"] = (B[COL] + B["sos"]).round(2)

pools = {}
for p in set(list(base) + ["RB", "WR", "TE", "QB"]):
    d = B[B["position"] == p].sort_values("proj_sch",
                                          ascending=False)
    pools[p] = list(d["proj_sch"].values)

taken = {p: base.get(p, 0) * NT for p in pools}
for _ in range(len(flex) * NT):
    best, bp = -1e9, None
    for p in ("RB", "WR", "TE"):
        i = taken.get(p, 0)
        if i < len(pools[p]) and pools[p][i] > best:
            best, bp = pools[p][i], p
    if bp is None:
        break
    taken[bp] += 1

REP = {}
for p, n in taken.items():
    v = pools.get(p) or []
    REP[p] = float(v[min(n, len(v) - 1)]) if v else 0.0
print("\n=== REPLACEMENT LEVEL (ppg) ===")
for p in sorted(REP):
    print("  %-4s starters %-3d  replacement %6.2f"
          % (p, taken[p], REP[p]))

B["vorp"] = (B["proj_sch"]
             - B["position"].map(lambda p: REP.get(p, 0.0)))
B["vorp"] = B["vorp"].round(2)
B = B.sort_values("vorp", ascending=False)
B["rank_v"] = range(1, len(B) + 1)
B.to_csv("board_final.csv", index=False)

print("\n=== TOP 20 BY VALUE OVER REPLACEMENT ===")
print("%-3s %-24s %-4s %7s %6s %7s"
      % ("#", "PLAYER", "POS", "PROJ", "SOS", "VORP"))
for _, r in B.head(20).iterrows():
    print("%-3d %-24s %-4s %7.2f %+6.2f %7.2f"
          % (r["rank_v"], r["player_display_name"][:24],
             r["position"], r["proj_sch"], r["sos"],
             r["vorp"]))

print("\n=== WHERE THE FIRST QB LANDS ===")
q = B[B["position"] == "QB"].head(3)
for _, r in q.iterrows():
    print("  #%-4d %-22s %.2f ppg -> %.2f over replacement"
          % (r["rank_v"], r["player_display_name"][:22],
             r["proj_sch"], r["vorp"]))
