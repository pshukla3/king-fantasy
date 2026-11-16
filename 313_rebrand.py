import glob
import re
import shutil

OLD, NEW = "Shukie Fantasy", "King Fantasy"

# ---------- 1. find the bar ----------
H = open("vaporai.html").read()
n0 = len(H)
shutil.copy("vaporai.html", "vaporai.html.prerebrand")

m = re.search(r"2026 Season", H)
if not m:
    print("1. no '2026 Season' bar in vaporai.html")
else:
    st = m.start()
    op = None
    for tag in ("div", "header", "section"):
        i = H.rfind("<" + tag, max(0, st - 900), st)
        if i > (op[0] if op else -1):
            op = (i, tag)
    if not op or op[0] < 0:
        print("1. found text but no enclosing tag - skipped")
    else:
        i, tag = op
        rx = re.compile(r"</?%s\b" % tag, re.I)
        d, k = 0, i
        en = -1
        while True:
            mm = rx.search(H, k)
            if not mm:
                break
            if H[mm.start():mm.start() + 2] == "</":
                d -= 1
                if d == 0:
                    en = H.index(">", mm.start()) + 1
                    break
            else:
                d += 1
            k = mm.end()
        if en > i:
            print("1. removing bar (%d bytes):" % (en - i))
            print("   %s" % H[i:en][:200].replace("\n", " "))
            H = H[:i] + H[en:]
        else:
            print("1. unbalanced - not removed")

# ---------- 2. rename ----------
c = H.count(OLD)
H = H.replace(OLD, NEW)
H = re.sub(r"(<title>)[^<]*(</title>)",
           r"\1" + NEW + r"\2", H, count=1)
print("2. renamed %d occurrences in vaporai.html" % c)

assert "</script></body></html>" in H, "tail broken"
assert len(H) > n0 * 0.9, "size dropped >10%%"
open("vaporai.html", "w").write(H)
print("   vaporai.html %d -> %d bytes" % (n0, len(H)))

# ---------- 3. generators ----------
hit = 0
for f in sorted(glob.glob("*.py")):
    if f.startswith("313_"):
        continue
    s = open(f).read()
    if OLD not in s and "2026 Season" not in s:
        continue
    s2 = s.replace(OLD, NEW)
    if s2 != s:
        shutil.copy(f, f + ".prerebrand")
        open(f, "w").write(s2)
        hit += 1
        print("3. %s renamed" % f)
    if "2026 Season" in s2:
        print("3. NOTE %s still emits '2026 Season' bar"
              % f)
print("   %d generator files renamed" % hit)

# ---------- 4. logo ----------
f = "289_nav2.py"
s = open(f).read()
LOGO = (
 "      'var lg=mk(\"div\",\"lg\");lg.innerHTML="
 "\\'<svg viewBox=\"0 0 34 34\" fill=\"none\">"
 "<ellipse cx=\"17.5\" cy=\"20\" rx=\"11\" ry=\"7.4\" "
 "transform=\"rotate(-32 17.5 20)\" fill=\"#0a0a0c\" "
 "stroke=\"#0a0a0c\" stroke-width=\"1.4\"/>"
 "<path d=\"M12.6 24.4 22.4 15.6\" stroke=\"#fff\" "
 "stroke-width=\"1.5\" stroke-linecap=\"round\"/>"
 "<path d=\"M15.4 20.2 17.2 22\" stroke=\"#fff\" "
 "stroke-width=\"1.4\" stroke-linecap=\"round\"/>"
 "<path d=\"M17.6 18 19.4 19.8\" stroke=\"#fff\" "
 "stroke-width=\"1.4\" stroke-linecap=\"round\"/>"
 "<circle cx=\"25.4\" cy=\"9.6\" r=\"3.1\" "
 "fill=\"#0a0a0c\"/>"
 "<circle cx=\"29.4\" cy=\"5.4\" r=\"1.8\" "
 "fill=\"#0a0a0c\"/>"
 "<circle cx=\"31.8\" cy=\"2.4\" r=\"1\" "
 "fill=\"#0a0a0c\"/>"
 "</svg>\\';rail.appendChild(lg);\\n'\n")
s2 = re.sub(r"      'var lg=mk\(.*?rail\.appendChild\(lg\);"
            r"\\n'\n", LOGO, s, count=1, flags=re.S)
if s2 != s:
    open(f, "w").write(s2)
    print("4. logo replaced: football + thought bubbles")
else:
    print("4. LOGO PATTERN NOT MATCHED - printing what's there:")
    mm = re.search(r"var lg=mk.{0,260}", s, re.S)
    print("   %s" % (mm.group(0)[:260] if mm else "not found"))
