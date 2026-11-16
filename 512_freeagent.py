import json, re, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())

from namekey import nk as norm

print("pulling Sleeper roster status")
ALL = json.loads(U.urlopen(U.Request(
    "https://api.sleeper.app/v1/players/nfl",
    headers={"User-Agent": "Mozilla/5.0"}),
    timeout=60, context=CTX).read())

ONTEAM, BYID = {}, {}
for pid, p in ALL.items():
    if not isinstance(p, dict):
        continue
    if p.get("position") not in ("QB", "RB", "WR", "TE", "K"):
        continue
    nm = p.get("full_name")
    if not nm:
        continue
    rec = {"tm": p.get("team"), "st": p.get("status")}
    ONTEAM[norm(nm)] = rec
    if p.get("gsis_id"):
        BYID[p["gsis_id"]] = rec

# manual overrides -- Sleeper lags same-day transactions
OVR = {}
try:
    OVR = json.load(open("fa_override.json"))
    print("manual free-agent overrides: %d" % len(OVR))
except Exception:
    pass

B = json.load(open("site/_board.json"))
freed = []
for r in B["rows"]:
    if r.get("pos") not in ("QB", "RB", "WR", "TE", "K"):
        continue
    rec = BYID.get(r.get("pid")) or ONTEAM.get(norm(r.get("n")))
    if rec is None:
        rec = {"tm": None} if norm(r.get("n")) in OVR else None
    if rec is None:
        continue
    if rec["tm"] and norm(r.get("n")) not in OVR:
        continue
    # no NFL team -> he cannot score for anyone
    if (r.get("live") or 0) > 0 or (r.get("ros") or 0) > 0:
        freed.append((r.get("n"), r.get("pos"),
                      r.get("tm"), r.get("live")))
    for f in ("live", "live_lg", "base", "ros", "rosv",
              "vorp", "uvorp", "val", "uval", "floor",
              "ceil", "s_cons", "s_floor", "s_ceil",
              "s_ds", "s_upd"):
        if f in r:
            r[f] = 0.0
    r["wk"] = []
    r["gleft"] = 0
    r["tm"] = "FA"
    r["logo"] = ""
    r["inj"] = "Free Agent"
    r["free_agent"] = 1
    r["conf"] = "none"
    r["conf_why"] = ("not on an NFL roster - no projection "
                     "until he signs")

json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
n = sum(1 for r in B["rows"] if r.get("free_agent"))
print("free agents zeroed: %d" % n)
if freed:
    print("\nthese had live projections and were released:")
    for nm, pos, tm, lv in sorted(freed,
                                  key=lambda x: -(x[3] or 0)):
        print("   %-24s %-3s was %-4s  %.2f ppg -> 0"
              % (nm[:24], pos, tm, lv or 0))
else:
    print("(none of them were carrying a projection)")

# a released STARTER leaves his team without one
print("\n=== teams whose kicker is now a free agent ===")
k = [r for r in B["rows"] if r.get("pos") == "K"]
gone = [r for r in k if r.get("free_agent")]
for r in gone:
    print("   %-24s released" % r["n"][:24])
if not gone:
    print("   none")
