import json
import re
import ssl
import time
import certifi
import urllib.request as UR
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import pandas as pd

FEEDS = [
    ("ESPN", "https://www.espn.com/espn/rss/nfl/news"),
    ("PFT", "https://profootballtalk.nbcsports.com/feed/"),
    ("Yahoo", "https://sports.yahoo.com/nfl/rss.xml"),
    ("CBS",
     "https://www.cbssports.com/rss/headlines/nfl/"),
    ("Rotowire",
     "https://www.rotowire.com/rss/news.php?sport=NFL"),
    ("PFRumors", "https://www.profootballrumors.com/feed"),
    ("SportingN",
     "https://www.sportingnews.com/us/rss/nfl"),
    ("Athletic",
     "https://www.nytimes.com/athletic/rss/nfl/"),
    ("Rotoballer", "https://www.rotoballer.com/feed"),
]
HDR = {"User-Agent": "curl/8.7.1"}
CTX = ssl.create_default_context(cafile=certifi.where())

def get(u):
    r = UR.Request(u, headers=HDR)
    with UR.urlopen(r, timeout=20, context=CTX) as f:
        return f.read()

def sub(e, *tags):
    for t in tags:
        for c in e.iter():
            if c.tag.split("}")[-1] == t and c.text:
                return c.text.strip()
    return ""

def link(e):
    for c in e.iter():
        if c.tag.split("}")[-1] == "link":
            if c.text and c.text.strip():
                return c.text.strip()
            h = c.attrib.get("href")
            if h:
                return h
    return ""

IMRX = re.compile(r"\.(jpg|jpeg|png|webp)", re.I)

def imgof(e, raw):
    for c in e.iter():
        n = c.tag.split("}")[-1]
        if n in ("content", "thumbnail", "enclosure",
                 "image"):
            u = c.attrib.get("url") or c.attrib.get("href")
            if u and IMRX.search(u):
                return u
    m = re.search(r'<img[^>]+src="([^"]+)"', raw or "")
    if m and IMRX.search(m.group(1)):
        return m.group(1)
    return ""

ITEMS = []
for name, url in FEEDS:
    try:
        root = ET.fromstring(get(url))
    except Exception as e:
        print("  %-10s FAIL %s" % (name, str(e)[:38]))
        continue
    n = 0
    for e in root.iter():
        if e.tag.split("}")[-1] not in ("item", "entry"):
            continue
        t = sub(e, "title")
        if not t:
            continue
        raw = sub(e, "description", "summary", "content")
        ITEMS.append({
            "t": re.sub(r"\s+", " ", t), "u": link(e),
            "s": name,
            "d": sub(e, "pubDate", "published", "updated"),
            "b": re.sub("<[^>]+>", " ", raw)[:400],
            "i": imgof(e, raw)})
        n += 1
    print("  %-10s ok  %d" % (name, n))
    time.sleep(0.2)
EJ = ("https://site.api.espn.com/apis/site/v2/"
      "sports/football/nfl/news?limit=50")
try:
    _d = json.loads(get(EJ))
    _n = 0
    for a in (_d.get("articles") or []):
        _t = (a.get("headline") or "").strip()
        if not _t:
            continue
        _u = ((a.get("links") or {}).get("web")
              or {}).get("href") or ""
        _im = ""
        for _x in (a.get("images") or []):
            _q = _x.get("url") or ""
            if IMRX.search(_q):
                _im = _q
                break
        ITEMS.append({
            "t": re.sub(r"\s+", " ", _t), "u": _u,
            "s": "ESPNwire",
            "d": a.get("published") or "",
            "b": re.sub("<[^>]+>", " ",
                        a.get("description") or "")[:400],
            "i": _im})
        _n += 1
    print("  %-10s ok  %d" % ("ESPNwire", _n))
except Exception as _e:
    print("  %-10s FAIL %s" % ("ESPNwire", str(_e)[:38]))

BRU = "https://feeds.bleacherreport.com/articles"
try:
    _r = ET.fromstring(get(BRU))
    _n = 0
    for e in _r.iter():
        if e.tag.split("}")[-1] not in ("item", "entry"):
            continue
        _c = [(_y.text or "").strip().lower() for _y in e
              if _y.tag.split("}")[-1] == "category"]
        if "nfl" not in _c:
            continue
        t = sub(e, "title")
        if not t:
            continue
        raw = sub(e, "description", "summary", "content")
        ITEMS.append({
            "t": re.sub(r"\s+", " ", t), "u": link(e),
            "s": "BleacherR",
            "d": sub(e, "pubDate", "published", "updated"),
            "b": re.sub("<[^>]+>", " ", raw)[:400],
            "i": imgof(e, raw)})
        _n += 1
    print("  %-10s ok  %d" % ("BleacherR", _n))
except Exception as _e:
    print("  %-10s FAIL %s" % ("BleacherR", str(_e)[:38]))

print("raw %d from %d feeds | with images %d"
      % (len(ITEMS), len({i["s"] for i in ITEMS}),
         len([i for i in ITEMS if i["i"]])))

