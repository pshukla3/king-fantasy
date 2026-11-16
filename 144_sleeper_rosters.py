import json
import ssl
import urllib.request as U
import certifi
import pandas as pd

LG = "1312181058833240064"
CTX = ssl.create_default_context(cafile=certifi.where())


def get(u):
    with U.urlopen(u, context=CTX, timeout=30) as r:
        return json.loads(r.read().decode())


base = "https://api.sleeper.app/v1/league/" + LG
RS = get(base + "/rosters")
US = get(base + "/users")
uname = {u["user_id"]: u.get("display_name", "?")
         for u in US}
tname = {}
for u in US:
    md = u.get("metadata") or {}
    tname[u["user_id"]] = md.get(
        "team_name") or u.get("display_name", "?")
print("rosters %d | users %d" % (len(RS), len(US)))

PJ = json.load(open("sleeper_players.json"))
rows = []
for r in RS:
    rid = r["roster_id"]
    ow = r.get("owner_id")
    for pid in (r.get("players") or []):
        p = PJ.get(str(pid), {})
        rows.append({
            "roster_id": rid,
            "owner": uname.get(ow, "?"),
            "team_name": tname.get(ow, "?"),
            "sleeper_id": pid,
            "name": p.get("full_name")
            or (str(p.get("first_name", "")) + " "
                + str(p.get("last_name", ""))).strip(),
            "pos": p.get("position"),
            "nfl": p.get("team")})
L = pd.DataFrame(rows)
L.to_csv("league_rosters.csv", index=False)
print("\n=== LEAGUE ROSTERS ===")
for rid, g in L.groupby("roster_id"):
    t = g.iloc[0]
    mine = "  <-- YOU" if rid == 1 else ""
    print("\n  [%d] %s (%s) %d players%s"
          % (rid, t["team_name"], t["owner"],
             len(g), mine))
    for _, p in g.sort_values("pos").iterrows():
        print("      %-4s %-24s %s"
              % (p["pos"], str(p["name"])[:24],
                 p["nfl"]))
print("\nwrote league_rosters.csv (%d rows)" % len(L))
