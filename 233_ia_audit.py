import re
import json
import os

print("=== NAV TABS IN 112_ui_v4.py ===")
s = open("112_ui_v4.py").read()
for m in re.finditer(
        r'data-t="([a-z]+)"[^>]*>([^<]+)<', s):
    print("  %-10s %s" % (m.group(1), m.group(2)))

print("\n=== WHAT EACH SECTION HOLDS ===")
for m in re.finditer(
        r'<section[^>]*id="([a-z]+)"[^>]*>(.{0,110})',
        s, re.S):
    body = m.group(2).replace("\n", " ").strip()
    kind = "iframe" if "iframe" in body else "js-render"
    src = re.search(r'src="([^"]+)"', body)
    print("  %-10s %-9s %s"
          % (m.group(1), kind,
             src.group(1) if src else ""))

print("\n=== PAGE SIZES ===")
for f in ["site/index.html", "site/league.html",
          "site/teams.html", "site/rankings.html",
          "site/trade.html", "site/player.html"]:
    if os.path.exists(f):
        print("  %-22s %6d KB"
              % (f, os.path.getsize(f) // 1024))

print("\n=== league.html FUNCTIONS (150) ===")
t = open("150_league_page.py").read()
for m in re.finditer(r"function (\w+)\(", t):
    print("  %s" % m.group(1))
print("  uses Chart.js: %s" % ("Chart.js" in t))

print("\n=== teams.html FUNCTIONS (200) ===")
u = open("site/_teams.js").read()
for m in re.finditer(r"function (\w+)\(", u):
    print("  %s" % m.group(1))
print("  live Sleeper fetch: %s"
      % ("api.sleeper.app" in u))
