import ssl, certifi, json
import urllib.request as U
import xml.etree.ElementTree as ET

CTX = ssl.create_default_context(cafile=certifi.where())
UAS = {
 "curl": "curl/8.7.1",
 "browser": ("Mozilla/5.0 (Macintosh; Intel Mac OS X "
             "10_15_7) AppleWebKit/537.36 Chrome/126.0"),
 "none": None,
}
E = "https://www.espn.com/espn/rss/nfl/news"

print("=== ESPN RSS by User-Agent ===")
for k, ua in UAS.items():
    h = {"User-Agent": ua} if ua else {}
    try:
        r = U.Request(E, headers=h)
        b = U.urlopen(r, timeout=20, context=CTX).read()
    except Exception as e:
        print("%-8s FETCH FAIL %s" % (k, str(e)[:40]))
        continue
    try:
        n = len(ET.fromstring(b).findall(".//item"))
        print("%-8s %5d bytes  %3d items" % (k, len(b), n))
    except Exception as e:
        print("%-8s %5d bytes  XML FAIL %s"
              % (k, len(b), str(e)[:30]))
        print("     head: %r" % b[:90])

print("\n=== ESPN JSON API sample ===")
A = ("https://site.api.espn.com/apis/site/v2/sports/"
     "football/nfl/news?limit=50")
r = U.Request(A, headers={"User-Agent": "curl/8.7.1"})
d = json.loads(U.urlopen(r, timeout=20, context=CTX).read())
ar = d.get("articles") or []
print("articles: %d" % len(ar))
for a in ar[:3]:
    ln = ((a.get("links") or {}).get("web") or {}).get("href")
    print("  pub : %s" % a.get("published"))
    print("  hd  : %s" % (a.get("headline") or "")[:56])
    print("  desc: %s" % (a.get("description") or "")[:56])
    print("  url : %s" % str(ln)[:56])
    print("  by  : %s" % [x.get("firstName", "") + " " +
          x.get("lastName", "")
          for x in (a.get("byline") and [] or
                    a.get("categories") or [])][:0])
    print("  ---")

print("\n=== BleacherReport NFL share ===")
B = "https://feeds.bleacherreport.com/articles"
r = U.Request(B, headers={"User-Agent": "curl/8.7.1"})
rt = ET.fromstring(U.urlopen(r, timeout=25,
                             context=CTX).read())
it = rt.findall(".//item")
nfl = 0
for x in it:
    t = " ".join(filter(None, [
        x.findtext("title") or "",
        x.findtext("link") or "",
        " ".join(c.text or "" for c in
                 x.findall("category"))])).lower()
    if "nfl" in t or "football" in t:
        nfl += 1
print("total %d | nfl-tagged %d" % (len(it), nfl))
for x in it[:3]:
    print("  cats: %s" % [c.text for c in
                          x.findall("category")][:4])
