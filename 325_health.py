import json
import os
import re

H = open("site/index.html").read()
print("site/index.html %.2f MB" % (len(H) / 1e6))
ok, bad = 0, []

def chk(lbl, cond, note=""):
    global ok
    if cond:
        ok += 1
        print("  OK    %-34s %s" % (lbl, note))
    else:
        bad.append(lbl)
        print("  FAIL  %-34s %s" % (lbl, note))

print("\n=== ASSETS THE PAGE FETCHES ===")
for m in sorted(set(re.findall(r'fetch\("([\w.\-]+)"', H))):
    p = "site/" + m
    e = os.path.exists(p)
    chk(m, e, "%d KB" % (os.path.getsize(p) / 1024) if e
        else "MISSING")

print("\n=== SCRIPTS THE PAGE LOADS ===")
for m in sorted(set(re.findall(r'src="(_[\w.]+\.js)"', H))):
    p = "site/" + m
    chk(m, os.path.exists(p),
        "%d KB" % (os.path.getsize(p) / 1024)
        if os.path.exists(p) else "MISSING")

print("\n=== SECTIONS: do they have content? ===")
IFRAME = {"league", "mock", "rank", "trades"}
RUNTIME = {"rosters", "calc", "topt", "tstart", "teams",
           "board", "news"}
for sid in ["home", "league", "mock", "rank", "rosters",
            "calc", "tcalc", "tfind", "acc", "rtiers",
            "rboom", "lgodds", "lgpower", "topt", "tstart",
            "dmodel", "rsos"]:
    m = re.search(r'<section id="%s"[^>]*>(.*?)</section>'
                  % sid, H, re.S)
    if not m:
        m = re.search(r'<section class="on" id="%s"[^>]*>'
                      r'(.*?)</section>' % sid, H, re.S)
    n = len(m.group(1)) if m else 0
    ph = "Building this next" in (m.group(1) if m else "")
    if sid in IFRAME:
        chk(sid, "iframe" in (m.group(1) if m else ""),
            "iframe page")
    elif sid in RUNTIME:
        chk(sid, m is not None, "rendered by JS")
    else:
        chk(sid, n > 400 and not ph,
            "%d bytes%s" % (n, "  PLACEHOLDER" if ph else ""))

print("\n=== NAV + CORE ===")
nav = re.findall(r'<button[^>]*data-t="(\w+)"', H)
chk("nav buttons", len(nav) == 18, "%d" % len(nav))
chk("rail script", "nav2js" in H)
chk("auth", "_auth.js" in H and "supabase-js" in H)
chk("landing gate", 'id="land"' in H and "kf_skip" not in H)
chk("brand", 'id="kbrand"' in H or "_brand.js" in H)
chk("theme last", H.index('id="hawkcss"')
    > H.index('id="finalcss"'))
chk("no royal", 'id="royalcss"' not in H)
chk("no old bar", "2026 Season" not in H)
chk("King Fantasy", "King Fantasy" in H)

print("\n=== DATA SANITY ===")
import pandas as pd
B = pd.read_csv("board_final.csv")
chk("board rows", len(B) > 500, "%d" % len(B))
chk("DST = 32", int((B["position"] == "DST").sum()) == 32,
    "%d" % int((B["position"] == "DST").sum()))
z = B[(B["points"].fillna(0) <= 0.01)
      & (B["rank"].fillna(999) <= 200)]
chk("no zero-pt in top 200", len(z) == 0, "%d" % len(z))
chk("p10/p90 filled",
    int(B[["p10", "p90"]].notna().all(axis=1).sum()) > 550,
    "%d" % int(B[["p10", "p90"]].notna().all(axis=1).sum()))
n = json.load(open("site/_news.json"))
chk("news items", len(n.get("items", [])) > 10,
    "%d" % len(n.get("items", [])))
d = json.load(open("site/_dst.json"))
chk("dst weekly", len(d) == 32, "%d teams" % len(d))
w = json.load(open("site/_wk.json"))
chk("weekly ingest ready", "players" in w,
    "%d weeks so far" % len(w.get("weeks", [])))

print("\n%d checks passed, %d failed" % (ok, len(bad)))
if bad:
    print("FAILURES: %s" % ", ".join(bad))
