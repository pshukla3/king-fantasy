import json, re, sys

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

B = json.load(open("site/_board.json"))
IDX = {}
for r in B["rows"]:
    IDX[norm(r["n"])] = r
    for sf in (" sr", " jr", " ii", " iii"):
        if norm(r["n"]).endswith(sf):
            IDX.setdefault(norm(r["n"])[:-len(sf)], r)

def look(nm):
    r = IDX.get(norm(nm))
    if r:
        return r
    for k, v in IDX.items():
        if norm(nm) in k or k in norm(nm):
            return v
    return None

def side(names, label):
    tot = 0.0
    print("  %s:" % label)
    for nm in names:
        r = look(nm)
        if not r:
            print("    %-24s NOT FOUND" % nm)
            continue
        v = r.get("val") or 0
        tot += v
        flag = ""
        if r.get("out_season"):
            flag = "  <-- OUT FOR SEASON"
        elif r.get("miss"):
            flag = "  (misses %d)" % r["miss"]
        print("    %-24s %-3s %-4s ppg %5.1f  val %6.0f%s"
              % (r["n"][:24], r.get("pos"), r.get("tm"),
                 r.get("live") or 0, v, flag))
    print("    %-24s %28.0f" % ("TOTAL", tot))
    return tot

def judge(get, give, title):
    print("\n" + "=" * 62)
    print(title)
    print("=" * 62)
    a = side(get, "YOU GET")
    print()
    b = side(give, "YOU GIVE")
    net = a - b
    pct = (net / b * 100) if b else 0
    if pct > 12:
        vd = "ACCEPT - clear win"
    elif pct > 4:
        vd = "ACCEPT - modest win"
    elif pct > -4:
        vd = "EVEN - preference call"
    elif pct > -12:
        vd = "DECLINE - modest loss"
    else:
        vd = "DECLINE - clear loss"
    print("\n  net %+.0f  (%+.1f%%)   ->  %s" % (net, pct, vd))

judge(["Zay Flowers"],
      ["Bhayshul Tuten", "Josh Downs"],
      "OFFER 1")

judge(["Josh Allen", "James Cook", "Tucker Kraft",
       "Rams Defense"],
      ["Omarion Hampton", "George Pickens",
       "Dalton Kincaid", "Bryce Young",
       "Seahawks Defense"],
      "OFFER 2")
