import json

S = json.load(open("site/_lgsched.json"))
print("type:", type(S).__name__)
if isinstance(S, dict):
    print("keys:", list(S.keys())[:20])
    k0 = list(S.keys())[0]
    print("S[%r] = %s" % (k0, json.dumps(S[k0])[:300]))
else:
    print("len:", len(S))
    print("S[0] =", json.dumps(S[0])[:300])

OUT = {}


def ids(g):
    out = []
    for x in g:
        if isinstance(x, dict):
            v = x.get("id", x.get("roster_id"))
        else:
            v = x
        if v is not None:
            out.append(int(v))
    return out


if isinstance(S, dict):
    for w, games in S.items():
        wk = int(str(w).replace("week", "").strip() or 0)
        rows = []
        for g in games:
            p = ids(g if isinstance(g, list) else [g])
            if len(p) == 2:
                rows.append(p)
        if rows:
            OUT[str(wk)] = rows
else:
    for g in S:
        wk = int(g.get("week", g.get("w", 0)))
        p = ids(g.get("teams", g.get("g", [])))
        if len(p) == 2:
            OUT.setdefault(str(wk), []).append(p)

json.dump(OUT, open("site/_musched.json", "w"),
          separators=(",", ":"))
print("\nweeks: %d" % len(OUT))
for w in sorted(OUT, key=lambda x: int(x))[:3]:
    print("  wk %s: %s" % (w, OUT[w]))
