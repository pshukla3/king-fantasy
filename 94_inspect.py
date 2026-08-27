import json, pandas as pd

U = json.load(open("ui_data.json"))
print("top-level keys: %s" % list(U.keys()))

T = U["teams"]
k0 = sorted(T.keys())[0]
print("\nteams: %d | sample key %r" % (len(T), k0))
for kk, vv in T[k0].items():
    if isinstance(vv, list):
        print("  %-12s list[%d]" % (kk, len(vv)))
        if vv:
            print("       item0 %s" % json.dumps(vv[0])[:200])
    elif isinstance(vv, dict):
        print("  %-12s dict %s" % (kk, list(vv.keys())[:8]))
    else:
        print("  %-12s %r" % (kk, vv))

P = U["players"]
print("\nplayers: %d" % len(P))
for i in list(P.keys())[:3]:
    print("  %s %s" % (i, json.dumps(P[i])[:240]))

cov = {}
for v in P.values():
    for kk in v:
        cov[kk] = cov.get(kk, 0) + 1
print("\nfield coverage (of %d players):" % len(P))
for kk, c in sorted(cov.items(), key=lambda x: -x[1]):
    print("  %-14s %5d" % (kk, c))

b = pd.read_csv("board_final.csv", low_memory=False)
print("\nboard_final cols: %s" % list(b.columns))
c = pd.read_csv("coaching_2026.csv")
print("coaching_2026: %d rows | cols %s" % (len(c), list(c.columns)))
