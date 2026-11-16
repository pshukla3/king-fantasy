import re
import shutil

shutil.copy("vaporai.html", "vaporai.html.predupe")
H = open("vaporai.html").read()
n0 = len(H)

MK = "safe(drawRosters,'rosters');"
pos = [m.end() for m in re.finditer(re.escape(MK), H)]
print("theme JS copies: %d" % len(pos))
if len(pos) > 1:
    seg = H[pos[0]:pos[1]]
    same = all(H[pos[i]:pos[i + 1]] == seg
               for i in range(len(pos) - 1))
    print("  blocks identical: %s" % same)
    H = H[:pos[0]] + H[pos[-1]:]
    print("  removed %d duplicates" % (len(pos) - 1))

bl = [(m.start(), m.end(), m.group(0))
      for m in re.finditer(r"<style[^>]*>.*?</style>",
                           H, re.S)]
print("style tags: %d" % len(bl))
seen, drop = {}, set()
for i, (a, b, t) in enumerate(bl):
    inner = t[t.index(">") + 1:]
    if inner in seen:
        drop.add(seen[inner])
    seen[inner] = i
if drop:
    out, last = [], 0
    for i, (a, b, t) in enumerate(bl):
        if i in drop:
            out.append(H[last:a])
            last = b
    out.append(H[last:])
    H = "".join(out)
    print("  removed %d duplicate styles" % len(drop))

assert len(H) > n0 * 0.4, "removed too much"
open("vaporai.html", "w").write(H)
print("%d -> %d (-%d bytes)" % (n0, len(H), n0 - len(H)))
