import json, re

from namekey import nk as norm

B = json.load(open("site/_board.json"))
SRC = {}
for f, tag in (("site/_qbproj.json", "QB"),
               ("site/_wrproj.json", "WR"),
               ("site/_rbproj.json", "RB")):
    try:
        j = json.load(open(f))
        print("%-22s %d players" % (f, len(j)))
        for k, v in j.items():
            # RB file wins for RBs (it has rushing too)
            if tag == "RB" or k not in SRC:
                SRC[k] = v
    except Exception as e:
        print(f, "->", e)

# suffix aliases
for k in list(SRC):
    for sf in (" sr", " jr", " ii", " iii", " iv", " v"):
        if k.endswith(sf):
            SRC.setdefault(k[:-len(sf)], SRC[k])

hit = miss = 0
for r in B["rows"]:
    if r.get("pos") not in ("QB", "RB", "WR", "TE"):
        continue
    v = SRC.get(norm(r.get("n")))
    if not v:
        miss += 1
        continue
    wk = [x for x in v["wk"]
          if x["o"] != "BYE" and not x.get("out")]
    r["live"] = v["ppg"]
    r["base"] = v["ppg"]
    r["wk"] = v["wk"]
    r["sim"] = 20000
    if wk:
        r["floor"] = round(sum(x["lo"] for x in wk) / len(wk), 1)
        r["ceil"] = round(sum(x["hi"] for x in wk) / len(wk), 1)
    hit += 1
json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
print("\nmerged %d rows, %d had no simulation" % (hit, miss))
