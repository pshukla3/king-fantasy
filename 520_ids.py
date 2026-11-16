import json
import nflreadpy as nfl
from namekey import nk, dk, tfix

print("building the player ID crosswalk")
X = nfl.load_ff_playerids().to_pandas()
R = nfl.load_rosters([2026]).to_pandas()

CANON, BYSLP, BYESPN, BYNAME = {}, {}, {}, {}

def put(gsis, name, pos, team, slp, espn):
    if not gsis or gsis != gsis:
        return
    g = str(gsis)
    rec = CANON.setdefault(g, {"id": g, "n": name,
                               "pos": pos, "tm": tfix(team),
                               "sid": None, "eid": None})
    if name:
        rec["n"] = name
    if pos:
        rec["pos"] = pos
    if team:
        rec["tm"] = tfix(team)
    if slp and slp == slp:
        rec["sid"] = str(int(float(slp)))
        BYSLP[rec["sid"]] = g
    if espn and espn == espn:
        rec["eid"] = str(int(float(espn)))
        BYESPN[rec["eid"]] = g
    if name:
        BYNAME.setdefault(nk(name), g)

# official 2026 rosters first -- current teams win
for _, r in R.iterrows():
    put(r.get("gsis_id"), r.get("full_name"),
        r.get("position"), r.get("team"),
        r.get("sleeper_id"), r.get("espn_id"))
print("from 2026 rosters: %d players" % len(CANON))

for _, r in X.iterrows():
    put(r.get("gsis_id"), r.get("name"), r.get("position"),
        r.get("team"), r.get("sleeper_id"), r.get("espn_id"))
print("after crosswalk:   %d players" % len(CANON))

# team defenses: Sleeper uses the team code as the id
TEAMS = sorted({v["tm"] for v in CANON.values()
                if v.get("tm") and len(str(v["tm"])) <= 3})
for t in TEAMS:
    g = "DEF-" + t
    CANON[g] = {"id": g, "n": t + " Defense", "pos": "DEF",
                "tm": t, "sid": t, "eid": None}
    BYSLP[t] = g
    BYNAME[dk(t + " Defense")] = g
    BYNAME[dk(t)] = g
print("plus %d team defenses" % len(TEAMS))

json.dump({"canon": CANON, "by_sleeper": BYSLP,
           "by_espn": BYESPN, "by_name": BYNAME},
          open("site/_ids.json", "w"),
          separators=(",", ":"))
print("wrote site/_ids.json")

# stamp our id + the sleeper id onto every board row
B = json.load(open("site/_board.json"))
hit = miss = fixed = 0
for row in B["rows"]:
    g = row.get("pid")
    if not g or g not in CANON:
        g = BYNAME.get(nk(row.get("n") or ""))
        if not g and (row.get("pos") or "") in ("DEF", "DST"):
            g = BYNAME.get(dk(row.get("n") or ""))
        if g:
            row["pid"] = g
            fixed += 1
    if g and g in CANON:
        row["sid"] = CANON[g].get("sid")
        hit += 1
    else:
        miss += 1
json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
print("\nboard: %d rows carry our id (%d repaired), "
      "%d unresolved" % (hit, fixed, miss))
n_sid = sum(1 for r in B["rows"] if r.get("sid"))
print("rows with a sleeper id: %d" % n_sid)

for nm in ("Kenneth Walker III", "Harold Fannin Jr.",
           "Deebo Samuel Sr."):
    r = [x for x in B["rows"] if x.get("n") == nm]
    if r:
        r = r[0]
        print("  %-22s pid %-12s sid %s"
              % (nm[:22], r.get("pid"), r.get("sid")))
