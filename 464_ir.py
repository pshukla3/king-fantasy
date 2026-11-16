import json, re, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
def norm(s):
    s = str(s or "").lower(); s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

print("pulling live injury designations from Sleeper")
ALL = json.loads(U.urlopen(U.Request(
    "https://api.sleeper.app/v1/players/nfl",
    headers={"User-Agent": "Mozilla/5.0"}),
    timeout=60, context=CTX).read())

# IR and PUP mean a minimum absence, not a designation
# you play through. Out means this week.
GONE = {"IR": 5, "PUP": 5, "NA": 5, "Sus": 5,
        "IR-R": 5, "Out": 1, "Doubtful": 1}
STATUS = {}
for pid, p in ALL.items():
    if not isinstance(p, dict):
        continue
    st = p.get("injury_status")
    nm = p.get("full_name")
    if not st or not nm or st == "Active":
        continue
    STATUS[norm(nm)] = {
        "n": nm, "st": st, "tm": p.get("team"),
        "pos": p.get("position"),
        "body": p.get("injury_body_part") or "",
        "weeks_out": GONE.get(st, 0),
    }
print("players with a designation: %d" % len(STATUS))
sea = {k: v for k, v in STATUS.items()
       if v["weeks_out"] >= 99}
print("out long-term (IR/PUP/NA/Sus): %d" % len(sea))

CUR = 3
P = json.load(open("site/_projweek.json"))
zeroed = 0
for k, v in P.items():
    s = STATUS.get(k)
    if not s:
        continue
    w_out = s["weeks_out"]
    if w_out <= 0:
        continue
    for wkrow in v["wk"]:
        if wkrow["w"] <= CUR:
            continue
        if wkrow["w"] <= CUR + w_out:
            wkrow["m"] = 0.0
            wkrow["f"] = 0.0
            wkrow["c"] = 0.0
            wkrow["p20"] = 0.0
    played = [x["m"] for x in v["wk"]
              if x["o"] != "BYE" and x["w"] > CUR]
    v["season"] = round(sum(played) / len(played), 2) \
        if played else 0.0
    v["inj"] = s["st"]
    v["inj_body"] = s["body"]
    zeroed += 1
json.dump(P, open("site/_projweek.json", "w"),
          separators=(",", ":"))
print("zeroed future weeks for %d injured players" % zeroed)

# re-rank the board on our own projection, which just
# beat consensus 0.657 to 0.619 on three weeks of data
B = json.load(open("site/_board.json"))
rows = B["rows"]
for r in rows:
    k = norm(r["n"])
    s = STATUS.get(k)
    v = P.get(k)
    if v:
        r["live"] = v["season"]
    if s:
        r["inj"] = s["st"]
    r["_old_rk"] = r.get("rk")

live = [r for r in rows if r.get("live") is not None]
live.sort(key=lambda r: -(r["live"] or 0))
for i, r in enumerate(live, 1):
    r["rk"] = i
bypos = {}
for r in live:
    p = r.get("pos")
    bypos.setdefault(p, 0)
    bypos[p] += 1
    r["posrk"] = bypos[p]
json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
print("re-ranked %d players on projection" % len(live))

moves = [(r["_old_rk"] - r["rk"], r) for r in live
         if r.get("_old_rk")]
moves.sort(key=lambda x: x[0])
print("\n=== biggest FALLS ===")
print("  %-24s %-4s %6s %6s %7s  %s"
      % ("PLAYER", "POS", "WAS", "NOW", "PROJ", "WHY"))
for d, r in moves[:15]:
    print("  %-24s %-4s %6s %6d %7.1f  %s"
          % (r["n"][:24], r.get("pos"), r["_old_rk"],
             r["rk"], r["live"] or 0, r.get("inj") or ""))
print("\n=== biggest RISES ===")
for d, r in moves[-15:][::-1]:
    print("  %-24s %-4s %6s %6d %7.1f"
          % (r["n"][:24], r.get("pos"), r["_old_rk"],
             r["rk"], r["live"] or 0))
