import re

CSS = '''<style id="finalcss">
:root{
--bg:#0a0a0c;--pnl:rgba(19,19,22,.72);
--pnl2:rgba(28,28,33,.85);
--line:rgba(255,255,255,.09);
--tx:#f2f3f5;--dm:#8b8d94;
--acc:#ffffff;--acc2:#d6d8dd;
--green:#2f7a4a;--blue:#1668f0;
--grad:linear-gradient(135deg,#ffffff 0%,#c9ccd2 100%);}
html,html body{background:
radial-gradient(1100px 600px at 8% -12%,
rgba(255,255,255,.055),transparent 62%),
radial-gradient(900px 520px at 94% -6%,
rgba(255,255,255,.035),transparent 60%),
#0a0a0c!important;color:var(--tx)!important}
#rail{background:rgba(13,13,16,.9)!important;
border-right:1px solid var(--line)!important;
box-shadow:none!important}
#rail button{color:var(--dm)!important}
#rail button i{background:rgba(255,255,255,.055)!important;
border:1px solid rgba(255,255,255,.07)!important}
#rail button:hover{color:var(--tx)!important}
#rail button:hover i{background:rgba(255,255,255,.11)!important}
#rail button.on{color:#0a0a0c!important}
#rail button.on i{background:#fff!important;
box-shadow:0 6px 22px rgba(255,255,255,.22)!important}
#rail .lg{background:#fff!important;animation:none!important}
#rail .lg svg path[fill="#fff"]{fill:#0a0a0c!important}
#rail .lg svg path[stroke]{stroke:#0a0a0c!important}
#subbar{background:rgba(13,13,16,.86)!important;
border-bottom:1px solid var(--line)!important;
border-top:0!important}
#subbar button{color:var(--dm)!important}
#subbar button:hover{background:rgba(255,255,255,.06)!important;
color:var(--tx)!important}
#subbar button.on{background:rgba(255,255,255,.1)!important;
color:#fff!important;
box-shadow:inset 0 -2px 0 #fff!important}
.scorebar{background:rgba(13,13,16,.86)!important;
border-bottom:1px solid var(--line)!important}
.sbrow{color:var(--tx)!important}
.sbrow span.vv,.sbmeta{color:var(--dm)!important}
.sbc{border-right:1px solid var(--line)!important}
.sbc:hover{background:rgba(255,255,255,.06)!important;
box-shadow:inset 0 0 0 1px rgba(255,255,255,.14)!important}
.welc{background:linear-gradient(135deg,#17181c,#0d0e11)
!important;border:1px solid var(--line)!important;
box-shadow:none!important;animation:none!important}
.welc h1{color:#fff!important}
.welc h1 em{color:var(--dm)!important}
.welc p{color:var(--dm)!important}
.welc::after{display:none!important}
.nrow,table.tf,table.st,.hero,section iframe,.tcside,
.gvbx,.dcard,#cardbx,.tcset,#skr,.tcsugbox{
background:var(--pnl)!important;
border:1px solid var(--line)!important;
box-shadow:none!important}
.nrow:hover{border-color:rgba(255,255,255,.22)!important;
box-shadow:0 10px 30px rgba(0,0,0,.5)!important}
.nrow a,.gvhd b,.tcside h3,.tcchip b,.tcrow b,.skrow b,
.dcard h3,.gvt b,.pg h3{color:var(--tx)!important}
.pg h2{background:none!important;color:#fff!important;
-webkit-text-fill-color:#fff!important}
.pg .sub,.pg .note,.hnote,.nmeta,.hsec,.gvsub,.gvmut,
.tctot,.dnote{color:var(--dm)!important}
.pg .note b{color:var(--tx)!important}
.brk{background:#fff!important;color:#0a0a0c!important}
table.tf th,table.st th{color:var(--dm)!important;
border-bottom:1px solid var(--line)!important}
table.tf td,table.st td{color:var(--tx)!important;
border-bottom:1px solid rgba(255,255,255,.06)!important}
table.tf td span{color:var(--dm)!important}
table.tf td.n{color:#fff!important;text-shadow:none!important}
table.tf td.n.d,table.tf td.tg{color:var(--dm)!important}
table.tf td.w,table.tf td.r{color:#7fd7a1!important}
table.tf td.l,table.tf td.g{color:#e88b9a!important}
table.tf td.bb{background:rgba(255,255,255,.07)!important}
table.tf td.bb .bar{background:linear-gradient(90deg,
#8b8d94,#fff)!important}
table.tf td.bb .med{background:#fff!important}
table.tf td.tag.ceiling{color:#c9ccd2!important}
table.tf td.tag.floor{color:#7fd7a1!important}
.tcin input,#skq,.tcset select{background:#0f0f12!important;
color:var(--tx)!important;
border:1px solid rgba(255,255,255,.13)!important}
.tcin input:focus,#skq:focus{border-color:#fff!important;
box-shadow:0 0 0 3px rgba(255,255,255,.1)!important}
.tcsug:hover,.skrow:hover{
background:rgba(255,255,255,.09)!important}
.tcsug u,.tcchip u,.tcrow u,.skrow u,.gvqt td:last-child{
color:#fff!important}
.skrow.pg b{color:#c9ccd2!important}
.tcv.a,.tcv.b{background:var(--blue)!important;
color:#fff!important;box-shadow:none!important}
.tcv.even{background:var(--pnl)!important;color:#fff!important}
.gvov,#cardov{background:rgba(6,6,8,.9)!important}
.gvpl b.up{color:#7fd7a1!important}
.gvpl b.dn{color:#e88b9a!important}
.gvpl u{color:var(--tx)!important}
.gvpl.big{background:rgba(255,255,255,.06)!important}
.gvbar{background:rgba(255,255,255,.12)!important}
.dp.clk:hover{background:rgba(255,255,255,.09)!important;
box-shadow:inset 0 0 0 1px rgba(255,255,255,.18)!important}
a{color:#fff!important}
::selection{background:rgba(255,255,255,.25);color:#fff}
::-webkit-scrollbar-thumb{
background:rgba(255,255,255,.18)!important}
::-webkit-scrollbar-thumb:hover{
background:rgba(255,255,255,.3)!important}
.btn-green{background:var(--green)!important;color:#fff!important}
.btn-blue{background:var(--blue)!important;color:#fff!important}
</style>'''

H = open("vaporai.html").read()
n0 = len(H)
for sid in ("finalcss", "lightcss", "iricss"):
    H = re.sub(r'<style id="%s">.*?</style>' % sid, "", H,
               flags=re.S)
bl = list(re.finditer(r'<style id="[\w-]+">', H))
last = max(bl, key=lambda x: x.start())
j = H.index("</style>", last.start()) + 8
H = H[:j] + CSS + H[j:]
assert H.count('id="finalcss"') == 1
assert 'id="lightcss"' not in H, "light theme not removed"
assert "</script></body></html>" in H, "tail broken"
open("vaporai.html", "w").write(H)
print("light + iridescent removed, final dark theme in")
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
