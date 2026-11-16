import json

D = json.load(open("site/_slteams.json"))
SLOTS = [s for s in D["slots"] if s != "BN"]
FLEX = {"FLEX": {"RB", "WR", "TE"},
        "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
        "WRRB_FLEX": {"RB", "WR"},
        "REC_FLEX": {"WR", "TE"}}
print("starting slots (%d): %s" % (len(SLOTS), SLOTS))

print("\n=== PLAYERS WITH NO PROJECTION ===")
n = 0
for t in D["teams"]:
    for p in t["players"]:
        if p["ppg"] <= 0:
            print("  %-24s %-4s %-4s  %s"
                  % (p["n"][:24], p["pos"], p["tm"],
                     t["owner"][:18]))
            n += 1
print("total: %d" % n)

def optimize(players, slots):
    pool = sorted(players, key=lambda x: -x["ppg"])
    used, line = set(), []
    for s in slots:
        if s in FLEX:
            continue
        ok = ({"DEF", "DST"} if s in ("DEF", "DST")
              else {s})
        pick = next((p for p in pool if p["pos"] in ok
                     and p["pid"] not in used), None)
        if pick:
            used.add(pick["pid"])
        line.append((s, pick))
    for s in slots:
        if s not in FLEX:
            continue
        pick = next((p for p in pool
                     if p["pos"] in FLEX[s]
                     and p["pid"] not in used), None)
        if pick:
            used.add(pick["pid"])
        line.append((s, pick))
    return line

me = D["teams"][0]
for t in D["teams"]:
    if t["owner"].startswith("Shukie"):
        me = t
        break

byid = {p["pid"]: p for p in me["players"]}
print("\n=== %s: CURRENT STARTERS ===" % me["owner"])
cur = 0.0
for pid in me["starters"]:
    p = byid.get(str(pid))
    if not p:
        print("  %-24s (not on roster?)" % pid)
        continue
    cur += p["ppg"]
    print("  %-24s %-4s %-4s %6.2f %s"
          % (p["n"][:24], p["pos"], p["tm"], p["ppg"],
             p.get("inj", "")))
print("  %-24s        %6.2f" % ("CURRENT TOTAL", cur))

print("\n=== OPTIMAL (2 FLEX) ===")
tot = 0.0
for s, p in optimize(me["players"], SLOTS):
    if p:
        tot += p["ppg"]
        print("  %-6s %-24s %-4s %6.2f %s"
              % (s, p["n"][:24], p["tm"], p["ppg"],
                 p.get("inj", "")))
    else:
        print("  %-6s %s" % (s, "-- none eligible --"))
print("  %-6s %-24s      %6.2f" % ("TOTAL", "", tot))
print("\n  gain vs current: %+.2f" % (tot - cur))
