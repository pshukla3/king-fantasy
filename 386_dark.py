import re

T = {"__BG__": "#0a0a0c", "__PANEL__": "#141417",
     "__P2__": "#1c1c21", "__LINE__": "#2b2b31",
     "__INK__": "#f3f5f6", "__MUT__": "#a5acaf",
     "__GRN__": "#69be28", "__GRNS__": "#8fd94f",
     "__AMB__": "#e0a32e", "__RED__": "#e5544b",
     "__NAVY__": "#00304d"}

CSS = """<style id="kf-theme">
:root{--bg:__BG__!important;--panel:__PANEL__!important;
--line:__LINE__!important;--text:__INK__!important;
--tx:__INK__!important;--muted:__MUT__!important;
--acc:__GRN__!important;--accent:__GRN__!important}
html,body{background:__BG__!important;color:__INK__!important}
body,main,section,article,header,footer,aside,div,p,span,
li,ul,ol,table,tbody,thead,tr,td,th,h1,h2,h3,h4,h5,h6,
b,strong,em,i,u,label,dl,dt,dd
{color:__INK__!important;border-color:__LINE__!important}
.sub,.gvmut,.muted,small,figcaption,.sbmeta,.lbrow u,
.lbcol h5,.slp,.bn,.bnm i,.btb .bp,.bph span
{color:__MUT__!important}
section,.card,.tf,.gvbx,.sbc,.lbcol,.slwrap,.panel,.box,
table,.gvfp,.bpv
{background:__PANEL__!important;
border:1px solid __LINE__!important}
.gvpbx{background:__BG__!important;
border:1px solid __LINE__!important}
th{background:__BG__!important;color:__MUT__!important;
font-weight:700}
tr:nth-child(even) td{background:rgba(255,255,255,.015)
!important}
a{color:__GRN__!important;text-decoration:none;
font-weight:600}
a:hover{color:__GRNS__!important}
input,select,textarea{background:__P2__!important;
color:__INK__!important;border:1px solid __LINE__!important}
#rail{background:__BG__!important;
border-right:1px solid __LINE__!important}
#rail button,#rail a{color:__MUT__!important;
background:transparent!important}
#rail *{background:transparent!important;
box-shadow:none!important}
#rail .on,#rail button.on{color:__GRN__!important;
font-weight:800;
box-shadow:inset 3px 0 0 __GRN__!important}
#rail button i,#rail button.on i,#rail a i
{background:__P2__!important;background-image:none!important}
#rail .lg{display:none!important}
#rank iframe{display:none!important}
.bsp{width:18px}
.btb td.bk{font-weight:700}
.btb tbody tr.brw td{border-top:1px solid #1e1e23!important;border-bottom:1px solid #1e1e23!important}
.injb{text-decoration:none;color:#e0a32e;font-size:10px;font-weight:800;margin-left:6px}
.injb.out{color:#e5544b}
.bpr{font-style:normal;color:#a5acaf;font-size:11px;margin-left:4px}
#subbar{background:__BG__!important;
border-bottom:1px solid __LINE__!important}
.up,.pos{color:__GRN__!important}
.dn,.neg{color:__RED__!important}
.stab.on,.slb.on,.tab.on,.pill.on,button.on,
.bvt button.on,.bfl button.on
{background:__GRN__!important;color:__BG__!important;
border-color:__GRN__!important}
.bvt button,.bfl button{background:__P2__!important;
border:1px solid __LINE__!important;color:__MUT__!important;
border-radius:9px;padding:7px 15px;cursor:pointer;
font-size:11px;font-weight:700;letter-spacing:.06em;
text-transform:uppercase}
.bvt,.bfl{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.bfl input{background:__P2__!important;
border:1px solid __LINE__!important;color:__INK__!important;
border-radius:9px;padding:7px 13px;font-size:12px}
.btb{width:100pc;border-collapse:separate;
border-spacing:0 3px}
.btb th{font-size:10px;color:__MUT__!important;
padding:9px 8px;letter-spacing:.06em;
text-transform:uppercase;text-align:left;
border-bottom:1px solid __LINE__!important}
.btb td{padding:7px 8px;font-size:13px;
background:__PANEL__!important;border:0!important}
.btb tr.brw td:first-child{border-radius:9px 0 0 9px}
.btb tr.brw td:last-child{border-radius:0 9px 9px 0}
.btb td.n,.btb th.n{text-align:right;
font-variant-numeric:tabular-nums}
.btb .bk{color:__MUT__!important;font-size:12px;width:40px}
.btb .bv{font-weight:800;color:__GRN__!important}
.brw{cursor:pointer}
.brw:hover td{background:__P2__!important}
.btr td{background:transparent!important;padding:10px 0 4px}
.tierp{display:inline-block;padding:4px 16px;
border-radius:999px;font-size:12px;font-weight:900;
letter-spacing:.1em;color:__BG__!important}
.bnm{display:flex;align-items:center;gap:10px}
.bnm span{display:flex;flex-direction:column;line-height:1.3}
.bnm i{font-style:normal;font-size:11px;
color:__MUT__!important;font-weight:600}
.bfx{width:34px;height:34px;border-radius:50pc;
object-fit:cover;background:__P2__;flex:0 0 auto}
.bfx0{display:flex;align-items:center;
justify-content:center;font-weight:800;
color:__MUT__!important;font-size:13px}
.posb{display:inline-block;min-width:44px;text-align:center;
padding:3px 8px;border-radius:7px;font-size:11px;
font-weight:800;color:#06070a!important}
.posb.QB{background:#c084fc!important}
.posb.RB{background:#38bdf8!important}
.posb.WR{background:#fb7185!important}
.posb.TE{background:#fbbf24!important}
.posb.K{background:#94a3b8!important}
.posb.DST{background:__GRN__!important}
.cel{display:inline-block;min-width:56px;text-align:right;
padding:4px 10px;border-radius:7px;font-weight:700;
font-variant-numeric:tabular-nums}
.cel.g{background:rgba(105,190,40,.14)!important;
color:__GRNS__!important}
.cel.a{background:rgba(224,163,46,.14)!important;
color:__AMB__!important}
.cel.r{background:rgba(229,84,75,.14)!important;
color:__RED__!important}
.pl{display:inline-block;padding:3px 11px;
border-radius:999px;font-size:12px;font-weight:700;
background:__P2__;color:__INK__!important}
.pl.pg{background:rgba(105,190,40,.14)!important;
color:__GRNS__!important}
.pl.pr{background:rgba(229,84,75,.14)!important;
color:__RED__!important}
#bpov{display:none;position:fixed;inset:0;
background:rgba(0,0,0,.72);z-index:9000;overflow:auto;
padding:36px 16px}
.bpv{max-width:560px;margin:0 auto;border-radius:16px;
padding:20px;box-shadow:0 20px 60px rgba(0,0,0,.6)}
.bpx{float:right;background:transparent;
border:1px solid __LINE__;color:__MUT__;border-radius:8px;
padding:4px 12px;cursor:pointer;font-size:11px}
.bph{display:flex;gap:12px;align-items:center;
margin-bottom:14px}
.bph .bfx{width:60px;height:60px}
.bph b{font-size:20px;display:block}
.bpt{width:100pc;border-collapse:collapse}
.bpt td{padding:7px 0;font-size:13px;
border-bottom:1px solid __LINE__!important;
background:transparent!important}
.bpt td:last-child{text-align:right;font-weight:700;
font-variant-numeric:tabular-nums}
.bpl{font-size:12px;color:__MUT__!important;margin-top:12px;
line-height:1.55}
.bpw{margin:8px 0 0;padding-left:18px;font-size:12px;
color:__RED__!important;line-height:1.5}
</style>"""
for k, v in T.items():
    CSS = CSS.replace(k, v)
