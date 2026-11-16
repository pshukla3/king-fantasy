import re

T = {
 "__BG__": "#f2f3f4",    # light grey canvas
 "__PANEL__": "#ffffff",
 "__LINE__": "#dcdfe1",
 "__INK__": "#002244",   # seahawks navy
 "__MUT__": "#5f686d",   # wolf grey, darkened for contrast
 "__ACC__": "#00declared",
 "__GRN__": "#69be28",   # action green
 "__GRNT__": "#41761a",  # green dark enough to read on white
 "__RED__": "#b3261e",
}
T["__ACC__"] = "#002244"

CSS = """<style id="kf-theme">
:root{--bg:__BG__!important;--panel:__PANEL__!important;
--line:__LINE__!important;--text:__INK__!important;
--tx:__INK__!important;--muted:__MUT__!important;
--acc:__ACC__!important;--accent:__ACC__!important}
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
tr:nth-child(even) td{background:rgba(0,34,68,.02)!important}
a{color:__ACC__!important;text-decoration:none;
font-weight:600}
a:hover{color:__GRNT__!important}
input,select,textarea{background:#fff!important;
color:__INK__!important;border:1px solid __LINE__!important}
#rail{background:__PANEL__!important;
border-right:1px solid __LINE__!important}
#rail button,#rail a{color:__MUT__!important;
background:transparent!important}
#rail *{background:transparent!important;
box-shadow:none!important}
#rail .on,#rail button.on{color:__ACC__!important;
font-weight:800;
box-shadow:inset 3px 0 0 __GRN__!important}
#rail button i,#rail button.on i,#rail a i
{background:__BG__!important;background-image:none!important}
#rail .lg{display:none!important}
#subbar{background:__PANEL__!important;
border-bottom:1px solid __LINE__!important}
.up,.pos{color:__GRNT__!important}
.dn,.neg{color:__RED__!important}
.stab.on,.slb.on,.tab.on,.pill.on,button.on,
.bvt button.on,.bfl button.on
{background:__ACC__!important;color:#fff!important;
border-color:__ACC__!important}
.bvt button,.bfl button{background:__PANEL__!important;
border:1px solid __LINE__!important;color:__MUT__!important;
border-radius:8px;padding:6px 14px;cursor:pointer;
font-size:11px;font-weight:700;letter-spacing:.06em;
text-transform:uppercase}
.bvt,.bfl{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.bfl input{background:#fff!important;
border:1px solid __LINE__!important;color:__INK__!important;
border-radius:8px;padding:6px 12px;font-size:12px}
.btb{width:100pc;border-collapse:collapse}
.btb th{font-size:10px;color:__MUT__!important;padding:9px 8px;
letter-spacing:.06em;text-transform:uppercase;
border-bottom:2px solid __LINE__!important;text-align:left}
.btb td{padding:8px;font-size:13px;
border-bottom:1px solid __LINE__!important}
.btb td.n,.btb th.n{text-align:right;
font-variant-numeric:tabular-nums}
.btb .bk{color:__MUT__!important;font-size:12px;width:38px}
.btb .bv{font-weight:800;background:rgba(0,34,68,.05)
!important}
.brw{cursor:pointer}
.brw:hover{background:rgba(105,190,40,.10)!important}
.btr td{background:__INK__!important;color:#fff!important;
font-size:11px;font-weight:800;letter-spacing:.16em;
text-align:center;padding:7px;font-style:italic}
.bnm{display:flex;align-items:center;gap:10px}
.bnm span{display:flex;flex-direction:column;line-height:1.3}
.bnm i{font-style:normal;font-size:11px;
color:__MUT__!important;font-weight:600}
.bfx{width:34px;height:34px;border-radius:50pc;
object-fit:cover;background:__BG__;flex:0 0 auto}
.bfx0{display:flex;align-items:center;
justify-content:center;font-weight:800;
color:__MUT__!important;font-size:13px}
.pl{display:inline-block;padding:3px 11px;
border-radius:999px;font-size:12px;font-weight:700;
background:#eef0f1;color:__INK__!important}
.pl.pg{background:#dcecd0!important;color:__GRNT__!important}
.pl.pr{background:#f7dcda!important;color:__RED__!important}
#bpov{display:none;position:fixed;inset:0;
background:rgba(0,34,68,.45);z-index:9000;overflow:auto;
padding:36px 16px}
.bpv{max-width:560px;margin:0 auto;border-radius:14px;
padding:20px;box-shadow:0 18px 50px rgba(0,34,68,.25)}
.bpx{float:right;background:transparent;
border:1px solid __LINE__;color:__MUT__;border-radius:8px;
padding:4px 12px;cursor:pointer;font-size:11px}
.bph{display:flex;gap:12px;align-items:center;
margin-bottom:14px}
.bph .bfx{width:60px;height:60px}
.bph b{font-size:20px;display:block}
.bpt{width:100pc;border-collapse:collapse}
.bpt td{padding:7px 0;font-size:13px;
border-bottom:1px solid __LINE__!important}
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
print("seahawks light theme applied | %d -> %d | nav %d"
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

print("\ncontrast checks (AA needs 4.5):")
for lab, f, b in (("navy on grey", "#002244", "#f2f3f4"),
                  ("navy on white", "#002244", "#ffffff"),
                  ("muted on white", "#5f686d", "#ffffff"),
                  ("green text on white", "#41761a", "#ffffff"),
                  ("white on navy", "#ffffff", "#002244"),
                  ("green on navy tier", "#69be28", "#002244")):
    r = cr(f, b)
    print("  %-22s %5.2f  %s"
          % (lab, r, "PASS" if r >= 4.5 else "CHECK"))
