import re

# Los Angeles Chargers
BOLT = "#0080C6"   # powder blue
GOLD = "#FFC20E"   # sunshine gold
NAVY = "#002A5E"   # navy

P = {
    "bg":     "#04121F",
    "panel":  "#0A1E33",
    "panel2": "#102C47",
    "line":   "#1C4265",
    "text":   "#EAF2F8",
    "dim":    "#93AFC6",
    "acc":    BOLT,
    "acc2":   GOLD,
    "link":   "#4FB3E8",
    "grad":   "linear-gradient(135deg,%s 0%%,%s 100%%)"
              % (BOLT, NAVY),
}


def lum(h):
    h = h.lstrip("#")
    o = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        o.append(c / 12.92 if c <= 0.03928
                 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * o[0] + 0.7152 * o[1] + 0.0722 * o[2]


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


print("=== contrast against background %s ===" % P["bg"])
for k in ("text", "dim", "acc", "acc2", "link"):
    r = ratio(P[k], P["bg"])
    tag = "AAA" if r >= 7 else ("AA" if r >= 4.5 else
                                ("AA-large" if r >= 3
                                 else "FAIL"))
    print("  %-6s %-9s %5.2f:1  %s" % (k, P[k], r, tag))

VARS = []
for a, b in (("bg", "bg"), ("panel", "panel"),
             ("panel", "pnl"), ("panel2", "panel2"),
             ("panel2", "pnl2"), ("line", "line"),
             ("text", "text"), ("text", "tx"),
             ("dim", "dim"), ("dim", "dm"),
             ("dim", "muted"), ("acc", "acc"),
             ("acc", "accent"), ("acc2", "acc2"),
             ("link", "sky"), ("link", "sky2"),
             ("acc", "blue"), ("grad", "grad")):
    VARS.append("--%s:%s!important" % (b, P[a]))
VARS.append("--green:#2F8F5B!important")

CSS = ("<style id=\"kfbolt\">:root{" + ";".join(VARS)
       + "}\n"
       "a{color:%s}\n"
       "nav button.on,.stab.on,.kftabs button.on{"
       "border-bottom-color:%s}\n"
       "#rail button.on{background:%s;color:#fff}\n"
       "#subbar button.on{background:%s;color:#04121F;"
       "font-weight:700}\n"
       "</style>" % (P["link"], GOLD, BOLT, GOLD))

H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<style id="kfbolt">.*?</style>', "", H,
           flags=re.S)

# Insert before the FINAL script tag so the
# </script></body></html> anchor 114_theme.py needs
# survives intact.
i = H.rfind("<script")
assert i > 0, "no script tag found"
H = H[:i] + CSS + H[i:]
assert H.count("</script></body></html>") == 1, "tail anchor"
assert H.count('<style id="kfbolt">') == 1
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav %d" % nav
open("vaporai.html", "w").write(H)
print("\nvaporai.html %d -> %d | nav %d" % (n0, len(H), nav))

# --- repaint the pages I generated ---------------------
MAP = {
    "#c9a227": GOLD, "#0d0d10": P["bg"],
    "#101013": P["panel"], "#131318": P["panel"],
    "#0a0a0c": P["bg"], "#0f1a12": "#0B2E1C",
    "#1a1610": "#12314B", "#111": "#04121F",
    "#26262b": P["line"], "#232327": P["line"],
    "#26262c": P["line"], "#22222a": P["line"],
    "#1e1e24": P["line"], "#1c1c20": P["line"],
    "#1c1c22": P["line"], "#2a2a30": P["panel2"],
    "#2a2a42": P["panel2"], "#33333b": P["line"],
    "#3a3a42": P["line"], "#17171c": P["panel"],
    "#e8e8ea": P["text"], "#c8c8d0": P["text"],
    "#8a8a92": P["dim"], "#9a9aa2": P["dim"],
    "#6a6a72": P["dim"], "#b4b4bc": P["dim"],
    "#eee": P["text"], "#ccc": P["dim"],
    "#333": P["line"], "#444": P["line"],
    "#888": P["dim"], "#bbb": P["dim"],
}

for f in ("site/matchup.html", "site/myteam.html",
          "site/_card.js", "site/_connect.js"):
    try:
        s = open(f).read()
    except IOError:
        print("  %-22s MISSING" % f)
        continue
    n = 0
    for a, b in MAP.items():
        c = s.count(a)
        if c:
            s = s.replace(a, b)
            n += c
    open(f, "w").write(s)
    print("  %-22s %d colours repainted" % (f, n))
