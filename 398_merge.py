import json, re
import numpy as np
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

MP = pd.read_csv("model_proj.csv")
PJ = dict(zip(MP["k"], MP["proj_model"]))
print("model projections: %d players" % len(PJ))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
B["points"] = pd.to_numeric(B["points"], errors="coerce")
B["mproj"] = B["k"].map(PJ)
hit = int(B["mproj"].notna().sum())
print("matched to the board: %d" % hit)
# players the model has no 2026 data for keep the old number
B["mproj"] = B["mproj"].fillna(B["points"])

D = json.load(open("site/_slteams.json"))
SLOTS = [s for s in D["slots"] if s != "BN"]
NT = len(D["teams"])
FLEXOK = {"FLEX": {"RB", "WR", "TE"},
          "SUPER_FLEX": {"QB", "RB", "WR", "TE"}}
base, flex = {}, []
for s in SLOTS:
    if s in FLEXOK:
        flex.append(FLEXOK[s])
    else:
        p = "DST" if s in ("DEF", "DST") else s
        base[p] = base.get(p, 0) + 1

pools = {}
for p in set(list(base) + ["RB", "WR", "TE", "QB"]):
    pools[p] = list(B[B["position"] == p]["mproj"]
                    .dropna().sort_values(
                        ascending=False).values)
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
print("\n=== HOW MANY START / WHAT IS FREE ===")
for p in sorted(REP):
    print("  %-4s %2d start, replacement %.2f"
          % (p, taken[p], REP[p]))

M = json.load(open("pos_mult.json"))
print("\npositional multipliers:", M)
B["mvorp"] = ((B["mproj"]
               - B["position"].map(lambda p: REP.get(p, 0.0)))
              * B["position"].map(
                  lambda p: float(M.get(str(p), 1.0)))
              ).round(2)
B = B.sort_values("mvorp", ascending=False)
B["rank_v"] = range(1, len(B) + 1)
B["pre_vorp"] = B["mvorp"]
B["upd_vorp"] = B["mvorp"]
B["pre_rank"] = B["rank_v"]
B["upd_rank"] = B["rank_v"]
B["proj_live"] = B["mproj"]
B["proj_sch"] = B["mproj"]
B.drop(columns=["k"]).to_csv("board_final.csv",
                             index=False)

print("\n=== TOP 30 BY VALUE ===")
print("%-3s %-24s %-4s %7s %7s"
      % ("#", "PLAYER", "POS", "PROJ", "VALUE"))
for _, r in B.head(30).iterrows():
    print("%-3d %-24s %-4s %7.2f %7.2f"
          % (r["rank_v"], r["player_display_name"][:24],
             r["position"], r["mproj"], r["mvorp"]))
print("\n=== FIRST AT EACH POSITION ===")
seen = set()
for _, r in B.iterrows():
    p = r["position"]
    if p not in seen:
        seen.add(p)
        print("  %-4s #%-4d %-24s proj %.2f"
              % (p, r["rank_v"],
                 r["player_display_name"][:24], r["mproj"]))