B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()]
RK = "rank" if "rank" in B.columns else "model_rank"
NAMES = {}
for _, r in B.iterrows():
    nm = str(r["player_display_name"]).strip()
    if " " in nm and len(nm) > 5:
        try:
            k = int(r[RK])
        except Exception:
            k = 999
        NAMES[nm.lower()] = (nm, k)
print("board names %d" % len(NAMES))

FAN = {"injur": 3, "injured reserve": 4, "out for": 4,
       "torn": 4, "acl": 4, "achilles": 4, "hamstring": 2,
       "trade": 4, "traded": 4, "released": 3,
       "waived": 2, "sign": 2, "suspend": 3,
       "activat": 2, "questionable": 2, "doubtful": 2,
       "ruled out": 3, "starter": 2, "benched": 3,
       "return": 2, "claim": 2, "promot": 2}
BIG = {"fired": 3, "hired": 2, "head coach": 2,
       "arrested": 3, "retire": 3, "unretire": 3,
       "ruling": 2, "appeal": 2, "extension": 2,
       "franchise tag": 3, "53-man": 2, "cut": 2,
       "practice squad": 1}
SKIP = ("podcast", "watch:", "highlights", "power rank",
        "mock draft", "best bets", "odds:", "picks:")

def findpl(t, b):
    tl, bl = t.lower(), b.lower()
    bn, br = None, 999
    for lo, (nm, rk) in NAMES.items():
        if lo in tl and rk < br:
            bn, br = nm, rk
    if bn:
        return bn, br, True
    for lo, (nm, rk) in NAMES.items():
        if lo in bl and rk < br:
            bn, br = nm, rk
    return bn, br, False

STOP = set(("the a an and or of to in on for with at is "
            "was be as by from his her their it that "
            "nfl news report says after who what more "
            "will has have this new").split())

def toks(t):
    return {w for w in re.findall(r"[a-z]{4,}", t.lower())
            if w not in STOP}

SC = []
for it in ITEMS:
    tl = it["t"].lower()
    if any(x in tl for x in SKIP):
        continue
    s = tl + " " + it["b"].lower()
    pl, pr, intitle = findpl(it["t"], it["b"])
    k = max([v for w, v in FAN.items() if w in s] or [0])
    bg = max([v for w, v in BIG.items() if w in s] or [0])
    if pl is None and bg == 0:
        continue
    base = k * 2 + bg * 2
    if pl:
        pb = 6 if pr <= 50 else (4 if pr <= 120 else 2)
        base += pb if intitle else pb * 0.4
    if not intitle and bg == 0:
        pl = None
    SC.append({**it, "pl": pl, "sc": base,
               "tk": toks(it["t"])})

CL = []
for it in SC:
    hit = None
    for c in CL:
        if it["pl"] and c["pl"] and it["pl"] == c["pl"]:
            hit = c
            break
        u = it["tk"] & c["tk"]
        v = it["tk"] | c["tk"]
        if v and len(u) / len(v) >= 0.40:
            hit = c
            break
    if hit is None:
        CL.append({"pl": it["pl"], "tk": set(it["tk"]),
                   "srcs": {it["s"]: it["u"]}, "best": it})
    else:
        hit["srcs"][it["s"]] = it["u"]
        hit["tk"] |= it["tk"]
        if it["sc"] > hit["best"]["sc"]:
            hit["best"] = it
        if hit["pl"] is None:
            hit["pl"] = it["pl"]
        if not hit["best"].get("i") and it.get("i"):
            hit["best"]["i"] = it["i"]

OUT = []
for c in CL:
    it = c["best"]
    n = len(c["srcs"])
    OUT.append({"t": it["t"], "u": it["u"], "s": it["s"],
                "d": it["d"], "b": it["b"][:200],
                "i": it.get("i", ""), "p": c["pl"], "n": n,
                "sc": round(it["sc"] + 4.0 * (n - 1), 1),
                "srcs": sorted(c["srcs"])})
OUT.sort(key=lambda x: -x["sc"])
OUT = OUT[:40]
NOW = datetime.now(timezone.utc)
json.dump({"gen": NOW.isoformat(), "items": OUT},
          open("site/_news.json", "w"))

ART = []
for o in OUT[:14]:
    src = ", ".join(o["srcs"])
    if o["n"] > 1:
        src += " (%d outlets)" % o["n"]
    ART.append({"hd": o["t"], "url": o["u"],
                "img": o["i"], "ins": o["n"] > 1,
                "ts": NOW.strftime("%Y-%m-%d"),
                "dk": (o["p"] + " \u2014 " if o["p"]
                       else "") + src})
json.dump({"articles": ART, "gen": NOW.isoformat()},
          open("news_2026.json", "w"))

print("\nscored %d -> clusters %d -> kept %d"
      % (len(SC), len(CL), len(OUT)))
print("corroborated 2+: %d | with images: %d"
      % (len([o for o in OUT if o["n"] > 1]),
         len([o for o in OUT if o["i"]])))
print("wrote site/_news.json + news_2026.json (%d arts)"
      % len(ART))
print("\n=== TOP 12 ===")
for o in OUT[:12]:
    print("  %5.1f [%d]%s %-16s %s"
          % (o["sc"], o["n"], "*" if o["i"] else " ",
             (o["p"] or "league")[:16], o["t"][:46]))
