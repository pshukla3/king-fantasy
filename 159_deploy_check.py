import os
import re

print("=== deploy.sh ===")
s = open("deploy.sh").read()
for i, l in enumerate(s.split("\n"), 1):
    print("  %3d| %s" % (i, l))

print("\n=== FILES ===")
for f in ["vaporai.html", "site/index.html",
          "site/league.html", "site/trade.html",
          "league_data.json"]:
    if os.path.exists(f):
        print("  %-22s %7d bytes" % (f, os.path.getsize(f)))
    else:
        print("  %-22s MISSING" % f)

print("\n=== MARKERS ===")
for f in ["112_ui_v4.py", "vaporai.html",
          "site/index.html"]:
    if not os.path.exists(f):
        print("  %s missing" % f)
        continue
    t = open(f, errors="ignore").read()
    print("  %-18s league-btn %-3s league-iframe %-3s"
          " trade-iframe %s"
          % (f,
             "YES" if 'data-t="league"' in t else "NO",
             "YES" if 'src="league.html"' in t else "NO",
             "YES" if 'src="trade.html"' in t else "NO"))

print("\n=== DO 113/114 REWRITE THE NAV? ===")
for f in ["113_home.py", "114_theme.py"]:
    if not os.path.exists(f):
        continue
    t = open(f, errors="ignore").read()
    hits = [l.strip()[:70] for l in t.split("\n")
            if "<nav" in l or "data-t=" in l
            or "vaporai.html" in l]
    print("  %s:" % f)
    for h in hits[:8]:
        print("    %s" % h)
    if not hits:
        print("    (no nav writes)")
