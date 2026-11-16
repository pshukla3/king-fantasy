import json, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X "
     "10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}

def get(u, t=20):
    r = U.Request(u, headers=H)
    return U.urlopen(r, timeout=t, context=CTX).read()

print("=== SLEEPER (no auth) ===")
try:
    d = json.loads(get("https://api.sleeper.app/v1/league/"
                       "1312181058833240064"))
    print("  OK: %s | %s teams | %s"
          % (d.get("name"), d.get("total_rosters"),
             d.get("season")))
    print("  works for any league id, no credentials")
except Exception as e:
    print("  FAIL", str(e)[:60])

print("\n=== ESPN read API (public leagues) ===")
E = ("https://lm-api-reads.fantasy.espn.com/apis/v3/games/"
     "ffl/seasons/2026/segments/0/leagues/%s"
     "?view=mTeam&view=mSettings")
for lid in ("1234567", "12345"):
    try:
        b = get(E % lid)
        d = json.loads(b)
        print("  %s -> %d bytes, keys: %s"
              % (lid, len(b), list(d.keys())[:6]))
        break
    except Exception as e:
        print("  %s -> %s" % (lid, str(e)[:70]))

print("\n=== YAHOO ===")
try:
    b = get("https://fantasysports.yahooapis.com/fantasy/v2/"
            "game/nfl")
    print("  unexpected: reachable without auth,", len(b))
except Exception as e:
    print("  %s" % str(e)[:70])
    print("  -> needs OAuth2 + a registered app, as expected")
