import os
import re
import glob

print("=== UI BUILDERS ===")
for f in sorted(glob.glob("1*.py")):
    s = open(f, errors="ignore").read()
    if "vaporai" in s or "<html" in s or "<div" in s:
        print("  %-24s %6d bytes" % (f, len(s)))

P = "112_ui_v4.py"
if os.path.exists(P):
    s = open(P, errors="ignore").read()
    print("\n=== %s : first 45 lines ===" % P)
    for i, l in enumerate(s.split("\n")[:45]):
        print("  %3d| %s" % (i + 1, l[:88]))
    print("\n=== lines mentioning tab/nav/section ===")
    for i, l in enumerate(s.split("\n")):
        if re.search(r"tab|nav|section|button",
                     l, re.I):
            print("  %3d| %s" % (i + 1, l.strip()[:88]))
else:
    print("\n%s NOT FOUND" % P)

for H in ["vaporai.html", "site/index.html"]:
    if not os.path.exists(H):
        print("\n%s missing" % H)
        continue
    s = open(H, errors="ignore").read()
    print("\n=== %s : %d KB ===" % (H, len(s) // 1024))
    ids = re.findall(r'id=["\']?([A-Za-z0-9_-]+)', s)
    print("  ids: %s" % sorted(set(ids))[:40])
    cls = re.findall(r'class=["\']([A-Za-z0-9_ -]+)', s)
    flat = sorted(set(" ".join(cls).split()))
    print("  classes: %s" % flat[:40])
    for m in re.finditer(r"(?i)(tab|nav)", s):
        a = max(0, m.start() - 90)
        print("  ...%s..." % s[a:m.start() + 130]
              .replace("\n", " ")[:210])
        break