CSS = CSS.replace("100pc", "100%").replace("50pc", "50%")

H = open("vaporai.html").read()
n0 = len(H)
for sid in ("kf-light", "kf-theme"):
    H = re.sub('<style id="%s">.*?</style>' % sid, "", H,
               flags=re.S)
i = H.rfind("<script")
assert i > 0
H = H[:i] + CSS + H[i:]
assert H.count('id="kf-theme"') == 1
assert H.count("</script></body></html>") == 1
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav %d" % nav
open("vaporai.html", "w").write(H)
print("black theme applied | %d -> %d | nav %d"
      % (n0, len(H), nav))

def lum(h):
    h = h.lstrip("#")
    v = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        v.append(c / 12.92 if c <= .04045
                 else ((c + .055) / 1.055) ** 2.4)
    return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]

def cr(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + .05) / (min(x, y) + .05)

print("\ncontrast (AA needs 4.5):")
for lab, f, b in (("text on black", "#f3f5f6", "#0a0a0c"),
                  ("text on panel", "#f3f5f6", "#141417"),
                  ("muted on panel", "#a5acaf", "#141417"),
                  ("green on panel", "#8fd94f", "#141417"),
                  ("amber on panel", "#e0a32e", "#141417"),
                  ("red on panel", "#e5544b", "#141417"),
                  ("black on green badge", "#06070a",
                   "#69be28"),
                  ("black on RB badge", "#06070a",
                   "#38bdf8")):
    r = cr(f, b)
    print("  %-22s %5.2f  %s"
          % (lab, r, "PASS" if r >= 4.5 else "CHECK"))
