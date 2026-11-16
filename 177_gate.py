import re
import subprocess
import sys

FILES = ["site/index.html", "site/league.html",
         "site/trade.html", "site/player.html"]
ok = True
for f in FILES:
    try:
        s = open(f, errors="ignore").read()
    except IOError:
        print("  %-20s MISSING" % f)
        continue
    n = 0
    for i, m in enumerate(re.finditer(
            r"<script>(.*?)</script>", s, re.S)):
        n += 1
        open("/tmp/gate.js", "w").write(m.group(1))
        r = subprocess.run(
            ["node", "--check", "/tmp/gate.js"],
            capture_output=True, text=True)
        if r.returncode != 0:
            ok = False
            print("  SYNTAX ERROR in %s block %d" % (f, i))
            print(r.stderr[:500])
    print("  %-20s %d script block(s) ok" % (f, n))
if not ok:
    print("\nGATE FAILED - deploy aborted")
    sys.exit(1)
print("\nGATE PASS")
