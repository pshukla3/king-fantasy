import json, re, os

B = json.load(open("site/_board.json"))
ROWS = B.get("rows", [])
N = json.load(open("site/_news.json"))
ITEMS = N.get("items", []) if isinstance(N, dict) else N
print("news items: %d | board players: %d"
      % (len(ITEMS), len(ROWS)))


def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


# Last name alone is too noisy (Smith, Williams).
# Require first+last, or a distinctive last name.
COMMON = set("""smith williams johnson jones brown davis
miller wilson moore taylor anderson thomas jackson white
harris martin thompson robinson clark lewis walker hall
allen young king wright hill green adams baker""".split())

OUT = {}
for r in ROWS:
    nm = r.get("n") or ""
    k = norm(nm)
    parts = k.split()
    if len(parts) < 2:
        continue
    first, last = parts[0], parts[-1]
    hits = []
    for it in ITEMS:
        t = it.get("t") or ""
        body = norm(t + " " + str(it.get("d") or ""))
        ok = False
        if k in body:
            ok = True
        elif last not in COMMON and last in body.split():
            ok = True
        elif (first[:1] + " " + last) in body:
            ok = True
        if ok:
            hits.append({
                "t": t[:180],
                "u": it.get("u"),
                "s": it.get("s"),
                "d": str(it.get("d") or "")[:200],
            })
    if hits:
        OUT[k] = {"n": nm, "items": hits[:6]}

# Preserve hand-curated timeline entries if present.
if os.path.exists("site/_pnews.json"):
    try:
        old = json.load(open("site/_pnews.json"))
        for k, v in old.items():
            if isinstance(v, dict) and v.get("weeks"):
                OUT.setdefault(k, {}).update(
                    {"weeks": v.get("weeks"),
                     "kind": v.get("kind"),
                     "src": v.get("src"),
                     "line": v.get("line"),
                     "n": v.get("n", OUT.get(k, {}).get("n"))})
    except Exception as e:
        print("  (could not merge old _pnews: %s)" % e)

json.dump(OUT, open("site/_pnews.json", "w"),
          separators=(",", ":"))
tot = sum(len(v.get("items", [])) for v in OUT.values())
print("players with news: %d | linked items: %d"
      % (len(OUT), tot))
for k in list(OUT)[:6]:
    v = OUT[k]
    print("  %-22s %d  %s"
          % (v.get("n", k), len(v.get("items", [])),
             (v.get("items") or [{}])[0].get("t", "")[:60]))
