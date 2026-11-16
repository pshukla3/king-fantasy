import os
import re
import sys

APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

FILES = ["vaporai.html", "113_home.py",
         "158_trade_page.py", "site/_rank.css",
         "site/_teams.css", "site/_player.css"]

CHIP = {"QB": "#f2f4f8", "RB": "#d9dee6",
        "WR": "#c0c6d0", "TE": "#a8aeb9",
        "K": "#9096a1", "DEF": "#7d838e"}
EXACT = {"#f4739a": CHIP["QB"], "#00e07a": CHIP["RB"],
         "#00b4d8": CHIP["WR"], "#fbbf24": CHIP["TE"],
         "#a78bfa": CHIP["K"], "#94a3b8": CHIP["DEF"],
         "#040506": "#0a0a0c", "#08090b": "#0a0a0c"}

HEX = re.compile(
    r"(?<![&\w])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}"
    r"|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})\b")

ROOT = ("\n --bg:#0a0a0c; --panel:#101115;"
        " --panel2:#16181d;\n"
        " --line:#24262d; --text:#e6e8ec;"
        " --dim:#878c96;\n"
        " --sky:#c3c9d4; --sky2:#ffffff;\n")

def grey(m):
    h = m.group(0)[1:]
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h)
    al = h[6:]
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#%02x%02x%02x%s" % (
        int(min(255, y * 0.97)), int(min(255, y)),
        int(min(255, y * 1.07)), al)

def convert(s, f):
    n = 0
    for a, b in EXACT.items():
        c = len(re.findall(a, s, flags=re.I))
        if c:
            s = re.sub(a, b, s, flags=re.I)
            n += c
    k = len(HEX.findall(s))
    s = HEX.sub(grey, s)
    kn = s.count("KING")
    s = s.replace("KING<em>Fantasy</em>",
                  "SHUKIE<em>Fantasy</em>")
    s = s.replace("KING Fantasy", "King Fantasy")
    s = s.replace("KING", "SHUKIE")
    s = s.replace("king fantasy ready", "shukie ready")
    rr = len(re.findall(r"border-radius:\s*\d+px", s))
    s = re.sub(r"border-radius:\s*\d+px",
               "border-radius:3px", s)
    root = 0
    if f == "vaporai.html":
        m = re.search(r":root\{(.*?)\}", s, re.S)
        if m:
            s = s[:m.start(1)] + ROOT + s[m.end(1):]
            root = 1
    return s, n, k, kn, rr, root

print("=== %s ===" % ("APPLYING" if APPLY else "DRY RUN"))
print("  %-20s %6s %6s %5s %6s %5s %8s"
      % ("file", "exact", "grey", "KING", "radii",
         "root", "dsize"))
print("  " + "-" * 64)
for f in FILES:
    if not os.path.exists(f):
        print("  %-20s MISSING" % f)
        continue
    s0 = open(f, errors="ignore").read()
    s1, n, k, kn, rr, root = convert(s0, f)
    d = len(s1) - len(s0)
    print("  %-20s %6d %6d %5d %6d %5d %+8d"
          % (f[:20], n, k, kn, rr, root, d))
    if not APPLY:
        continue
    if len(s1) < len(s0) * 0.9:
        print("     ABORT: size dropped >10%%")
        continue
    open(f + ".prebrand", "w").write(s0)
    open(f, "w").write(s1)
    chk = os.path.getsize(f)
    print("     wrote %d bytes (backup .prebrand)" % chk)
    assert chk > 0, "wrote an empty file"

print("\n=== ANY COLOR LEFT? ===")
bad = 0
for f in FILES:
    if not os.path.exists(f):
        continue
    s = open(f, errors="ignore").read()
    for h in set(HEX.findall(s)):
        c = h[1:7].ljust(6, "0")
        v = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
        if max(v) - min(v) > 26:
            bad += 1
            if bad < 12:
                print("  %-20s %s" % (f[:20], h))
print("  colored hexes: %d" % bad)
