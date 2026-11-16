import glob, re, json, os
from collections import defaultdict

RX = re.compile(r'open\(\s*["\'](site/[^"\']+)["\']\s*,'
                r'\s*["\']w')
BASE = "guard_baseline.json"

own = defaultdict(set)
for f in sorted(glob.glob("*.py")):
    try:
        s = open(f).read()
    except IOError:
        continue
    for m in RX.finditer(s):
        own[m.group(1)].add(f)

cur = {k: sorted(v) for k, v in own.items() if len(v) > 1}

if not os.path.exists(BASE):
    json.dump(cur, open(BASE, "w"), indent=1)
    print("guard: baseline created with %d known "
          "multi-writer files" % len(cur))
    raise SystemExit(0)

known = json.load(open(BASE))
new = {}
for k, v in cur.items():
    if k not in known:
        new[k] = v
    else:
        extra = sorted(set(v) - set(known[k]))
        if extra:
            new[k] = extra

print("site/ outputs: %d | known multi-writer: %d"
      % (len(own), len(known)))
if new:
    print("\n!! NEW COLLISION - a script now writes a file "
          "another script already owns:")
    for k, v in sorted(new.items()):
        print("   %-26s added by %s" % (k, v))
    print("\nIf intentional, delete %s to re-baseline."
          % BASE)
    raise SystemExit(1)
print("guard: no new collisions")
