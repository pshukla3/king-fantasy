import sys

# Markers that must exist in the shipped page.
# Add a line here whenever a feature ships.
NEED = [
    ('</script></body></html>', 1),
    ('data-t="lgsync"', 1),
    ('id="lgsync"', 1),
    ('id="kfgo"', 1),
    ('_connect.js', 1),
    ('nav2js', 1),
    ('data-src=\"power.html', 1),
    ('data-src=\"matchup.html', 1),
    ('data-src=\"myteam.html', 1),
    ('data-src=\"waivers.html', 1),
    ('data-src=\"games.html', 1),
    ('data-src=\"standings.html', 1),
    ('_card2.js', 1),
    ('_scores.js', 1),
    ('_score.js', 1),
    ('_sb.js', 1),
    ('data-src=\"tradecalc.html', 2),
    ('data-src=\"startsit.html', 1),
    ('id="tcwrap"', 0),
    ('safe(drawTrades', 0),
    ('id="scores"', 1),
]

H = open("vaporai.html").read()
bad = []
for m, n in NEED:
    c = H.count(m)
    ok = "ok " if c == n else "FAIL"
    print("  %s %-28s %d (want %d)" % (ok, m[:28], c, n))
    if c != n:
        bad.append(m)

import re
nav = len(re.findall(r'<button[^>]*data-t=', H))
NAVN = 26
print("  %s nav buttons                  %d (want %d)"
      % ("ok " if nav == NAVN else "FAIL", nav,
         NAVN))
if nav != NAVN:
    bad.append("nav count")

if bad:
    print("BUILD VERIFY FAILED: " + ", ".join(bad))
    sys.exit(1)
print("build verify passed")
