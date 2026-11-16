import re

IC = {"home": "\u2302", "league": "\u2691",
      "mock": "\u25c8", "rank": "\u25a4",
      "trades": "\u21c4", "calc": "\u2605",
      "rosters": "\u2630"}

CSS = '''<style id="shellcss">
:root{--bg:#0a0b0d;--pnl:#121417;--pnl2:#191c21;
--line:#262a30;--tx:#e9ecef;--dm:#8b9299;
--acc:#4f8cff;--acc2:#a855f7;
--grad:linear-gradient(135deg,#4f8cff 0%,#a855f7 100%);}
body{background:var(--bg)!important;color:var(--tx);
padding-left:226px!important;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",
Inter,sans-serif}
nav{position:fixed!important;left:0;top:0;bottom:0;
width:226px;background:#0c0e11;
border-right:1px solid var(--line);
display:flex!important;flex-direction:column;gap:3px;
padding:18px 12px;z-index:500;overflow-y:auto;
align-items:stretch!important}
nav .brand{font-size:17px;font-weight:800;color:#fff;
padding:4px 12px 20px;letter-spacing:-.02em}
nav .brand em{font-style:normal;background:var(--grad);
-webkit-background-clip:text;background-clip:text;
-webkit-text-fill-color:transparent}
nav button{display:flex!important;align-items:center;
gap:12px;width:100%;text-align:left;background:transparent;
border:0;color:var(--dm);padding:11px 13px;
border-radius:10px;font-size:14px;font-weight:600;
cursor:pointer;transition:background .15s,color .15s;
letter-spacing:0}
nav button::before{content:attr(data-ic);font-size:14px;
width:18px;text-align:center;opacity:.85}
nav button:hover{background:var(--pnl2);color:var(--tx)}
nav button.on{background:var(--grad);color:#fff;
box-shadow:0 4px 16px rgba(79,140,255,.3)}
.scorebar{background:var(--pnl)!important;
border-bottom:1px solid var(--line)!important;
border-radius:0 0 14px 14px;margin-bottom:20px}
.sbc{border-right:1px solid var(--line)!important;
border-radius:10px;margin:6px 3px;
transition:background .15s}
.sbc:hover{background:var(--pnl2)}
.welc{background:var(--grad)!important;border:0!important;
border-radius:18px!important;padding:34px 36px!important;
overflow:hidden}
.welc h1{color:#fff!important;font-size:31px!important}
.welc h1 em{color:rgba(255,255,255,.8)!important}
.welc p{color:rgba(255,255,255,.87)!important}
.hero{border-radius:16px!important;
border-color:var(--line)!important}
.hgrid{gap:28px!important}
.nrow{background:var(--pnl);border:1px solid var(--line);
border-radius:12px;padding:12px!important;
margin-bottom:10px;transition:transform .15s,
border-color .15s}
.nrow:hover{transform:translateY(-2px);
border-color:#3b424b}
.nrow img{border-radius:8px}
.hsec{font-size:11px!important;letter-spacing:.11em;
color:var(--dm)!important;text-transform:uppercase;
font-weight:700!important}
.brk{background:var(--grad);color:#fff!important;
padding:2px 7px;border-radius:5px;font-size:9px;
font-weight:700;letter-spacing:.04em}
table.st{background:var(--pnl);border-radius:12px;
overflow:hidden;border:1px solid var(--line)}
section{padding:0 26px 40px}
section iframe{border-radius:14px;background:var(--pnl)}
.hnote{color:var(--dm)!important;font-size:12px!important}
@media(max-width:1000px){
body{padding-left:64px!important}
nav{width:64px;padding:14px 8px}
nav .brand{font-size:0;padding:4px 0 14px}
nav .brand::after{content:"SF";font-size:15px;
background:var(--grad);-webkit-background-clip:text;
background-clip:text;-webkit-text-fill-color:transparent}
nav button{font-size:0;justify-content:center;padding:12px 0}
nav button::before{font-size:16px;width:auto}}
</style>'''

H = open("vaporai.html").read()
n0 = len(H)

H = re.sub(r'<style id="shellcss">.*?</style>', "", H,
           flags=re.S)

n = 0
for t, ic in IC.items():
    pat = '<button([^>]*)data-t="%s"' % t
    m = re.search(pat, H)
    if not m:
        print("  no button for %s" % t)
        continue
    if 'data-ic' in m.group(0):
        continue
    H = H[:m.start()] + ('<button%sdata-ic="%s" data-t="%s"'
                         % (m.group(1), ic, t)) + H[m.end():]
    n += 1
print("icons added to %d buttons" % n)

if 'class="brand"' not in H:
    m = re.search(r"<nav[^>]*>", H)
    assert m, "no <nav>"
    H = (H[:m.end()]
         + '<div class="brand"><em>Shukie</em> Fantasy</div>'
         + H[m.end():])
    print("brand block inserted")

m = re.search(r"<body[^>]*>", H)
assert m, "no <body>"
H = H[:m.end()] + CSS + H[m.end():]
assert H.count('id="shellcss"') == 1, "css not once"
assert len(H) > n0 * 0.9, "size drop"
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
