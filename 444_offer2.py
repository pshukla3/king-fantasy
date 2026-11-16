import json, re

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

B = json.load(open("site/_board.json"))
SL = json.load(open("site/_slteams.json"))
TC = {norm(x["n"]): x for x in json.load(open("site/_tc.json"))}
BM = {norm(r["n"]): r for r in B["rows"]
      if r.get("pos") not in ("DEF", "DST")}
BD = {str(r.get("tm")): r for r in B["rows"]
      if r.get("pos") in ("DEF", "DST")}
SLOTS = [s for s in SL.get("slots", [])
         if s not in ("BN", "IR", "TAXI")]
EL = {"QB": ["QB"], "RB": ["RB"], "WR": ["WR"],
      "TE": ["TE"], "K": ["K"], "DEF": ["DEF", "DST"],
      "FLEX": ["RB", "WR", "TE"]}
MYID = 1

GIVE = ["Deebo Samuel", "Tee Higgins", "George Pickens",
        "Omarion Hampton"]
GET = ["Puka Nacua", "Cam Skattebo", "DJ Moore"]

def proj(p):
    b = (BD.get(p.get("tm")) if p.get("pos") in ("DEF", "DST")
         else BM.get(p.get("k") or norm(p.get("n"))))
    return float(b["live"]) if b and b.get("live") is not None \
        else float(p.get("ppg") or 0)

def best(players, show=False):
    pool = sorted(players, key=lambda x: -proj(x))
    used, tot, flex, out = set(), 0.0, [], []
    for s in SLOTS:
        if "FLEX" in s:
            flex.append(s); continue
        for p in pool:
            k = p.get("pid") or p["n"]
            if k in used: continue
            if p.get("pos") in EL.get(s, []):
                used.add(k); tot += proj(p)
                out.append((s, p["n"], proj(p))); break
    for s in flex:
        for p in pool:
            k = p.get("pid") or p["n"]
            if k in used: continue
            if p.get("pos") in EL.get(s, []):
                used.add(k); tot += proj(p)
                out.append((s, p["n"], proj(p))); break
    if show:
        for s, n, v in out:
            print("    %-6s %-24s %6.2f" % (s, n[:24], v))
    return tot

me = next(t for t in SL["teams"] if int(t["id"]) == MYID)
print("team: %s\n" % me["owner"])

def side(names, lbl):
    tot = 0
    print("%s:" % lbl)
    for n in names:
        x = TC.get(norm(n))
        if not x:
            cand = [v for k, v in TC.items()
                    if k.split()[-1] == norm(n).split()[-1]]
            x = cand[0] if cand else None
        if not x:
            print("  %-22s NOT FOUND" % n); continue
        tot += x["val"]
        print("  %-22s %-4s proj %5.1f  vorp %5.1f  "
              "value %6d" % (x["n"][:22], x["p"], x["g"],
                             x["vw"], x["val"]))
    print("  %-22s %38d\n" % ("TOTAL", tot))
    return tot

a = side(GIVE, "YOU GIVE")
b = side(GET, "YOU GET")
print("  value net %+d\n" % (b - a))

gk = [norm(x) for x in GIVE]
have = [p for p in me["players"]
        if (p.get("k") or norm(p["n"])) in gk]
print("you own %d of the %d you'd send" % (len(have), len(GIVE)))
got = []
for g in GET:
    r = BM.get(norm(g))
    if r:
        got.append({"pid": "NEW_" + norm(g), "n": r["n"],
                    "pos": r["pos"], "tm": r["tm"]})

print("\n=== LINEUP BEFORE ===")
before = best(me["players"], show=True)
print("    %-31s %6.2f" % ("TOTAL", before))
keep = [p for p in me["players"] if p not in have]
print("\n=== LINEUP AFTER ===")
after = best(keep + got, show=True)
print("    %-31s %6.2f" % ("TOTAL", after))
print("\n  weekly change %+.2f" % (after - before))
print("  roster %d -> %d" % (len(me["players"]),
                             len(keep) + len(got)))

print("\n=== depth by position ===")
for lbl, ros in (("before", me["players"]),
                 ("after", keep + got)):
    for pos in ("RB", "WR"):
        g = sorted([p for p in ros if p.get("pos") == pos],
                   key=lambda x: -proj(x))
        print("  %-6s %-3s: %s" % (lbl, pos,
              ", ".join("%s %.1f" % (p["n"].split()[-1],
                                     proj(p)) for p in g[:5])))
