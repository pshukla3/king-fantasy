import re
from collections import Counter

H = open("vaporai.html").read()
n0 = len(H)

pat = re.compile(
    r'<script[^>]*src="([^"]+)"[^>]*>(.*?)</script>', re.S)
spans = [(m.start(), m.end(), m.group(1), m.group(2).strip())
         for m in pat.finditer(H)]

before = Counter(s[2] for s in spans)
print("before: %d tags, %d unique"
      % (len(spans), len(before)))

# Walk backwards, keep the LAST copy of each src.
# Tags carrying inline code are never touched.
seen, drop, inline = set(), [], 0
for st, en, src, body in reversed(spans):
    if body:
        inline += 1
        continue
    if src in seen:
        drop.append((st, en))
    else:
        seen.add(src)

for st, en in sorted(drop, reverse=True):
    H = H[:st] + H[en:]

after = Counter(
    m.group(1) for m in pat.finditer(H))
print("removed %d duplicate tags (%d inline left alone)"
      % (len(drop), inline))
print("after:  %d tags, %d unique"
      % (sum(after.values()), len(after)))
for k, v in after.most_common():
    if v > 1:
        print("  STILL DUPLICATED: %s x%d" % (k, v))

assert H.count("</script></body></html>") == 1, "tail anchor"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav " + str(nav)
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
