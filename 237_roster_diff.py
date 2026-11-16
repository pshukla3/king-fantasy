import os
import pandas as pd

if not os.path.exists("league_rosters.prev.csv"):
    raise SystemExit("no snapshot yet - run again tomorrow")

A = pd.read_csv("league_rosters.prev.csv")
B = pd.read_csv("league_rosters.csv")
K = ["roster_id", "name"]
TN = dict(zip(B["roster_id"], B["team_name"]))

a = set(map(tuple, A[K].astype(str).values))
b = set(map(tuple, B[K].astype(str).values))
add = sorted(b - a)
drp = sorted(a - b)

PP = dict(zip(B["name"].astype(str), B["ppg"]))
QP = dict(zip(A["name"].astype(str), A["ppg"]))

print("=== ROSTER CHANGES SINCE LAST PULL ===")
print("  adds %d | drops %d" % (len(add), len(drp)))
if not add and not drp:
    print("  no moves")
print("\n  %-24s %-20s %8s" % ("player", "team", "ppg"))
for rid, nm in add:
    print("  + %-22s %-20s %8.2f"
          % (nm[:22], str(TN.get(int(rid)))[:20],
             float(PP.get(nm, 0.0))))
for rid, nm in drp:
    print("  - %-22s %-20s %8.2f"
          % (nm[:22], str(TN.get(int(rid)))[:20],
             float(QP.get(nm, 0.0))))
