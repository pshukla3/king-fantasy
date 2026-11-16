import json, os
from datetime import datetime, timezone
import fpts

WK = fpts.nflweek()
ev = fpts.week_events(WK)
done = [e for e in ev if e["state"] == "post"]
print("week %d | %d scheduled, %d final"
      % (WK, len(ev), len(done)))
if not done:
    print("no completed games yet this week")

ALL = {}
for e in done:
    s = fpts.get(fpts.BASE + "summary?event=" + e["id"])
    r = fpts.score_summary(s)
    print("  %-12s %3d players" % (e["name"], len(r)))
    for nm, v in r.items():
        if nm not in ALL or v["p"] > ALL[nm]["p"]:
            ALL[nm] = v

PMAP = {"PK": "K", "K": "K", "QB": "QB", "RB": "RB",
        "FB": "RB", "WR": "WR", "TE": "TE"}
rows = []
for nm, v in ALL.items():
    if abs(v["p"]) < 0.05:
        continue
    rows.append({"name": nm, "tm": v["tm"],
                 "pos": PMAP.get(v["pos"], v["pos"] or "?"),
                 "pts": round(v["p"], 2)})
rows.sort(key=lambda x: -x["pts"])

BY = {}
for r in rows:
    BY.setdefault(r["pos"], []).append(r)

out = {"week": WK, "games": len(done),
       "updated": datetime.now(timezone.utc)
       .isoformat(timespec="seconds"),
       "overall": rows[:25],
       "byPos": {k: v[:12] for k, v in BY.items()}}
os.makedirs("site", exist_ok=True)
json.dump(out, open("site/_wk_leaders.json", "w"))

print("\n=== TOP 10 OVERALL (week %d) ===" % WK)
for r in rows[:10]:
    print("  %-24s %-3s %-4s %6.1f"
          % (r["name"][:24], r["pos"], r["tm"], r["pts"]))
for p in ("QB", "RB", "WR", "TE", "K"):
    z = BY.get(p, [])[:5]
    if not z:
        continue
    print("\n--- %s ---" % p)
    for r in z:
        print("  %-24s %-4s %6.1f"
              % (r["name"][:24], r["tm"], r["pts"]))
print("\nwrote site/_wk_leaders.json (%d players)"
      % len(rows))
