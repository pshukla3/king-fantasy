import json, re

D = json.load(open("league_data.json"))
try:
    INJ = json.load(open("site/_inj.json"))
except IOError:
    INJ = {}
    print("!! site/_inj.json missing - run 345 first")
try:
    ADJ = json.load(open("site/_projadj.json"))
except IOError:
    ADJ = {}
    print("!! site/_projadj.json missing - run 347 first")
print("injury statuses %d | proj adjustments %d"
      % (len(INJ), len(ADJ)))
print("=== league block ===")
print(json.dumps(D.get("league", {}), indent=1)[:600])
tm = D.get("teams") or []
if tm:
    print("\n=== teams[0] keys ===")
    print(list(tm[0].keys()))
    print(json.dumps(tm[0], indent=1)[:700])

SLOTS = None
for path in (D.get("league", {}).get("roster_positions"),
             D.get("league", {}).get("roster_pos"),
             D.get("roster_positions")):
    if path:
        SLOTS = list(path)
        break
if not SLOTS:
    SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE",
             "FLEX", "K", "DEF"]
    print("\n!! roster_positions not found, using default")
print("\nslots: %s" % SLOTS)

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

START = {}
for t in tm:
    rid = t.get("roster_id")
    st = t.get("starters") or []
    if rid is not None and st:
        START[str(rid)] = st

out = {"slots": SLOTS, "my": D.get("my_roster_id"),
       "teams": []}
for r in D.get("rosters", []):
    ps = []
    for p in r.get("players", []):
        ps.append({"n": p.get("name"), "k": norm(p.get("name")),
                   "pos": p.get("pos"), "nfl": p.get("nfl"),
                   "ppg": round(float(p.get("ppg") or 0), 2),
                   "pid": p.get("pid")})
    for p in ps:
        j = INJ.get(p["k"])
        a = ADJ.get(p["k"])
        p["inj"] = (j or {}).get("status", "")
        p["injtype"] = (j or {}).get("type", "")
        p["ppg0"] = p["ppg"]
        if a:
            p["m"] = float(a.get("m", 1.0))
            p["ppg"] = round(p["ppg0"] * p["m"], 2)
            # what he is worth if he suits up
            p["ppg_if"] = round(
                p["ppg0"] * (0.0 if p["m"] == 0 else 0.95), 2)
        else:
            p["m"] = 1.0
            p["ppg_if"] = p["ppg0"]
    ps.sort(key=lambda x: -x["ppg"])
    out["teams"].append({
        "id": r.get("roster_id"), "name": r.get("name"),
        "owner": r.get("owner"),
        "proj": r.get("proj"),
        "starters": START.get(str(r.get("roster_id")), []),
        "players": ps})

json.dump(out, open("site/_teams.json", "w"))
print("\nwrote site/_teams.json | %d teams, %d players"
      % (len(out["teams"]),
         sum(len(t["players"]) for t in out["teams"])))
print("starters present for %d teams"
      % sum(1 for t in out["teams"] if t["starters"]))

# optimal lineup check on my team
FLEX = {"FLEX": ("RB", "WR", "TE"),
        "WRRB_FLEX": ("RB", "WR"),
        "REC_FLEX": ("WR", "TE"),
        "SUPER_FLEX": ("QB", "RB", "WR", "TE")}

def optimize(players, slots):
    pool = sorted(players, key=lambda x: -x["ppg"])
    used, line = set(), []
    for s in slots:
        if s in FLEX:
            continue
        allow = ({"DEF", "DST"} if s in ("DEF", "DST")
                 else {s})
        pick = next((p for p in pool
                     if p["pos"] in allow
                     and p["n"] not in used), None)
        if pick:
            used.add(pick["n"])
        line.append((s, pick))
    for s in slots:
        if s not in FLEX:
            continue
        ok = FLEX[s]
        pick = next((p for p in pool
                     if p["pos"] in ok
                     and p["n"] not in used), None)
        if pick:
            used.add(pick["n"])
        line.append((s, pick))
    return line

me = next((t for t in out["teams"]
           if t["id"] == out["my"]), out["teams"][0])
print("\n=== OPTIMAL LINEUP: %s ===" % me["name"])
tot = 0.0
for s, p in optimize(me["players"], SLOTS):
    if p:
        tot += p["ppg"]
        ex = ""
        if p.get("m", 1.0) < 1.0:
            ex = "(%.2f if active) %s" % (
                p.get("ppg_if", 0), p.get("inj", ""))
        print("  %-6s %-24s %-4s %5.2f  %s"
              % (s, p["n"][:24], p["nfl"], p["ppg"], ex))
    else:
        print("  %-6s %-24s" % (s, "-- none eligible --"))
print("  %-6s %-24s      %5.2f" % ("TOTAL", "", tot))
