import re
import ssl
import time
import urllib.request
import certifi
import pandas as pd

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
      " AppleWebKit/537.36 (KHTML, like Gecko)"
      " Chrome/124.0 Safari/537.36")
CTX = ssl.create_default_context(cafile=certifi.where())

FEEDS = [
    ("NFL.com", 1,
     "https://www.nfl.com/feeds/rss/news"),
    ("ESPN NFL", 1,
     "https://www.espn.com/espn/rss/nfl/news"),
    ("Yahoo Sports NFL", 2,
     "https://sports.yahoo.com/nfl/rss.xml"),
    ("CBS Sports NFL", 2,
     "https://www.cbssports.com/rss/headlines/nfl/"),
    ("ProFootballTalk", 2,
     "https://profootballtalk.nbcsports.com/feed/"),
    ("Sporting News NFL", 2,
     "https://www.sportingnews.com/us/rss"),
    ("SI NFL", 2,
     "https://www.si.com/rss/si_nfl.rss"),
    ("The Score NFL", 2,
     "https://www.thescore.com/nfl/news.rss"),
    ("Rotowire NFL", 3,
     "https://www.rotowire.com/rss/news.php?sport=nfl"),
    ("FantasyPros NFL", 3,
     "https://www.fantasypros.com/nfl/rss/news.php"),
]

def get(u, tmo=20):
    r = urllib.request.Request(u, headers={
        "User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(
            r, timeout=tmo, context=CTX) as f:
        return f.read().decode("utf-8", "ignore")

def items(x):
    o = re.findall(r"<item[ >].*?</item>", x, re.S)
    if not o:
        o = re.findall(r"<entry[ >].*?</entry>", x, re.S)
    return o

def tag(s, t):
    m = re.search(r"<%s[^>]*>(.*?)</%s>" % (t, t),
                  s, re.S)
    if not m:
        return ""
    v = re.sub(r"<!\[CDATA\[|\]\]>", "", m.group(1))
    return re.sub(r"<[^>]+>", " ", v).strip()

print("=== FEED PROBE ===")
print("  %-20s %4s %6s  %s"
      % ("source", "tier", "items", "status"))
print("  " + "-" * 60)
OK, RAW = [], {}
for nm, ti, u in FEEDS:
    try:
        x = get(u)
        it = items(x)
        st = "ok" if it else "responded, 0 items"
        if it:
            OK.append({"source": nm, "tier": ti,
                       "url": u, "n": len(it)})
            RAW[nm] = it
    except Exception as e:
        it, st = [], type(e).__name__ + " " + str(e)[:28]
    print("  %-20s %4d %6d  %s" % (nm[:20], ti,
                                   len(it), st))
    time.sleep(0.4)
pd.DataFrame(OK).to_csv("news_feeds_ok.csv", index=False)
print("\n  working: %d of %d" % (len(OK), len(FEEDS)))

print("\n=== SAMPLE HEADLINES PER WORKING FEED ===")
for d in OK:
    nm = d["source"]
    print("\n  --- %s (tier %d, %d items) ---"
          % (nm, d["tier"], d["n"]))
    for s in RAW[nm][:3]:
        t = tag(s, "title")
        dt = (tag(s, "pubDate") or tag(s, "updated")
              or tag(s, "published"))
        print("    %-58s" % t[:58])
        print("      %s" % dt[:40])

print("\n=== DUPLICATE COVERAGE CHECK ===")
print("  same story across outlets = corroboration,")
print("  which is the credibility signal we can")
print("  actually measure\n")
import collections
w = collections.Counter()
for d in OK:
    seen = set()
    for s in RAW[d["source"]]:
        for t in re.findall(r"[A-Z][a-z]{3,}",
                            tag(s, "title")):
            seen.add(t)
    for t in seen:
        w[t] += 1
top = [(k, v) for k, v in w.most_common(40) if v >= 3]
print("  names/terms carried by 3+ outlets:")
for k, v in top[:18]:
    print("    %-22s %d outlets" % (k, v))
