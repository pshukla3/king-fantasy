import json
import ssl
import certifi
import urllib.request as UR

CTX = ssl.create_default_context(cafile=certifi.where())
HDR = {"User-Agent": "curl/8.7.1"}
API = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/"

def g(u):
    r = UR.Request(u, headers=HDR)
    with UR.urlopen(r, timeout=25, context=CTX) as f:
        return json.load(f)

sb = g(API + "scoreboard?dates=20251005")
ev = [e for e in sb.get("events", [])
      if ((e.get("status") or {}).get("type") or {})
      .get("state") == "post"]
print("completed games found: %d" % len(ev))
if not ev:
    raise SystemExit("no completed games on that date")
E = ev[0]
print("testing: %s  (id %s)" % (E.get("name"), E["id"]))

sm = g(API + "summary?event=" + E["id"])
print("summary keys: %s" % list(sm.keys())[:12])

OK, BAD = [], []
def chk(label, val, ok):
    (OK if ok else BAD).append(label)
    print("  %-34s %-5s %s"
          % (label, "OK" if ok else "FAIL", str(val)[:52]))

print("\n=== FIELDS _game.js DEPENDS ON ===")
c = (E.get("competitions") or [{}])[0]
chk("status.type.state", ((E.get("status") or {})
    .get("type") or {}).get("state"), True)
chk("status.type.shortDetail", ((E.get("status") or {})
    .get("type") or {}).get("shortDetail"), True)
od = (c.get("odds") or [{}])[0]
chk("odds[0].spread", od.get("spread"),
    od.get("spread") is not None)
cp = c.get("competitors") or []
chk("competitors count", len(cp), len(cp) == 2)
for x in cp:
    t = x.get("team") or {}
    chk("  %s color/abbr" % x.get("homeAway"),
        "%s / %s" % (t.get("color"), t.get("abbreviation")),
        bool(t.get("color") and t.get("abbreviation")))

hid = [x.get("id") for x in
       ((((sm.get("header") or {}).get("competitions")
          or [{}])[0]).get("competitors") or [])
       if x.get("homeAway") == "home"]
chk("header home id (used for possession)", hid, bool(hid))

dv = (sm.get("drives") or {})
prev = dv.get("previous") or []
chk("drives.previous count", len(prev), len(prev) > 0)
chk("drives.current present", "current" in dv, True)

np_ = 0
sample = None
miss = {"down": 0, "distance": 0, "yardsToEndzone": 0,
        "clock": 0, "period": 0, "text": 0, "team": 0}
for d in prev:
    for p in (d.get("plays") or []):
        s = p.get("start") or {}
        if not s.get("down"):
            continue
        np_ += 1
        if s.get("distance") is None:
            miss["distance"] += 1
        if s.get("yardsToEndzone") is None:
            miss["yardsToEndzone"] += 1
        if not ((p.get("clock") or {}).get("displayValue")):
            miss["clock"] += 1
        if not ((p.get("period") or {}).get("number")):
            miss["period"] += 1
        if not p.get("text"):
            miss["text"] += 1
        if not ((s.get("team") or {}).get("id")):
            miss["team"] += 1
        if sample is None:
            sample = p
chk("scrimmage plays parsed", np_, np_ > 50)
for k, v in miss.items():
    chk("  plays missing %s" % k, v, v == 0)

print("\n=== SAMPLE PLAY (what the feed will render) ===")
if sample:
    s = sample.get("start") or {}
    print("  Q%s %s | %s & %s at %s to endzone"
          % ((sample.get("period") or {}).get("number"),
             (sample.get("clock") or {}).get("displayValue"),
             s.get("down"), s.get("distance"),
             s.get("yardsToEndzone")))
    print("  score %s-%s | poss team id %s"
          % (sample.get("homeScore"), sample.get("awayScore"),
             (s.get("team") or {}).get("id")))
    print("  %s" % str(sample.get("text"))[:150])

print("\n%d checks OK, %d FAILED" % (len(OK), len(BAD)))
if BAD:
    print("FAILURES: %s" % ", ".join(BAD))
