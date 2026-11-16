import json, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
LG = "1312181058833240064"
S = "https://api.sleeper.app/v1/"

def g(u):
    return json.loads(U.urlopen(U.Request(u, headers=H),
                      timeout=25, context=CTX).read())

lg = g(S + "league/" + LG)
sc = lg.get("scoring_settings") or {}
print("league: %s | season %s | week? %s"
      % (lg.get("name"), lg.get("season"),
         lg.get("settings", {}).get("leg")))
print("\n=== DST-RELEVANT SCORING SETTINGS ===")
for k in sorted(sc):
    if any(t in k for t in ("def", "pts_allow", "sack",
                            "int", "ff", "fum", "safe",
                            "blk", "yds_allow")):
        print("  %-22s %s" % (k, sc[k]))

M = g(S + "league/%s/matchups/1" % LG)
print("\nmatchup entries: %d" % len(M))
tot = {}
for m in M:
    pp = m.get("players_points") or {}
    for pid, v in pp.items():
        if v:
            tot[pid] = v
print("players with points: %d" % len(tot))

# defenses use team abbreviation as the player id
print("\n=== DST POINTS AS SLEEPER SCORES THEM ===")
for pid, v in sorted(tot.items(), key=lambda x: -x[1]):
    if pid.isalpha() and len(pid) <= 4:
        print("  %-5s %6.2f" % (pid, v))

print("\n=== TOP 12 SCORERS (any position) ===")
for pid, v in sorted(tot.items(), key=lambda x: -x[1])[:12]:
    print("  %-10s %6.2f" % (pid, v))

print("\n=== MY TEAM ===")
mine = [m for m in M
        if m.get("roster_id") == json.load(
            open("league_data.json")).get("my_roster_id")]
for m in mine:
    print("  roster %s | total %.2f"
          % (m.get("roster_id"), m.get("points") or 0))
    print("  starters: %s" % (m.get("starters") or [])[:12])
    sp = m.get("starters_points") or []
    print("  starters_points: %s" % sp)
