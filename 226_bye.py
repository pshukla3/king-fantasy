import pandas as pd
import nflreadpy as nfl

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX"}
S = nfl.load_schedules(seasons=[2026])
S = S.to_pandas() if hasattr(S, "to_pandas") else S
seen = {}
for _, r in S.iterrows():
    w = int(r["week"])
    for c in ["home_team", "away_team"]:
        seen.setdefault(str(r[c]), set()).add(w)
BYE = {}
for t, ws in seen.items():
    m = [w for w in range(1, 19) if w not in ws]
    BYE[FIX.get(t, t)] = m[0] if m else 0

B = pd.read_csv("board_final.csv", low_memory=False)
B["bye"] = (B["team"].astype(str).map(BYE)
            .fillna(0).astype(int))
B.to_csv("board_final.csv", index=False)
print("byes for %d teams" % len(BYE))
print("rows with a bye: %d of %d"
      % (int((B["bye"] > 0).sum()), len(B)))
print("  191_adp_merge used to attach this; it is")
print("  broken on KeyError 'sadp' and is out")
