import ssl, certifi, re, json
import urllib.request as U
import urllib.parse as UP
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime as pdt
from datetime import datetime, timezone

CTX = ssl.create_default_context(cafile=certifi.where())
HDR = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel "
       "Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, "
       "like Gecko) Chrome/126.0 Safari/537.36"}
NOW = datetime.now(timezone.utc)

SITES = [
 "https://www.nfl.com/news/",
 "https://www.si.com/nfl",
 "https://bleacherreport.com/nfl",
 "https://www.foxsports.com/nfl",
 "https://www.nbcsports.com/nfl",
 "https://www.fantasypros.com/nfl/news.php",
 "https://www.usatoday.com/sports/nfl/",
 "https://theathletic.com/nfl/",
 "https://www.sbnation.com/nfl",
 "https://www.espn.com/nfl/",
]

CUR = [
 "https://www.espn.com/espn/rss/nfl/news",
 "https://profootballtalk.nbcsports.com/feed/",
 "https://sports.yahoo.com/nfl/rss.xml",
 "https://www.cbssports.com/rss/headlines/nfl/",
 "https://www.rotowire.com/rss/news.php?sport=NFL",
 "https://www.profootballrumors.com/feed",
 "https://www.sportingnews.com/us/rss/nfl",
 "https://www.rotoballer.com/feed",
]

LK = re.compile(
 r'<link[^>]+type=["\']application/(?:rss|atom)'
 r'\+xml["\'][^>]*>', re.I)
HR = re.compile(r'href=["\']([^"\']+)["\']', re.I)

def get(u, t=20):
    r = U.Request(u, headers=HDR)
    return U.urlopen(r, timeout=t, context=CTX).read()

def pdate(s):
    if not s:
        return None
    try:
        return pdt(s.strip())
    except Exception:
        pass
    for f in ("%Y-%m-%dT%H:%M:%S%z",
              "%Y-%m-%dT%H:%M:%SZ",
              "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(s.strip(), f)
        except Exception:
            continue
    return None

def age(d):
    if d is None:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return (NOW - d).total_seconds() / 60.0

def probe(u):
    try:
        raw = get(u)
    except Exception as e:
        return (0, None, str(e)[:30])
    try:
        rt = ET.fromstring(raw)
    except Exception as e:
        return (0, None, "xml " + str(e)[:26])
    it = rt.findall(".//item")
    ds = [pdate(x.findtext("pubDate") or "") for x in it]
    if not it:
        ns = "{http://www.w3.org/2005/Atom}"
        it = rt.findall(".//%sentry" % ns)
        ds = [pdate(x.findtext(ns + "updated") or "")
              for x in it]
    ag = [age(d) for d in ds if d is not None]
    return (len(it), min(ag) if ag else None, "")

print("=== BASELINE: your current feeds ===")
print("%-46s %5s %9s" % ("URL", "N", "NEWEST"))
for u in CUR:
    n, a, e = probe(u)
    f = ("%5.0f min" % a) if a is not None else "   --"
    print("%-46s %5d %9s %s" % (u[:46], n, f, e))

found = {}
print("\n=== DISCOVERY ===")
for s in SITES:
    try:
        h = get(s, 25).decode("utf8", "ignore")
    except Exception as e:
        print("%-34s page fail %s" % (
            UP.urlparse(s).netloc, str(e)[:24]))
        continue
    hits = []
    for tag in LK.findall(h):
        m = HR.search(tag)
        if m:
            hits.append(UP.urljoin(s, m.group(1)))
    for tag in LK.finditer(h):
        pass
    hits = list(dict.fromkeys(hits))[:4]
    if not hits:
        print("%-34s no <link> feeds" % (
            UP.urlparse(s).netloc,))
    for u in hits:
        found[u] = UP.urlparse(s).netloc

print("\n=== PROBING %d DISCOVERED ===" % len(found))
print("%-46s %5s %9s" % ("URL", "N", "NEWEST"))
good = []
for u, site in found.items():
    n, a, e = probe(u)
    f = ("%5.0f min" % a) if a is not None else "   --"
    print("%-46s %5d %9s %s" % (u[:46], n, f, e))
    if n > 3:
        good.append((site, u, n, a))

print("\n=== USABLE ===")
for g in sorted(good, key=lambda x: x[3]
                if x[3] is not None else 1e9):
    print("  %-20s %s" % (g[0], g[1]))
