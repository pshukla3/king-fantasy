import json
import ssl
import urllib.request
import certifi
import re
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
URL = ("https://lm-api-reads.fantasy.espn.com/apis/v3/"
       "games/ffl/seasons/2026/segments/0/"
       "leaguedefaults/3?view=kona_player_info")
FILT = {"players": {"limit": 1200,
                    "sortPercOwned": {"sortAsc": False,
                                      "sortPriority": 1}}}
req = urllib.request.Request(URL, headers={
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "X-Fantasy-Filter": json.dumps(FILT)})

try:
    with urllib.request.urlopen(req, context=CTX,
                                timeout=60) as f:
        J = json.load(f)
    ok = True
except Exception as e:
    print("ESPN fetch failed: %s" % e)
    ok = False
    J = {}

if ok:
    pl = J.get("players", [])
    print("espn rows: %d" % len(pl))
    if pl:
        p0 = pl[0]
        print("row keys: %s" % sorted(p0.keys()))
        print("player keys: %s"
              % sorted((p0.get("player") or {}).keys())[:20])
        print("ownership: %s"
              % json.dumps(
                  (p0.get("player") or {}).get("ownership"),
                  indent=1)[:400])
    POS = {1: "QB", 2: "RB", 3: "WR", 4: "TE",
           5: "K", 16: "DST"}
    rows = []
    for d in pl:
        p = d.get("player") or {}
        o = p.get("ownership") or {}
        a = o.get("averageDraftPosition")
        if a is None or float(a) <= 0 or float(a) > 400:
            continue
        rows.append({"nm": p.get("fullName"),
                     "pos": POS.get(p.get(
                         "defaultPositionId"), "?"),
                     "eadp": round(float(a), 1)})
    E = pd.DataFrame(rows)
    E.to_csv("espn_adp_2026.csv", index=False)
    print("\nusable ESPN ADP rows: %d" % len(E))
    print(E.head(15).to_string(index=False))
