import json, re

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

B = json.load(open("site/_board.json"))
ROWS = B.get("rows", [])
SL = json.load(open("site/_slteams.json"))
TC = {norm(r["n"]): r for r in json.load(open("site/_tc.json"))}

WANT = ["Amon-Ra St. Brown", "Kyren Williams",
        "Malik Nabers", "DJ Moore", "Cam Skattebo"]

def find(name):
    k = norm(name)
    for r in ROWS:
        if norm(r["n"]) == k:
            return r
    # loose: last name + first initial
    p = k.split()
    for r in ROWS:
        q = norm(r["n"]).split()
        if q and p and q[-1] == p[-1] and q[0][:1] == p[0][:1]:
            return r
    return None

print("=== who owns each player ===")
own = {}
for t in SL.get("teams", []):
    for p in t.get("players", []):
        own[p.get("k") or norm(p.get("n"))] = t.get("owner")

print("%-22s %-5s %-4s %5s %6s %6s %6s %5s %6s %-22s"
      % ("PLAYER", "POS", "TM", "RK", "PROJ", "FLOOR",
         "CEIL", "TIER", "VORP", "OWNER"))
found = {}
for w in WANT:
    r = find(w)
    if not r:
        print("  %-22s NOT FOUND ON BOARD" % w)
        continue
    found[w] = r
    k = norm(r["n"])
    print("%-22s %-5s %-4s %5s %6s %6s %6s %5s %6s %-22s"
          % (r["n"][:22], r.get("pos"), r.get("tm"),
             r.get("rk"), r.get("live"), r.get("floor"),
             r.get("ceil"), r.get("tier"),
             r.get("vorp"), str(own.get(k, "FREE AGENT"))[:22]))

print("\n=== trade value table (_tc.json) ===")
for w in WANT:
    r = found.get(w)
    if not r:
        continue
    t = TC.get(norm(r["n"]))
    print("  %-22s g=%s rec=%s"
          % (r["n"][:22], t.get("g") if t else "-",
             t.get("rec") if t else "-"))

SIDE_A = ["Amon-Ra St. Brown", "Kyren Williams"]
SIDE_B = ["Malik Nabers", "DJ Moore", "Cam Skattebo"]

def total(names, field):
    s = 0.0
    for n in names:
        r = found.get(n)
        if r and r.get(field) is not None:
            s += float(r[field])
    return s

print("\n=== raw totals ===")
print("  %-28s %8s %8s %8s %8s"
      % ("", "PROJ", "FLOOR", "CEIL", "VORP"))
for lbl, side in (("A: ARSB + Kyren", SIDE_A),
                  ("B: Nabers + Moore + Skattebo", SIDE_B)):
    print("  %-28s %8.1f %8.1f %8.1f %8.2f"
          % (lbl, total(side, "live"), total(side, "floor"),
             total(side, "ceil"), total(side, "vorp")))
print("\n  Raw sums favour the 3-player side by construction"
      " -- you cannot start them all. Lineup impact below"
      " is the number that matters.")
