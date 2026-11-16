import json
import ssl
import urllib.request
import certifi

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
      " AppleWebKit/537.36 (KHTML, like Gecko)"
      " Chrome/124.0 Safari/537.36")
CTX = ssl.create_default_context(cafile=certifi.where())

def get(u, t=25):
    r = urllib.request.Request(u, headers={
        "User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(
            r, timeout=t, context=CTX) as f:
        return json.loads(f.read().decode("utf-8",
                                          "ignore"))

print("=== 1. SLEEPER STATE ===")
try:
    s = get("https://api.sleeper.app/v1/state/nfl")
    for k in sorted(s):
        print("  %-22s %s" % (k, s[k]))
except Exception as e:
    print("  FAILED %s" % e)

print("\n=== 2. SLEEPER WEEKLY STATS (2026 wk1) ===")
try:
    d = get("https://api.sleeper.com/stats/nfl/regular"
            "/2026/1?season_type=regular")
    print("  type %s | len %d" % (type(d).__name__,
                                  len(d)))
    if isinstance(d, list) and d:
        r0 = d[0]
        print("  row keys: %s" % sorted(r0.keys())[:14])
        st = r0.get("stats") or {}
        print("  stat keys: %s" % sorted(st.keys())[:18])
    elif isinstance(d, dict) and d:
        k = list(d)[0]
        print("  sample id %s -> %s" % (k, d[k]))
except Exception as e:
    print("  FAILED %s" % e)

print("\n=== 3. ESPN SCOREBOARD ===")
EV = None
try:
    d = get("https://site.api.espn.com/apis/site/v2/"
            "sports/football/nfl/scoreboard")
    ev = d.get("events") or []
    print("  events: %d | season %s week %s"
          % (len(ev),
             (d.get("season") or {}).get("year"),
             (d.get("week") or {}).get("number")))
    for e in ev[:3]:
        EV = EV or e.get("id")
        c = (e.get("competitions") or [{}])[0]
        st = ((c.get("status") or {}).get("type")
              or {}).get("description")
        sc = [(x.get("team", {}).get("abbreviation"),
               x.get("score"))
              for x in (c.get("competitors") or [])]
        print("  %-10s %-28s %s"
              % (e.get("id"), e.get("shortName"), st))
        print("       %s" % sc)
    if not ev:
        print("  no events - preseason gap is expected,"
              " week 1 is Sep 9")
except Exception as e:
    print("  FAILED %s" % e)

print("\n=== 4. ESPN WIN PROBABILITY ===")
if EV:
    try:
        d = get("https://site.api.espn.com/apis/site/v2/"
                "sports/football/nfl/summary?event=" + EV)
        print("  summary keys: %s" % sorted(d.keys()))
        wp = d.get("winprobability")
        print("  winprobability present: %s | n=%s"
              % (wp is not None,
                 len(wp) if wp else 0))
        if wp:
            print("  sample: %s" % wp[-1])
    except Exception as e:
        print("  FAILED %s" % e)
else:
    print("  no event id to test")
