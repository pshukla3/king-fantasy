import json
import shutil

P = "sleeper_players.json"
PJ = json.load(open(P))
k0 = list(PJ.keys())[0]
print("keys in a value: %s" % list(PJ[k0].keys()))

if "full_name" in PJ[k0]:
    print("already in standard form, nothing to do")
else:
    shutil.copy(P, P + ".abbrev.bak")
    NM = {"n": "full_name", "p": "position", "t": "team",
          "fn": "first_name", "ln": "last_name",
          "no": "number", "s": "status"}
    OUT = {}
    for k, v in PJ.items():
        d = {}
        for a, b in NM.items():
            if a in v:
                d[b] = v[a]
        for a in v:
            if a not in NM:
                d[a] = v[a]
        OUT[k] = d
    json.dump(OUT, open(P, "w"))
    print("backed up to %s.abbrev.bak" % P)
    print("rewrote %d players with standard keys" % len(OUT))
    PJ = OUT

n = 0
for k, v in list(PJ.items())[:400000]:
    if v.get("full_name") and v.get("position"):
        n += 1
print("players with name+position: %d" % n)
print("\nspot check:")
for x in ["4227", "5872", "6801", "11560"]:
    d = PJ.get(x, {})
    print("  %-8s %-24s %-4s %s"
          % (x, str(d.get("full_name"))[:24],
             d.get("position"), d.get("team")))
assert n > 1000, "still not resolving names"
print("\nOK")
