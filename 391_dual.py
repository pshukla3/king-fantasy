import json
import pandas as pd

M = json.load(open("pos_mult.json"))
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

B = pd.read_csv("board_final.csv")
for c in ("points", "proj_sch", "proj_live"):
    if c in B.columns:
        B[c] = pd.to_numeric(B[c], errors="coerce")
if "proj_sch" not in B.columns:
    B["proj_sch"] = B["points"]

def value(col, tag):
    pools = {}
    for p in set(list(base) + ["RB", "WR", "TE", "QB"]):
        d = B[B["position"] == p].sort_values(
            col, ascending=False)
        pools[p] = list(d[col].dropna().values)
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
    raw = B[col] - B["position"].map(
        lambda p: REP.get(p, 0.0))
    scaled = raw * B["position"].map(
        lambda p: float(M.get(str(p), 1.0)))
    B[tag + "_vorp"] = scaled.round(2)
    B[tag + "_rank"] = scaled.rank(ascending=False,
                                   method="min")
    return REP

rp = value("points", "pre")
ru = value("proj_sch", "upd")
print("replacement (preseason):",
      {k: round(v, 2) for k, v in sorted(rp.items())})
print("replacement (updated)  :",
      {k: round(v, 2) for k, v in sorted(ru.items())})

B["vorp"] = B["upd_vorp"]
B["rank_v"] = B["upd_rank"]
B.to_csv("board_final.csv", index=False)

print("\n%-24s %-4s %7s %7s %7s"
      % ("PLAYER", "POS", "PRESEAS", "UPDATED", "MOVE"))
z = B.sort_values("pre_rank").head(16)
for _, r in z.iterrows():
    print("%-24s %-4s %7.0f %7.0f %+7.0f"
          % (r["player_display_name"][:24], r["position"],
             r["pre_rank"], r["upd_rank"],
             r["upd_rank"] - r["pre_rank"]))
print("\nbiggest movers since week 1:")
B["mv"] = B["upd_rank"] - B["pre_rank"]
for _, r in B[B["pre_rank"] <= 80].nsmallest(
        5, "mv").iterrows():
    print("  UP   %-22s %3.0f -> %3.0f"
          % (r["player_display_name"][:22],
             r["pre_rank"], r["upd_rank"]))
for _, r in B[B["pre_rank"] <= 80].nlargest(
        5, "mv").iterrows():
    print("  DOWN %-22s %3.0f -> %3.0f"
          % (r["player_display_name"][:22],
             r["pre_rank"], r["upd_rank"]))
