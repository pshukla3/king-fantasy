import re

MAP = {
    "#0d1119": "#08090b", "#0f1420": "#08090b",
    "#151b2b": "#131519", "#141926": "#131519",
    "#1c2130": "#131519", "#141619": "#131519",
    "#232939": "#1b1e24", "#171d2a": "#1b1e24",
    "#222a3a": "#1b1e24", "#2a2f42": "#1b1e24",
    "#2f3648": "#262a33", "#232a3a": "#262a33",
    "#262d3f": "#262a33", "#212736": "#262a33",
    "#1d2331": "#262a33",
    "#e8ecf4": "#dfe4ec", "#8b95a8": "#8b95a5",
    "#7d8697": "#8b95a5", "#6b7486": "#8b95a5",
    "#5a6274": "#6a7280",
    "#2dd4bf": "#56c2ff",
    "#2dd4bf33": "#56c2ff33",
    "#1f3b3a": "#12283a", "#12312e": "#102532",
    "#3a1b28": "#331722",
}
ORD = sorted(MAP, key=len, reverse=True)
CHIP = ("\n.RB{background:#34d39933;color:#34d399}\n"
        ".QB{background:#f4739a33;color:#f4739a}\n"
        ".WR{background:#8fd8ff33;color:#8fd8ff}\n"
        ".TE{background:#fbbf2433;color:#fbbf24}\n"
        ".K{background:#a78bfa33;color:#a78bfa}\n"
        ".DEF{background:#94a3b833;color:#94a3b8}\n"
        ".DST{background:#94a3b833;color:#94a3b8}\n")

for f in ["150_league_page.py", "158_trade_page.py",
          "114_theme.py", "site/_player.css"]:
    try:
        s = open(f).read()
    except IOError:
        print("  %-22s MISSING" % f)
        continue
    n = 0
    for k in ORD:
        c = s.count(k)
        if c:
            s = s.replace(k, MAP[k])
            n += c
    open(f, "w").write(s)
    print("  %-22s %d colors remapped" % (f, n))

s = open("site/_player.css").read()
if ".RB{background:#34d399" not in s:
    open("site/_player.css", "a").write(CHIP)
    print("  appended position chips to _player.css")

for f in ["150_league_page.py", "158_trade_page.py"]:
    s = open(f).read()
    if ".RB{background:#34d399" in s:
        continue
    m = re.search(r'(CSS\s*=\s*""".*?)"""', s, re.S)
    if m:
        s = s[:m.end(1)] + CHIP + s[m.end(1):]
        open(f, "w").write(s)
        print("  injected chips into %s" % f)

print("\n=== LEFTOVER COLORS NOT IN PALETTE ===")
OK = set(MAP.values()) | {"#56c2ff33", "#34d39933",
                          "#8fd8ff33", "#f4739a33",
                          "#fbbf2433", "#a78bfa33",
                          "#94a3b833", "#f4739a",
                          "#8fd8ff", "#fbbf24",
                          "#a78bfa", "#94a3b8",
                          "#34d399", "#56c2ff"}
for f in ["150_league_page.py", "158_trade_page.py",
          "site/_player.css"]:
    try:
        s = open(f).read()
    except IOError:
        continue
    rest = [h for h in set(re.findall(
        r"#[0-9a-fA-F]{3,8}", s)) if h not in OK]
    if rest:
        print("  %-22s %s" % (f, sorted(rest)[:10]))
