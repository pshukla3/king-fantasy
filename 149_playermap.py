import json
import os
import ssl
import urllib.request as U
import certifi

CTX = ssl.create_default_context(cafile=certifi.where())
P = "sleeper_players.json"
LG = "1312181058833240064"


def get(u):
    with U.urlopen(u, context=CTX, timeout=120) as r:
        return json.loads(r.read().decode())


RS = get("https://api.sleeper.app/v1/league/%s/rosters" % LG)
pids = []
for r in RS:
    pids += [str(x) for x in (r.get("players") or [])]
print("roster player ids: %d" % len(pids))
print("sample: %s" % pids[:5])

ok = False
if os.path.exists(P):
    try:
        old = json.load(open(P))
        if isinstance(old, dict):
            hit = sum(1 for x in pids[:20] if x in old)
            print("existing file: %d keys, %d/20 match"
                  % (len(old), hit))
            ok = hit >= 15
        else:
            print("existing file is %s not dict"
                  % type(old).__name__)
    except Exception as e:
        print("existing file unreadable: %s" % e)
else:
    print("no existing file")

if not ok:
    print("\nfetching full player map (~10MB)...")
    PJ = get("https://api.sleeper.app/v1/players/nfl")
    print("  got %d players" % len(PJ))
    json.dump(PJ, open(P, "w"))
    print("  wrote %s" % P)
else:
    PJ = old
    print("existing map is fine")

hit = sum(1 for x in pids if x in PJ)
print("\nMATCH: %d of %d (%.0f%%)"
      % (hit, len(pids), 100.0 * hit / max(len(pids), 1)))
assert hit > len(pids) * 0.9, "player map still broken"
print("\nsample resolved:")
for x in pids[:8]:
    d = PJ.get(x, {})
    nm = d.get("full_name") or (
        str(d.get("first_name", "")) + " "
        + str(d.get("last_name", ""))).strip()
    print("  %-10s %-24s %-4s %s"
          % (x, nm[:24], d.get("position", "?"),
             d.get("team", "?")))
print("\nOK - now rerun 148_league_data.py")
