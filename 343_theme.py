import re

BG, SURF, LINE = "#111827", "#1f2937", "#374151"
TXT, MUT = "#f9fafb", "#9ca3af"
POS, NEG, CYA = "#10b981", "#f87171", "#06b6d4"

CSS = """<style id="kf-theme">
:root{--bg:%(bg)s!important;--panel:%(sf)s!important;
--line:%(ln)s!important;--text:%(tx)s!important;
--tx:%(tx)s!important;--muted:%(mu)s!important;
--acc:%(cy)s!important;--accent:%(cy)s!important;
--pos:%(po)s!important;--neg:%(ng)s!important}
html,body{background:%(bg)s!important;color:%(tx)s!important}
body,main,section,article,header,footer,aside,
div,p,span,li,ul,ol,table,tbody,thead,tr,td,th,
h1,h2,h3,h4,h5,h6,b,strong,em,i,u,label,dl,dt,dd
{color:%(tx)s!important;border-color:%(ln)s!important}
.sub,.gvmut,.muted,small,figcaption,.sbmeta,
.lbrow u,.lbcol h5,.slp,.bye,.posrank
{color:%(mu)s!important}
section,.card,.tf,.gvbx,.sbc,.lbcol,.slwrap,
.panel,.box,table,.gvfp
{background:%(sf)s!important;
border:1px solid %(ln)s!important}
.gvpbx{background:%(bg)s!important;
border:1px solid %(ln)s!important}
th{background:%(bg)s!important;color:%(mu)s!important;
font-weight:700}
tr:nth-child(even) td{background:rgba(255,255,255,.02)
!important}
a{color:%(cy)s!important;text-decoration:none}
a:hover{color:#22d3ee!important}
input,select,textarea{background:%(bg)s!important;
color:%(tx)s!important;border:1px solid %(ln)s!important}
#rail{background:%(bg)s!important;
border-right:1px solid %(ln)s!important}
#rail button,#rail a{color:%(mu)s!important}
#subbar{background:%(bg)s!important;
border-bottom:1px solid %(ln)s!important}
.up,.pos,.start{color:%(po)s!important}
.dn,.neg,.sit,.ir{color:%(ng)s!important}
/* filled accents take DARK text - bright mids fail
   contrast against white */
.stab.on,.slb.on,.tab.on,.pill.on,button.on
{background:%(cy)s!important;color:%(bg)s!important;
border-color:%(cy)s!important;font-weight:700}
/* rail: no filled tiles, active = cyan text + edge bar */
#rail *{background:transparent!important;
box-shadow:none!important}
#rail button,#rail a{border:0!important}
#rail .on,#rail button.on{background:transparent!important;
color:%(cy)s!important;font-weight:700;
box-shadow:inset 3px 0 0 %(cy)s!important}
#rail .on svg{opacity:1}
#rail .lg{background:transparent!important;
border:0!important;padding:4px 0!important}
#rail .lg{display:none!important}
.bvt,.bfl{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.bvt button,.bfl button{background:#1f2937;border:1px solid #374151;color:#9ca3af;border-radius:8px;padding:6px 14px;cursor:pointer;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase}
.bvt button.on,.bfl button.on{background:#06b6d4;color:#111827;border-color:#06b6d4}
.bfl input{background:#111827;border:1px solid #374151;color:#f9fafb;border-radius:8px;padding:6px 12px;font-size:12px}
.bn{font-size:11px;color:#9ca3af;margin:6px 0}
.btb{width:100%%;border-collapse:collapse}
.btb th{font-size:10px;color:#9ca3af;padding:8px;letter-spacing:.07em;text-transform:uppercase;border-bottom:1px solid #374151;text-align:left}
.btb td{padding:7px 8px;font-size:13px;border-bottom:1px solid #232f3e}
.btb td.n,.btb th.n{text-align:right;font-variant-numeric:tabular-nums}
.btb .bk{color:#9ca3af;font-size:11px;width:34px}
.btb .bp{color:#9ca3af;font-size:11px}
.btb .bv{font-weight:800;color:#06b6d4}
.brw{cursor:pointer}
.brw:hover{background:rgba(6,182,212,.08)}
.btr td{background:#0c1622!important;color:#9ca3af!important;font-size:10px;font-weight:800;letter-spacing:.14em;text-align:center;padding:5px}
.bnm{display:flex;align-items:center;gap:9px}
.bnm span{display:flex;flex-direction:column;line-height:1.25}
.bnm i{font-style:normal;font-size:10px;color:#9ca3af}
.bfx{width:34px;height:34px;border-radius:50%%;object-fit:cover;background:#111827;flex:0 0 auto}
.bfx0{display:flex;align-items:center;justify-content:center;font-weight:800;color:#9ca3af;font-size:13px}
.pl{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:700;background:rgba(255,255,255,.05)}
.pl.pg{background:rgba(16,185,129,.16);color:#10b981}
.pl.pr{background:rgba(248,113,113,.16);color:#f87171}
#bpov{display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:9000;overflow:auto;padding:36px 16px}
.bpv{max-width:540px;margin:0 auto;background:#1f2937;border:1px solid #374151;border-radius:14px;padding:18px}
.bpx{float:right;background:transparent;border:1px solid #374151;color:#9ca3af;border-radius:8px;padding:4px 12px;cursor:pointer;font-size:11px}
.bph{display:flex;gap:12px;align-items:center;margin-bottom:14px}
.bph .bfx{width:58px;height:58px}
.bph b{font-size:19px;display:block}
.bph span{font-size:11px;color:#9ca3af}
.bpt{width:100%%;border-collapse:collapse}
.bpt td{padding:6px 0;font-size:13px;border-bottom:1px solid #232f3e}
.bpt td:last-child{text-align:right;font-weight:700;font-variant-numeric:tabular-nums}
.bpl{font-size:12px;color:#9ca3af;margin-top:12px;line-height:1.55}
.bpw{margin:8px 0 0;padding-left:18px;font-size:12px;color:#f87171;line-height:1.5}
.rkbar{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.rkbar button{background:#1f2937;border:1px solid #374151;color:#9ca3af;border-radius:6px;padding:5px 12px;cursor:pointer;font-size:11px;font-weight:700}
.rkbar button.on{background:#06b6d4;color:#111827;border-color:#06b6d4}
.rkbar input{background:#111827;border:1px solid #374151;color:#f9fafb;border-radius:6px;padding:5px 10px;font-size:12px}
.rkn{font-size:11px;color:#9ca3af;margin:6px 0}
.rktab{width:100%%;border-collapse:collapse}
.rktab td,.rktab th{padding:5px 8px;font-size:13px}
.rktab td.n,.rktab th.n{text-align:right;font-variant-numeric:tabular-nums}
.rktab .rkr{color:#9ca3af;font-size:11px;width:38px}
.rktab .up{color:#10b981;font-weight:700}
.rktab .dn{color:#f87171;font-weight:700}
.rktab tbody tr:hover{background:rgba(6,182,212,.07)}
#rail button i,#rail button.on i,#rail button:hover i,#rail a i{background:#ffffff!important;background-image:none!important}
.htag,.lpts.fin
{background:%(po)s!important;color:%(bg)s!important;
border-color:%(po)s!important;font-weight:800}
.lpts.liv
{background:%(cy)s!important;color:%(bg)s!important;
font-weight:800}
.lbrow span.fin{color:%(po)s!important;
background:transparent!important}
.lbrow span.liv{color:%(cy)s!important;
background:transparent!important}
.tag.ceiling{background:%(po)s!important;
color:%(bg)s!important}
.tag.floor{background:%(cy)s!important;
color:%(bg)s!important}
.sbc.livegame{background:rgba(6,182,212,.10)!important;
box-shadow:inset 0 2px 0 %(cy)s!important}
.sbrow span.vv.win{color:%(po)s!important}
rgba(6,182,212,.30))!important}
</style>""" % {"bg": BG, "sf": SURF, "ln": LINE, "tx": TXT,
               "mu": MUT, "po": POS, "ng": NEG, "cy": CYA}

