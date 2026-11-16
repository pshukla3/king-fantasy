import json, sys

P = "site/_wkproj.json"
J = json.load(open(P))
bad = [k for k in J if not str(k).isdigit()]
if bad:
    print("!! _wkproj.json has %d non-week keys" % len(bad))
    print("   (it is the FROZEN weekly snapshot archive,")
    print("    keyed by week number -- player projections")
    print("    belong in _projweek.json)")
    for k in bad[:6]:
        print("     %s" % k)
    for k in bad:
        del J[k]
    json.dump(J, open(P, "w"), separators=(",", ":"))
    print("   cleaned -> keys now %s"
          % sorted(J.keys(), key=int))
else:
    print("_wkproj.json clean: weeks %s"
          % sorted(J.keys(), key=int))
