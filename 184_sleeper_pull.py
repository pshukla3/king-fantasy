import json
import ssl
import urllib.request
import certifi
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())

def get(u):
    r = urllib.request.Request(
        u, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(r, context=CTX,
                                timeout=60) as f:
        return json.load(f)

URL = ("https://api.sleeper.com/projections/nfl/2026"
       "?season_type=regular"
       "&position[]=QB&position[]=RB"
       "&position[]=WR&position[]=TE"
       "&order_by=pts_ppr")
J = get(URL)
print("rows returned: %d" % len(J))
if not J:
    raise SystemExit("empty response - endpoint changed")

d0 = J[0]
print("\ntop-level keys: %s" % sorted(d0.keys()))
print("\nstats keys: %s"
      % sorted((d0.get("stats") or {}).keys()))
print("\nplayer keys: %s"
      % sorted((d0.get("player") or {}).keys())[:16])
print("\nfirst row raw:")
print(json.dumps(d0, indent=1)[:900])

json.dump(J, open("sleeper_proj_raw.json", "w"))
print("\nsaved sleeper_proj_raw.json")
