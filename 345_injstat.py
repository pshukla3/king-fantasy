import json, re, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
E = ("https://site.api.espn.com/apis/site/v2/"
     "sports/football/nfl/injuries")

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

r = U.Request(E, headers=H)
d = json.loads(U.urlopen(r, timeout=30, context=CTX).read())

# Out means zero. Not a projection - a fact.
ZERO = {"out", "injured reserve", "ir", "suspension",
        "suspended", "physically unable to perform",
        "pup", "non football injury", "doubtful"}
OUT = {}
seen = {}
for t in (d.get("injuries") or []):
    ab = t.get("abbreviation") or ""
    for i in (t.get("injuries") or []):
        a = i.get("athlete") or {}
        nm = a.get("displayName")
        if not nm:
            continue
        st = str(i.get("status") or "").strip()
        de = i.get("details") or {}
        seen[st] = seen.get(st, 0) + 1
        OUT[norm(nm)] = {
            "n": nm, "tm": ab, "status": st,
            "type": de.get("type") or "",
            "fant": de.get("fantasyStatus") or "",
            "mult": 0.0 if st.lower() in ZERO else None}

json.dump(OUT, open("site/_inj.json", "w"))
print("injury rows: %d | statuses: %s"
      % (len(OUT), seen))

T = json.load(open("site/_teams.json"))
hit = 0
print("\n=== ROSTERED PLAYERS WITH A STATUS ===")
for t in T["teams"]:
    rows = []
    for p in t["players"]:
        j = OUT.get(p["k"])
        if j and j["status"].lower() != "active":
            rows.append((p, j))
    if not rows:
        continue
    print("\n%s:" % t["name"])
    for p, j in rows:
        z = "-> 0.00" if j["mult"] == 0.0 else "-> ?"
        print("  %-24s %-5s %-12s %-10s %5.2f %s"
              % (p["n"][:24], p["pos"], j["status"],
                 j["type"][:10], p["ppg"], z))
        hit += 1
print("\n%d rostered players carrying a status" % hit)
