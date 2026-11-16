import re

MAP = {
    "#08090b": "#040506", "#0b0d10": "#040506",
    "#15181e": "#0c0e11", "#1c2028": "#12151a",
    "#272c36": "#1c2027", "#d8dee6": "#e4e9ef",
    "#8b95a5": "#6e7783",
    "#56c2ff": "#00e07a", "#8fd8ff": "#5cffb0",
    "#56c2ff33": "#00e07a26", "#8fd8ff33": "#5cffb026",
    "#2dd4bf": "#00e07a", "#34d399": "#00e07a",
    "#34d39933": "#00e07a26", "#2dd4bf33": "#00e07a26",
    "#60a5fa": "#00b4d8", "#60a5fa33": "#00b4d826",
    "#06222f": "#04120b",
}
FILES = ["112_ui_v4.py", "113_home.py", "114_theme.py",
         "150_league_page.py", "158_trade_page.py",
         "site/_player.css", "site/_rank.css",
         "site/_league.css", "site/_trade.css"]

print("=== REPALETTE: DARKER + ACTION GREEN ===")
for f in FILES:
    try:
        s = open(f).read()
    except IOError:
        print("  %-22s missing" % f)
        continue
    n = 0
    for a, b in sorted(MAP.items(),
                       key=lambda x: -len(x[0])):
        c = s.count(a)
        if c:
            s = s.replace(a, b)
            n += c
    open(f, "w").write(s)
    print("  %-22s %3d swaps" % (f, n))

print("\n=== ANY SKY BLUE LEFT? ===")
for f in FILES:
    try:
        s = open(f).read()
    except IOError:
        continue
    left = [h for h in set(re.findall(
        r"#[0-9a-fA-F]{6,8}", s))
        if h.lower().startswith(("#56c", "#8fd", "#60a",
                                 "#2dd", "#34d"))]
    if left:
        print("  %-22s %s" % (f, sorted(left)))
print("\n  new accent  #00e07a  (action green)")
print("  new base    #040506  (near black)")
