import json, re

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

B = json.load(open("site/_board.json"))
Q = json.load(open("site/_qbproj.json"))
QB = {norm(v["n"]): v for v in Q.values()}

st = sorted([v["ppg"] for v in Q.values() if v.get("qb1")],
            reverse=True)
REP = st[10] if len(st) > 10 else (st[-1] if st else 12.0)
print("replacement QB (QB11) = %.2f ppg" % REP)

hit = 0
for r in B["rows"]:
    if r.get("pos") != "QB":
        continue
    v = QB.get(norm(r.get("n")))
    if not v:
        r["live"] = round((r.get("live") or 0) * 0.10, 2)
        r["vorp"] = 0.0
        continue
    wk = [x for x in v["wk"] if x["o"] != "BYE"]
    r["live"] = v["ppg"]
    r["base"] = v["ppg"]
    r["qb1"] = v.get("qb1", 0)
    if wk:
        r["floor"] = round(sum(x["lo"] for x in wk) / len(wk), 1)
        r["ceil"] = round(sum(x["hi"] for x in wk) / len(wk), 1)
    r["vorp"] = round(max(0.0, v["ppg"] - REP), 2)
    r["uvorp"] = r["vorp"]
    r["wk"] = v["wk"]
    r["sim"] = 20000
    hit += 1
json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
print("merged sim projections into %d QB rows" % hit)

a = QB.get("josh allen")
if a:
    print("\n=== Josh Allen week by week ===")
    for x in a["wk"][:8]:
        if x["o"] == "BYE":
            print("  wk %-3d BYE" % x["w"])
            continue
        print("  wk %-3d %-4s %s  proj %5.1f  (%4.1f - %4.1f)"
              % (x["w"], x["o"], "H" if x.get("h") else "A",
                 x["m"], x["lo"], x["hi"]))
    sp = [x["m"] for x in a["wk"] if x["o"] != "BYE"]
    print("  opponent spread: %.1f to %.1f" % (min(sp), max(sp)))
