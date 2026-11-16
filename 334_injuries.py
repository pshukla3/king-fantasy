import json, ssl, certifi, re
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
B = ("https://site.api.espn.com/apis/site/v2/"
     "sports/football/nfl/")

def g(u):
    r = U.Request(u, headers=H)
    return json.loads(U.urlopen(r, timeout=25,
                                context=CTX).read())

sb = g(B + "scoreboard")
EV = [(e["id"], e.get("shortName", ""))
      for e in sb.get("events", [])
      if ((e.get("status") or {}).get("type")
          or {}).get("state") == "post"]
print("completed games: %d" % len(EV))

RX = re.compile(
    r"\b(injur|hurt|carted|limp|down on the (field|turf)|"
    r"evaluat|concussion|shaken up|no return|questionable "
    r"to return|ruled out)\b", re.I)

ALL = []
for ev, sn in EV:
    s = g(B + "summary?event=" + str(ev))

    print("\n=== %s ===" % sn)
    print("top-level keys with 'inj': %s"
          % [k for k in s.keys() if "inj" in k.lower()])

    blk = s.get("injuries") or []
    print("injuries block: %d team entries" % len(blk))
    for t in blk:
        tm = ((t.get("team") or {}).get("abbreviation")
              or "")
        for i in (t.get("injuries") or []):
            ath = i.get("athlete") or {}
            st = i.get("status") or ""
            d = i.get("details") or {}
            ty = d.get("type") or d.get("detail") or ""
            nm = ath.get("displayName") or ""
            print("   %-4s %-24s %-12s %s"
                  % (tm, nm, st, ty))
            ALL.append({"g": sn, "tm": tm, "name": nm,
                        "status": st, "detail": str(ty),
                        "src": "injuries"})

    hits, np_ = [], 0
    for d in ((s.get("drives") or {}).get("previous")
              or []):
        for p in (d.get("plays") or []):
            np_ += 1
            tx = p.get("text") or ""
            if RX.search(tx):
                hits.append((
                    ((p.get("period") or {}).get("number")),
                    (p.get("clock") or {}).get(
                        "displayValue", ""),
                    tx[:96]))
    print("plays scanned %d | injury mentions %d"
          % (np_, len(hits)))
    for q, c, tx in hits[:12]:
        print("   Q%s %-6s %s" % (q, c, tx))
        ALL.append({"g": sn, "tm": "", "name": "",
                    "status": "in-game",
                    "detail": tx[:160], "src": "pbp"})

json.dump(ALL, open("site/_injuries.json", "w"))
print("\nwrote site/_injuries.json (%d rows)" % len(ALL))
