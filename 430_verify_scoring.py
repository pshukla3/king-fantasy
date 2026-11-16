import json, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
HD = {"User-Agent": "Mozilla/5.0"}


def get(u):
    return json.loads(U.urlopen(
        U.Request(u, headers=HD), timeout=30,
        context=CTX).read())


S = json.load(open("site/_scoring.json"))
PM = json.load(open("site/_pmap.json"))

ST = get("https://api.sleeper.app/v1/stats/nfl/"
         "regular/2026/1")
print("sleeper stat rows, week 1: %d" % len(ST))


def score(st):
    """points = sum(setting * stat) over shared keys."""
    t = 0.0
    used = []
    for k, v in (st or {}).items():
        w = S.get(k)
        if w and v:
            t += w * v
            used.append((k, v, w, w * v))
    return t, used


# Which stat keys actually carry weight in this league?
keys = set()
for pid, st in ST.items():
    for k in st:
        if S.get(k):
            keys.add(k)
print("scoring-relevant keys present: %d" % len(keys))
print("  " + ", ".join(sorted(keys)[:26]))

print("\n=== top 12 by our exact formula ===")
rows = []
for pid, st in ST.items():
    t, _ = score(st)
    m = PM.get(str(pid)) or {}
    rows.append((t, m.get("n", pid), m.get("p", "?"),
                 m.get("t", ""), st.get("pts_ppr")))
rows.sort(reverse=True)
print("  %-24s %-4s %-4s %8s %8s %7s"
      % ("PLAYER", "POS", "TM", "OURS", "SLEEPER", "DIFF"))
for t, n, p, tm, ppr in rows[:12]:
    d = ("" if ppr is None else "%+.2f" % (t - ppr))
    print("  %-24s %-4s %-4s %8.2f %8s %7s"
          % (str(n)[:24], p, tm, t,
             ("%.2f" % ppr) if ppr is not None else "-", d))

print("\n=== agreement with Sleeper's own pts_ppr ===")
n = ok = 0
worst = []
for pid, st in ST.items():
    ppr = st.get("pts_ppr")
    if ppr is None:
        continue
    t, _ = score(st)
    n += 1
    d = abs(t - ppr)
    if d < 0.02:
        ok += 1
    else:
        m = PM.get(str(pid)) or {}
        worst.append((d, m.get("n", pid), m.get("p", "?"),
                      t, ppr))
print("  %d of %d match within 0.02  (%.1f%%)"
      % (ok, n, 100.0 * ok / n if n else 0))
worst.sort(reverse=True)
print("  biggest gaps (expected for K and DEF, which"
      " pts_ppr does not cover the same way):")
for d, nm, p, t, ppr in worst[:10]:
    print("    %-22s %-4s ours %7.2f  ppr %7.2f  d %.2f"
          % (str(nm)[:22], p, t, ppr, d))

print("\n=== hand check: a 10-yard TD reception ===")
ex = {"rec": 1, "rec_yd": 10, "rec_td": 1}
t, used = score(ex)
for k, v, w, c in used:
    print("   %-10s %6s x %-5s = %6.2f" % (k, v, w, c))
print("   TOTAL = %.2f   (expect 8.00)" % t)

print("\n=== hand check: a kicker with a 52-yarder ===")
ex2 = {"fgm_30_39": 1, "fgm_50p": 1, "xpm": 2,
       "fgmiss": 1}
t2, used2 = score(ex2)
for k, v, w, c in used2:
    print("   %-10s %6s x %-5s = %6.2f" % (k, v, w, c))
print("   TOTAL = %.2f   (3 + 5 + 2 - 1 = 9.00)" % t2)
