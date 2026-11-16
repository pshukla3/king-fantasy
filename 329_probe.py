import ssl, certifi, json, re
import urllib.request as U
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime as pdt
from datetime import datetime, timezone

CTX = ssl.create_default_context(cafile=certifi.where())
HDR = {"User-Agent": "curl/8.7.1"}
NOW = datetime.now(timezone.utc)

CAND = [
 ("ESPN-API", "js",
  "https://site.api.espn.com/apis/site/v2/sports/"
  "football/nfl/news?limit=50"),
 ("NFL.com", "rss",
  "https://www.nfl.com/feeds/rss/news"),
 ("FantasyPros", "rss",
  "https://www.fantasypros.com/rss/nfl-news.xml"),
 ("TheScore", "rss",
  "https://www.thescore.com/nfl/news.rss"),
 ("SI-NFL", "rss",
  "https://www.si.com/rss/si_nfl.rss"),
 ("USAToday", "rss",
  "https://ftw.usatoday.com/feed"),
 ("Rotoballer", "rss",
  "https://www.rotoballer.com/feed"),
 ("BleacherRpt", "rss",
  "https://bleacherreport.com/articles/feed?tag_id=16"),
 ("NBCSports", "rss",
  "https://sports.nbcsports.com/feed/"),
 ("FoxSports", "rss",
  "https://www.foxsports.com/rss/nfl"),
 ("TheAthletic", "rss",
  "https://theathletic.com/nfl/?rss=1"),
 ("AP-NFL", "rss",
  "https://rsshub.app/apnews/topics/nfl"),
]

def age(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (NOW - dt).total_seconds() / 60.0

def pdate(s):
    if not s:
        return None
    s = s.strip()
    try:
        return pdt(s)
    except Exception:
        pass
    for f in ("%Y-%m-%dT%H:%M:%S%z",
              "%Y-%m-%dT%H:%M:%SZ",
              "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(s, f)
        except Exception:
            continue
    return None

def get(u):
    r = U.Request(u, headers=HDR)
    return U.urlopen(r, timeout=20, context=CTX).read()

def probe(name, kind, url):
    try:
        raw = get(url)
    except Exception as e:
        return (name, "FETCH FAIL", str(e)[:44], 0, None)
    if kind == "js":
        try:
            d = json.loads(raw)
            it = d.get("articles") or []
            ds = [pdate(x.get("published")) for x in it]
        except Exception as e:
            return (name, "JSON FAIL", str(e)[:44], 0, None)
    else:
        try:
            rt = ET.fromstring(raw)
        except Exception as e:
            return (name, "XML FAIL", str(e)[:44], 0, None)
        it = rt.findall(".//item")
        ds = [pdate((x.findtext("pubDate") or "")) for x in it]
        if not it:
            ns = "{http://www.w3.org/2005/Atom}"
            it = rt.findall(".//%sentry" % ns)
            ds = [pdate((x.findtext(ns + "updated") or ""))
                  for x in it]
    ag = [age(d) for d in ds if d is not None]
    if not it:
        return (name, "EMPTY", "0 items", 0, None)
    if not ag:
        return (name, "NO DATES", "%d items" % len(it),
                len(it), None)
    return (name, "OK", "", len(it), min(ag))

print("%-13s %-10s %5s %10s" % ("FEED", "STATUS",
                                "ITEMS", "NEWEST"))
print("-" * 44)
rows = []
for c in CAND:
    r = probe(*c)
    rows.append(r)
    f = ("%6.0f min" % r[4]) if r[4] is not None else "  --"
    print("%-13s %-10s %5d %10s  %s"
          % (r[0], r[1], r[3], f, r[2]))

ok = [r for r in rows if r[1] == "OK" and r[4] is not None]
ok.sort(key=lambda r: r[4])
print("\nFRESHEST (add these):")
for r in ok[:6]:
    print("  %-13s %.0f min old" % (r[0], r[4]))
