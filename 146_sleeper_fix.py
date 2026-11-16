import json
import ssl
import os
import urllib.request as U
import certifi
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
LG = "1312181058833240064"


def get(u):
    with U.urlopen(u, context=CTX, timeout=60) as r:
        return json.loads(r.read().decode())


p = "sleeper_players.json"
print("=== DIAGNOSING %s ===" % p)
if os.path.exists(p):
    print("  size %.1f MB" % (os.path.getsize(p) / 1e6))
    PJ = json.load(open(p))
    print("  type %s | len %d" % (type(PJ).__name__, len(PJ)))
    if isinstance(PJ, dict):
        ks = list(PJ.keys())[:5]
        print("  first keys: %s" % ks)
        v = PJ[ks[0]]
        print("  value type %s" % type(v).__name__)
        if isinstance(v, dict):
            print("  value keys: %s" % list(v.keys())[:12])
    elif isinstance(PJ, list):
        print("  LIST not dict. first item:")
        print("  %s" % str(PJ[0])[:300])
else:
    print("  FILE MISSING")
    PJ = {}

RS = get("https://api.sleeper.app/v1/league/%s/rosters" % LG)
mine = [r for r in RS if r["roster_id"] == 1][0]
pids = (mine.get("players") or [])[:5]
print("\n  sample roster ids: %s" % pids)
print("  id types: %s" % [type(x).__name__ for x in pids])
hit = 0
if isinstance(PJ, dict):
    for x in pids:
        if str(x) in PJ:
            hit += 1
print("  matched %d of %d by str(id)" % (hit, len(pids)))

if hit == 0:
    print("\n  refetching player map from Sleeper...")
    PJ = get("https://api.sleeper.app/v1/players/nfl")
    json.dump(PJ, open(p, "w"))
    print("  rewrote %s with %d players" % (p, len(PJ)))
    hit = sum(1 for x in pids if str(x) in PJ)
    print("  now matched %d of %d" % (hit, len(pids)))

for x in pids:
    d = PJ.get(str(x), {})
    print("    %-10s %-24s %-4s %s"
          % (x, d.get("full_name", "?"),
             d.get("position", "?"), d.get("team", "?")))
