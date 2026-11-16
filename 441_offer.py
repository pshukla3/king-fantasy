import json, re

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

B = json.load(open("site/_board.json"))
SL = json.load(open("site/_slteams.json"))
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

def proj(p):
    b = (BD.get(p.get("tm")) if p.get("pos") in ("DEF", "DST")
         else BM.get(p.get("k") or norm(p.get("n"))))
    return float(b["live"]) if b and b.get("live") is not None \
        else float(p.get("ppg") or 0)

def best(players, show=False):
    pool = sorted(players, key=lambda x: -proj(x))
    used, tot, flex, picked = set(), 0.0, [], []
    for s in SLOTS:
        if "FLEX" in s:
            flex.append(s); continue
        for p in pool:
            k = p.get("pid") or p["n"]
            if k in used: continue
            if p.get("pos") in EL.get(s, []):
                used.add(k); tot += proj(p)
                picked.append((s, p["n"], proj(p))); break
    for s in flex:
        for p in pool:
            k = p.get("pid") or p["n"]
            if k in used: continue
            if p.get("pos") in EL.get(s, []):
                used.add(k); tot += proj(p)
                picked.append((s, p["n"], proj(p))); break
    if show:
        for s, n, v in picked:
            print("    %-6s %-24s %6.2f" % (s, n[:24], v))
    return tot

me = None
for t in SL["teams"]:
    if int(t["id"]) == MYID:
        me = t
print("your team: %s (%d players)"
      % (me["owner"], len(me["players"])))

GIVE = ["Tee Higgins", "George Pickens", "Deebo Samuel",
        "Josh Downs"]
GET = ["Puka Nacua", "DJ Moore", "Jakobi Meyers"]

gk = [norm(x) for x in GIVE]
have = [p for p in me["players"]
        if (p.get("k") or norm(p["n"])) in gk]
print("\nof the %d you would give, you own %d:"
      % (len(GIVE), len(have)))
for p in have:
    print("   %-24s %s" % (p["n"], p["pos"]))
missing = [g for g in GIVE
           if norm(g) not in [(p.get("k") or norm(p["n"]))
                              for p in me["players"]]]
if missing:
    print("   NOT ON YOUR ROSTER: %s" % ", ".join(missing))

print("\nwho owns the players you would get:")
for g in GET:
    k = norm(g)
    who = "free agent"
    for t in SL["teams"]:
        for p in t["players"]:
            if (p.get("k") or norm(p["n"])) == k:
                who = t["owner"]
    print("   %-24s %s" % (g, who))

got = []
for g in GET:
    b = BM.get(norm(g))
    if b:
        got.append({"pid": "NEW_" + norm(g), "n": b["n"],
                    "pos": b["pos"], "tm": b["tm"]})

print("\n=== lineup BEFORE ===")
before = best(me["players"], show=True)
print("    %-31s %6.2f" % ("TOTAL", before))

keep = [p for p in me["players"] if p not in have]
print("\n=== lineup AFTER ===")
after = best(keep + got, show=True)
print("    %-31s %6.2f" % ("TOTAL", after))

print("\n  weekly change  %+.2f" % (after - before))
print("  roster size    %d -> %d"
      % (len(me["players"]), len(keep) + len(got)))

# depth check: what happens if a starter goes down
print("\n=== depth stress test ===")
for lbl, roster in (("before", me["players"]),
                    ("after", keep + got)):
    wrs = sorted([p for p in roster if p.get("pos") == "WR"],
                 key=lambda x: -proj(x))
    print("  %-6s WRs: %s"
          % (lbl, ", ".join("%s %.1f" % (p["n"].split()[-1],
                                         proj(p))
                            for p in wrs[:6])))
