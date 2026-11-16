import re

BG, PANEL, LINE = "#f2f8fd", "#ffffff", "#d6e6f3"
INK, MUTED = "#11212e", "#55697a"
ACC, ACC2 = "#0a63a8", "#2e8fd6"

CSS = """<style id="kf-light">
:root{--bg:%(bg)s!important;--panel:%(pn)s!important;
--line:%(ln)s!important;--text:%(ik)s!important;
--tx:%(ik)s!important;--muted:%(mu)s!important;
--acc:%(ac)s!important;--accent:%(ac)s!important}
html,body{background:%(bg)s!important;color:%(ik)s!important}
body,main,section,article,aside,header,footer,
div,p,span,li,ul,ol,td,th,tr,table,tbody,thead,
h1,h2,h3,h4,h5,h6,b,strong,em,i,u,small,label,
figure,figcaption,dl,dt,dd
{color:%(ik)s!important;
border-color:%(ln)s!important}
.sub,.gvmut,.muted,small,figcaption,
.lbrow u,.lbcol h5,.slp,.sbmeta
{color:%(mu)s!important}
section,.card,.tf,.gvbx,.sbc,.lbcol,.slwrap,
.panel,.box,table
{background:%(pn)s!important;
border:1px solid %(ln)s!important}
.gvpbx{background:#f7fbfe!important;
border:1px solid %(ln)s!important}
a{color:%(ac)s!important;text-decoration:none}
a:hover{color:%(a2)s!important}
th{background:#eef6fc!important;color:%(mu)s!important;
font-weight:700}
tr:nth-child(even) td{background:#fafdff!important}
#rail{background:%(pn)s!important;
border-right:1px solid %(ln)s!important}
#rail button,#rail a{color:%(mu)s!important}
#subbar{background:%(pn)s!important;
border-bottom:1px solid %(ln)s!important}
input,select,textarea{background:#fff!important;
color:%(ik)s!important;border:1px solid %(ln)s!important}
.up{color:#0c7040!important}
.dn{color:#c8342f!important}
/* accent chips keep white text - must come last */
#rail .on,#rail button.on,.stab.on,.slb.on,
.htag,.lpts,.tag,.gvfp h5 span,.pill.on,
button.on,.tab.on,.on
{background:%(ac)s!important;color:#fff!important;
border-color:%(ac)s!important}
.lpts.fin{background:#0c7040!important;color:#fff!important}
.lpts.liv{background:#8f5b00!important;color:#fff!important}
.lbrow span.fin{color:#0c7040!important;
background:transparent!important}
.lbrow span.liv{color:#b36b00!important;
background:transparent!important}
#rail .lg svg{filter:drop-shadow(0 2px 8px
rgba(11,127,212,.30))!important}
</style>""" % {"bg": BG, "pn": PANEL, "ln": LINE,
               "ik": INK, "mu": MUTED,
               "ac": ACC, "a2": ACC2}

H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<style id="kf-light">.*?</style>', "", H,
           flags=re.S)
i = H.rfind("<script")
assert i > 0, "no script tag to anchor to"
H = H[:i] + CSS + H[i:]
assert H.count('id="kf-light"') == 1
assert H.count("</script></body></html>") == 1, \
    "TAIL ANCHOR BROKEN - 114_theme.py will fail"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav changed: %d" % nav
open("vaporai.html", "w").write(H)
print("light theme injected | %d -> %d | nav %d"
      % (n0, len(H), nav))

def lum(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    v = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        v.append(c / 12.92 if c <= 0.04045
                 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]

def ratio(a, b):
    x, y = lum(a), lum(b)
    if x < y:
        x, y = y, x
    return (x + 0.05) / (y + 0.05)

print("\n=== CONTRAST (WCAG AA needs 4.5) ===")
PAIRS = [("body text", INK, BG), ("text on card", INK, PANEL),
         ("muted on card", MUTED, PANEL),
         ("link on card", ACC, PANEL),
         ("link on page", ACC, BG),
         ("white on accent", "#ffffff", ACC),
         ("white on green", "#ffffff", "#0c7040"),
         ("white on amber", "#ffffff", "#8f5b00"),
         ("header on th", MUTED, "#eef6fc")]
bad = 0
for nm, f, b in PAIRS:
    r = ratio(f, b)
    ok = "PASS" if r >= 4.5 else ("LARGE-ONLY" if r >= 3
                                  else "FAIL")
    if r < 4.5:
        bad += 1
    print("  %-16s %s on %s  %5.2f  %s"
          % (nm, f, b, r, ok))
print("\n%d pair(s) below 4.5" % bad)
