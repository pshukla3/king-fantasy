import json, re
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

# phrases that actually carry a timeline
DUR = [
    (r"out for the (season|year)", 18, "season-ending"),
    (r"season[- ]ending", 18, "season-ending"),
    (r"(\d+)\s*(?:to|-|â€“)\s*(\d+)\s*weeks?", None, "range"),
    (r"(?:miss|out)\s*(?:about|around|up to)?\s*"
     r"(\d+)\s*weeks?", None, "weeks"),
    (r"placed on (?:the )?injured reserve", 4, "IR"),
    (r"\bIR\b", 4, "IR"),
    (r"week[- ]to[- ]week", 2, "week-to-week"),
    (r"day[- ]to[- ]day", 1, "day-to-day"),
    (r"expected to (?:play|return)", 0, "expected back"),
    (r"(?:did not|didn't) practice", 1, "DNP"),
]

try:
    N = json.load(open("site/_news.json"))
except IOError:
    N = []
if isinstance(N, dict):
    items = N.get("items") or N.get("articles") or []
else:
    items = N
items = [x for x in items if isinstance(x, dict)]
print("news items: %d" % len(items))

B = pd.read_csv("board_final.csv")
NAMES = {}
for _, r in B.iterrows():
    nm = str(r["player_display_name"])
    if " " in nm and len(nm) > 5:
        NAMES[norm(nm)] = nm

OUT = {}
for it in items:
    txt = " ".join(str(it.get(k) or "")
                   for k in ("t", "title", "b", "desc",
                             "description", "hd", "dk"))
    low = txt.lower()
    hits = [k for k in NAMES if k in low]
    if not hits:
        continue
    wks, kind = None, None
    for pat, w, lab in DUR:
        m = re.search(pat, low)
        if not m:
            continue
        if lab == "range":
            wks = (int(m.group(1)) + int(m.group(2))) / 2.0
        elif lab == "weeks":
            wks = float(m.group(1))
        else:
            wks = float(w)
        kind = lab
        break
    if kind is None:
        continue
    for k in hits:
        cur = OUT.get(k)
        if cur is None or wks > cur["weeks"]:
            OUT[k] = {"n": NAMES[k], "weeks": wks,
                      "kind": kind,
                      "src": str(it.get("s") or ""),
                      "line": txt.strip()[:180]}

json.dump(OUT, open("site/_pnews.json", "w"))
print("players with a timeline in the news: %d" % len(OUT))
print()
for k, v in sorted(OUT.items(),
                   key=lambda x: -x[1]["weeks"])[:15]:
    print("%-24s %5.1f wk  %-14s %s"
          % (v["n"][:24], v["weeks"], v["kind"],
             v["src"]))
    print("    " + v["line"][:110])
