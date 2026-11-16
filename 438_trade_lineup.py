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

def proj(p):
    b = (BD.get(p.get("tm")) if p.get("pos") in ("DEF", "DST")
         else BM.get(p.get("k") or norm(p.get("n"))))
    if b and b.get("live") is not None:
        return float(b["live"])
    return float(p.get("ppg") or 0)

def best(players):
    pool = sorted(players, key=lambda x: -proj(x))
    used, tot, flex = set(), 0.0, []
    for i, s in enumerate(SLOTS):
        if "FLEX" in s:
            flex.append(s); continue
        for p in pool:
            if p["pid"] in used: continue
            if p.get("pos") in EL.get(s, []):
                used.add(p["pid"]); tot += proj(p); break
    for s in flex:
        for p in pool:
            if p["pid"] in used: continue
            if p.get("pos") in EL.get(s, []):
                used.add(p["pid"]); tot += proj(p); break
    return tot

def team(owner):
    for t in SL["teams"]:
        if owner.lower() in str(t.get("owner", "")).lower():
            return t
    return None

def pull(t, names):
    keys = [norm(n) for n in names]
    out = []
    for p in t["players"]:
        if (p.get("k") or norm(p["n"])) in keys:
            out.append(p)
    return out

A_OWNER, B_OWNER = "brownies", "Bryson"
A_GIVE = ["Amon-Ra St. Brown", "Kyren Williams"]
B_GIVE = ["Malik Nabers", "DJ Moore", "Cam Skattebo"]

ta, tb = team(A_OWNER), team(B_OWNER)
ga, gb = pull(ta, A_GIVE), pull(tb, B_GIVE)
print("matched %d of %d from %s, %d of %d from %s"
      % (len(ga), len(A_GIVE), ta["owner"],
         len(gb), len(B_GIVE), tb["owner"]))

for t, give, get, lbl in ((ta, ga, gb, ta["owner"]),
                          (tb, gb, ga, tb["owner"])):
    before = best(t["players"])
    keep = [p for p in t["players"] if p not in give]
    after = best(keep + get)
    print("\n=== %s ===" % lbl)
    print("  gives : %s"
          % ", ".join(p["n"] for p in give))
    print("  gets  : %s"
          % ", ".join(p["n"] for p in get))
    print("  optimal lineup before : %6.2f" % before)
    print("  optimal lineup after  : %6.2f" % after)
    print("  weekly change         : %+6.2f" % (after - before))
    print("  roster size %d -> %d"
          % (len(t["players"]),
             len(keep) + len(get)))
