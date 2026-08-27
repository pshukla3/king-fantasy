import pandas as pd
import nflreadpy as nfl

S = nfl.load_schedules(seasons=[2024, 2025, 2026])
S = S.to_pandas() if hasattr(S, "to_pandas") else S
print("coach cols: %s"
      % [c for c in S.columns if "coach" in c.lower()])

parts = []
for side in ["home", "away"]:
    k = side + "_coach"
    if k not in S.columns:
        continue
    d = S[["season", "week", side + "_team", k]].copy()
    d.columns = ["season", "week", "tm", "coach"]
    parts.append(d)

if not parts:
    raise SystemExit("no coach columns - use web search instead")

C = pd.concat(parts, ignore_index=True)
C = C[C["coach"].notna()]
C = C[C["coach"].astype(str).str.strip() != ""]
print("coach rows: %d" % len(C))
for y in sorted(C["season"].unique()):
    x = C[C["season"] == y]
    print("  %d  rows %4d  teams %d"
          % (y, len(x), x["tm"].nunique()))

C = C.sort_values(["season", "week"])
L = C.groupby("tm").tail(1)

MAP = {"LAR": "LA", "AZ": "ARI", "ARZ": "ARI"}

def key(t):
    return MAP.get(str(t).strip(), str(t).strip())

LK = {}
for _, r in L.iterrows():
    LK[key(r["tm"])] = (str(r["coach"]), int(r["season"]))

A = pd.read_csv("coaching_2026.csv")
for _c in ["head_coach", "off_coordinator",
           "def_coordinator", "scheme_note"]:
    A[_c] = A[_c].astype("object")
hit = 0
for i, r in A.iterrows():
    v = LK.get(key(r["team"]))
    if v is None:
        print("  NO MATCH: %s" % r["team"])
        continue
    A.at[i, "head_coach"] = v[0]
    A.at[i, "scheme_note"] = "HC of record, %d games" % v[1]
    hit += 1

A.to_csv("coaching_2026.csv", index=False)
print("\nfilled %d of %d head coaches" % (hit, len(A)))
print(A[["team", "head_coach", "scheme_note"]]
      .to_string(index=False))
