import json, ssl, certifi, datetime
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
LID = "1312181058833240064"
_A = datetime.datetime(2026, 9, 8,
                       tzinfo=datetime.timezone.utc)
CUR = max(1, min(18, (datetime.datetime.now(
    datetime.timezone.utc) - _A).days // 7 + 1))

def get(u):
    return json.loads(U.urlopen(U.Request(
        u, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=30, context=CTX).read())

B = "https://api.sleeper.app/v1/league/" + LID
lg = get(B)
rosters = get(B + "/rosters")
users = get(B + "/users")
UN = {u["user_id"]: (u.get("metadata", {}).get("team_name")
                     or u.get("display_name"))
      for u in users}
print("league: %s | teams %d | playoff spots %s"
      % (lg.get("name"), len(rosters),
         lg.get("settings", {}).get("playoff_teams")))
print("current week: %d" % CUR)

TEAMS = {}
for r in rosters:
    s = r.get("settings", {})
    TEAMS[r["roster_id"]] = {
        "rid": r["roster_id"],
        "name": UN.get(r.get("owner_id"), "team %d"
                       % r["roster_id"]),
        "w": s.get("wins", 0), "l": s.get("losses", 0),
        "t": s.get("ties", 0),
        "pf": s.get("fpts", 0) + s.get("fpts_decimal", 0) / 100,
        "pa": s.get("fpts_against", 0)
              + s.get("fpts_against_decimal", 0) / 100,
        "players": r.get("players") or [],
        "starters": r.get("starters") or [],
    }

# every week's matchups: results for played, pairings ahead
SCHED, RESULTS = {}, {}
for w in range(1, 18):
    try:
        m = get(B + "/matchups/%d" % w)
    except Exception:
        continue
    if not m:
        continue
    byid = {}
    for x in m:
        byid.setdefault(x.get("matchup_id"), []).append(x)
    pairs = []
    for mid, xs in byid.items():
        if len(xs) != 2 or mid is None:
            continue
        a, b = xs
        pairs.append([a["roster_id"], b["roster_id"]])
        if w < CUR:
            RESULTS.setdefault(w, []).append(
                {"a": a["roster_id"], "b": b["roster_id"],
                 "ap": a.get("points") or 0,
                 "bp": b.get("points") or 0})
    if pairs:
        SCHED[w] = pairs

played = sorted(RESULTS.keys())
ahead = [w for w in sorted(SCHED) if w >= CUR]
print("weeks played: %s" % played)
print("weeks remaining: %s" % ahead)

json.dump({"lid": LID, "cur": CUR,
           "spots": lg.get("settings", {}).get(
               "playoff_teams", 6),
           "teams": TEAMS, "sched": SCHED,
           "results": RESULTS},
          open("lgstate.json", "w"), separators=(",", ":"))
print("\nwrote lgstate.json")

print("\n=== ACTUAL STANDINGS ===")
st = sorted(TEAMS.values(),
            key=lambda x: (-x["w"], -x["pf"]))
print("  %-24s %6s %9s %9s" % ("TEAM", "REC", "PF", "PA"))
for t in st:
    print("  %-24s %3d-%-2d %9.1f %9.1f"
          % (t["name"][:24], t["w"], t["l"], t["pf"], t["pa"]))
