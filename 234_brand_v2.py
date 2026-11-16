import re
import os

FILES = ["112_ui_v4.py", "113_home.py", "114_theme.py",
         "150_league_page.py", "158_trade_page.py",
         "192_rank_page.py", "200_live_teams.py",
         "site/_player.css", "site/_rank.css",
         "site/_league.css", "site/_trade.css",
         "site/_teams.css"]

CHIP = {"QB": "#f2f4f8", "RB": "#d9dee6",
        "WR": "#c0c6d0", "TE": "#a8aeb9",
        "K":  "#9096a1", "DEF": "#7d838e"}

EXACT = {"#f4739a": CHIP["QB"],
         "#00e07a": CHIP["RB"],
         "#00b4d8": CHIP["WR"],
         "#fbbf24": CHIP["TE"],
         "#a78bfa": CHIP["K"],
         "#94a3b8": CHIP["DEF"],
         "#040506": "#0a0a0c",
         "#08090b": "#0a0a0c"}

def grey(m):
    h = m.group(0)[1:]
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    al = h[6:]
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#%02x%02x%02x%s" % (
        int(min(255, y * 0.97)),
        int(min(255, y * 1.00)),
        int(min(255, y * 1.07)), al)

HEX = re.compile(r"#[0-9a-fA-F]{3,8}")
print("=== MONOCHROME PASS ===")
for f in FILES:
    if not os.path.exists(f):
        continue
    s = open(f).read()
    n = 0
    for a, b in EXACT.items():
        c = len(re.findall(a, s, flags=re.I))
        if c:
            s = re.sub(a, b, s, flags=re.I)
            n += c
    k = len(HEX.findall(s))
    open(f, "w").write(HEX.sub(grey, s))
    print("  %-22s %3d exact | %3d greyed"
          % (f, n, k))

ROOT = ("\n --bg:#0a0a0c; --panel:#101115;"
        " --panel2:#16181d;\n"
        " --line:#24262d; --text:#e6e8ec;"
        " --dim:#878c96;\n"
        " --sky:#c3c9d4; --sky2:#ffffff;\n")

print("\n=== SHARPEN + BRAND ===")
for f in FILES:
    if not os.path.exists(f):
        continue
    s = open(f).read()
    r = len(re.findall(r"border-radius:\s*\d+px", s))
    s = re.sub(r"border-radius:\s*\d+px",
               "border-radius:3px", s)
    kn = s.count("KING")
    s = s.replace("KING<em>Fantasy</em>",
                  "SHUKIE<em>Fantasy</em>")
    s = s.replace("KING Fantasy", "King Fantasy")
    s = s.replace("KING", "SHUKIE")
    s = s.replace("king fantasy ready", "shukie ready")
    if f == "112_ui_v4.py":
        m = re.search(r":root\{(.*?)\}", s, re.S)
        if m:
            s = s[:m.start(1)] + ROOT + s[m.end(1):]
            print("  :root palette replaced")
        else:
            print("  WARNING :root not found in 112")
    open(f, "w").write(s)
    if r or kn:
        print("  %-22s %3d radii | %2d KING"
              % (f, r, kn))

SHARP = """
*{font-feature-settings:"tnum" 1,"cv02" 1}
h1,h2,h3,.brand{letter-spacing:-.02em}
th,.kpi-l,.hd,.lbl,.sl{letter-spacing:.09em;
text-transform:uppercase;font-size:10px;
font-weight:700;color:var(--dim)}
nav button{border-radius:2px;font-size:12px;
letter-spacing:.06em;text-transform:uppercase}
nav button.on{background:var(--sky);color:#0a0a0c}
.brand em{color:var(--sky);font-style:normal}
table{border-collapse:collapse}
"""
p = "112_ui_v4.py"
s = open(p).read()
if "cv02" not in s:
    i = s.find("</style>")
    if i > 0:
        s = s[:i] + SHARP + s[i:]
        open(p, "w").write(s)
        print("\n  sharp type rules injected")
    else:
        print("\n  WARNING no </style> in 112")
else:
    print("\n  already injected")

print("\n=== ANY COLOR LEFT? ===")
bad = 0
for f in FILES:
    if not os.path.exists(f):
        continue
    s = open(f).read()
    for h in set(HEX.findall(s)):
        c = h[1:7].ljust(6, "0")
        v = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
        if max(v) - min(v) > 26:
            bad += 1
            print("  %-22s %s" % (f, h))
print("  colored hexes remaining: %d" % bad)
