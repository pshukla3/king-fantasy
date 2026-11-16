import json
import ssl
import urllib.request
import certifi

CTX = ssl.create_default_context(cafile=certifi.where())
LG = "1312181058833240064"

def get(u):
    r = urllib.request.Request(
        u, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(r, context=CTX,
                                timeout=40) as f:
        return json.load(f)

L = get("https://api.sleeper.app/v1/league/%s" % LG)
print("league: %s" % L.get("name"))
rp = L.get("roster_positions") or []
print("roster_positions (%d): %s" % (len(rp), rp))
print("starting slots: %s"
      % [x for x in rp if x not in ("BN", "IR", "TAXI")])

R = get("https://api.sleeper.app/v1/league/%s/rosters" % LG)
print("\nrosters: %d" % len(R))
r0 = [x for x in R if int(x.get("roster_id", 0)) == 1]
r0 = r0[0] if r0 else R[0]
print("roster keys: %s" % sorted(r0.keys()))
print("\nroster_id %s" % r0.get("roster_id"))
print("  players  : %d" % len(r0.get("players") or []))
print("  starters : %s" % (r0.get("starters") or []))
print("  reserve  : %s" % (r0.get("reserve") or []))
print("  taxi     : %s" % (r0.get("taxi") or []))

PJ = json.load(open("sleeper_players.json"))
st = r0.get("starters") or []
slots = [x for x in rp if x not in ("BN", "IR", "TAXI")]
print("\n=== YOUR ACTUAL STARTING LINEUP ===")
for i, pid in enumerate(st):
    d = PJ.get(str(pid), {})
    sl = slots[i] if i < len(slots) else "?"
    print("  %-5s %-24s %-4s %s"
          % (sl, str(d.get("full_name"))[:24],
             d.get("position"), d.get("team")))

bench = [p for p in (r0.get("players") or [])
         if p not in st]
print("\n=== YOUR BENCH ===")
for pid in bench:
    d = PJ.get(str(pid), {})
    print("  %-24s %-4s %s"
          % (str(d.get("full_name"))[:24],
             d.get("position"), d.get("team")))

D = json.load(open("league_data.json"))
me = [t for t in D["rosters"]
      if t["roster_id"] == 1]
if me:
    print("\n=== WHAT THE SITE SHOWS NOW ===")
    print("  (no starter/bench split, byes all zero)")
    for p in me[0]["players"][:6]:
        print("  %-24s %-4s %6.2f  bye %s"
              % (p["name"][:24], p["pos"], p["ppg"],
                 p.get("bye")))
