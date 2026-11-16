import json
import pandas as pd
import nflreadpy as nfl

FIX = {"LAR": "LA", "WSH": "WAS", "JAC": "JAX",
       "AZ": "ARI"}
S = nfl.load_schedules(seasons=[2026])
S = S.to_pandas() if hasattr(S, "to_pandas") else S
SCH, DATES = {}, {}
for _, r in S.iterrows():
    w = int(r["week"])
    h = FIX.get(str(r["home_team"]), str(r["home_team"]))
    a = FIX.get(str(r["away_team"]), str(r["away_team"]))
    d = str(r.get("gameday"))[:10]
    t = "%s %s" % (str(r.get("weekday"))[:3],
                   str(r.get("gametime"))[:5])
    SCH.setdefault(h, {})[w] = {"o": a, "at": "vs",
                                "d": d, "t": t}
    SCH.setdefault(a, {})[w] = {"o": h, "at": "@",
                                "d": d, "t": t}
    DATES.setdefault(str(w), set()).add(d.replace("-", ""))
DATES = {k: sorted(v) for k, v in DATES.items()}
json.dump({"sched": SCH, "dates": DATES},
          open("site/_sched.json", "w"))
print("schedule: %d teams | %d weeks"
      % (len(SCH), len(DATES)))
print("  wk1 dates: %s" % DATES.get("1"))

PJ = json.load(open("sleeper_players.json"))
POS = ("QB", "RB", "WR", "TE", "K", "DEF", "DST")
M = {}
for k, v in PJ.items():
    p = v.get("position")
    if p in POS and (v.get("team") or p in ("DEF", "DST")):
        M[k] = {"n": v.get("full_name") or k,
                "p": "DEF" if p == "DST" else p,
                "t": v.get("team") or k}
json.dump(M, open("site/_pmap.json", "w"))
print("player map: %d fantasy-eligible" % len(M))
