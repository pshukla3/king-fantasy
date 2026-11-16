import json, re

B = json.load(open("site/_board.json"))
rows = [r for r in B["rows"] if r.get("rk")]
rows.sort(key=lambda r: r["rk"])

adps = sorted([r["adp"] for r in rows
               if isinstance(r.get("adp"), (int, float))])
def adprank(a):
    if not isinstance(a, (int, float)):
        return None
    import bisect
    return float(bisect.bisect_left(adps, a) + 1)

def num(v, d=2):
    try:
        if v is None or v != v:
            return None
        return round(float(v), d)
    except Exception:
        return None

D = []
for r in rows:
    st = ""
    if r.get("out_season"):
        st = "OUT FOR SEASON"
    elif r.get("inj_wks"):
        st = str(r.get("inj") or "") + " " + str(r["inj_wks"])
    elif r.get("inj") and r["inj"] != "Active":
        st = str(r["inj"])
    D.append({
        "rk": int(r["rk"]),
        "nm": r.get("n") or "",
        "tm": r.get("tm") or "",
        "ps": r.get("pos") or "",
        "pr": int(r.get("posrk") or 0),
        "by": int(r.get("bye") or 0),
        "pp": num(r.get("live"), 2),
        "sz": num(r.get("ros"), 1),
        "vp": num(r.get("vorp"), 2),
        "ad": num(r.get("adp"), 1),
        "sa": None, "ea": None,
        "ar": adprank(r.get("adp")),
        "st": st.strip(),
        "id": r.get("pid") or "",
    })

p = "site/rankings.html"
s = open(p).read()
m = re.search(r"var D=\[.*?\];", s, re.S)
assert m, "could not find the var D=[...] block"
new = "var D=" + json.dumps(D, separators=(",", ":")) + ";"
s = s[:m.start()] + new + s[m.end():]
open(p, "w").write(s)
print("rankings.html refreshed from the live board")
print("  players: %d" % len(D))
for x in D[:6]:
    print("  %-3d %-24s %-4s %-4s ppg %5.1f  vorp %5.2f  %s"
          % (x["rk"], x["nm"][:24], x["ps"], x["tm"],
             x["pp"] or 0, x["vp"] or 0, x["st"]))