H = open("vaporai.html").read()
n0 = len(H)
for sid in ("kf-light", "kf-theme"):
    H = re.sub(r'<style id="%s">.*?</style>' % sid, "", H,
               flags=re.S)
i = H.rfind("<script")
assert i > 0, "no script tag to anchor to"
H = H[:i] + CSS + H[i:]
assert H.count('id="kf-theme"') == 1
assert H.count('id="kf-light"') == 0
assert H.count("</script></body></html>") == 1, \
    "TAIL ANCHOR BROKEN - 114_theme.py will fail"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav changed: %d" % nav
open("vaporai.html", "w").write(H)
print("stadium theme injected | %d -> %d | nav %d"
      % (n0, len(H), nav))

def lum(h):
    h = h.lstrip("#")
    v = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        v.append(c / 12.92 if c <= 0.04045
                 else ((c + 0.055) / 1.055) ** 2.4)
    return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]

def ratio(a, b):
    x, y = lum(a), lum(b)
    return ((max(x, y) + .05) / (min(x, y) + .05))

print("\n=== CONTRAST (AA needs 4.5) ===")
P = [("text on bg", TXT, BG), ("text on card", TXT, SURF),
     ("muted on bg", MUT, BG), ("muted on card", MUT, SURF),
     ("green on card", POS, SURF), ("red on card", NEG, SURF),
     ("cyan on card", CYA, SURF), ("cyan link on bg", CYA, BG),
     ("dark on cyan fill", BG, CYA),
     ("dark on green fill", BG, POS)]
bad = 0
for nm, f, b in P:
    r = ratio(f, b)
    tag = "PASS" if r >= 4.5 else (
        "LARGE-ONLY" if r >= 3 else "FAIL")
    bad += (r < 4.5)
    print("  %-19s %-8s on %-8s %5.2f  %s"
          % (nm, f, b, r, tag))
print("\n%d pair(s) below 4.5" % bad)
