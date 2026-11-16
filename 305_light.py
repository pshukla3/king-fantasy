import re

CSS = '''<style id="lightcss">
:root{
--bg:#f4f6fb;--pnl:rgba(255,255,255,.78);
--pnl2:rgba(255,255,255,.94);
--line:rgba(16,20,28,.09);
--tx:#0d1119;--dm:#5f6879;
--aqua:#0fb59a;--lav:#6f6ae6;--pink:#d4629b;
--ice:#3f86ee;--acc:#0fb59a;--acc2:#6f6ae6;
--grad:linear-gradient(135deg,#5ff0d0 0%,#8fb8f5 46%,
#e9bde0 100%);
--gloss:inset 0 1px 0 rgba(255,255,255,.95),
0 10px 32px rgba(16,20,28,.07);}
html,html body{background:
radial-gradient(1100px 620px at 6% -12%,
rgba(95,240,208,.34),transparent 62%),
radial-gradient(1000px 580px at 94% -6%,
rgba(179,176,240,.36),transparent 60%),
radial-gradient(920px 720px at 62% 110%,
rgba(240,194,220,.32),transparent 62%),
#f4f6fb!important;color:var(--tx)!important}
#rail{background:rgba(255,255,255,.72)!important;
backdrop-filter:blur(20px) saturate(1.6);
border-right:1px solid var(--line)!important;
box-shadow:1px 0 24px rgba(16,20,28,.05)!important}
#rail button{color:#5f6879!important}
#rail button i{background:rgba(16,20,28,.05)!important;
border:1px solid rgba(255,255,255,.9)!important}
#rail button:hover{color:var(--tx)!important}
#rail button:hover i{background:rgba(95,240,208,.22)!important}
#rail button.on{color:#0d1119!important}
#rail button.on i{background:var(--grad)!important;
box-shadow:0 6px 20px rgba(95,240,208,.5)!important}
#subbar{background:rgba(255,255,255,.74)!important;
backdrop-filter:blur(18px) saturate(1.5);
border-bottom:1px solid var(--line)!important;
border-top:0!important}
#subbar button{color:#5f6879!important}
#subbar button:hover{background:rgba(16,20,28,.05)!important;
color:var(--tx)!important}
#subbar button.on{background:rgba(95,240,208,.2)!important;
color:#07463c!important;
box-shadow:inset 0 -2px 0 var(--aqua)!important}
.scorebar{background:rgba(255,255,255,.76)!important;
border-bottom:1px solid var(--line)!important;
backdrop-filter:blur(18px)}
.sbrow{color:var(--tx)!important}
.sbrow span.vv{color:var(--dm)!important}
.sbmeta{color:var(--dm)!important}
.sbc{border-right:1px solid var(--line)!important}
.sbc:hover{background:rgba(95,240,208,.16)!important;
box-shadow:inset 0 0 0 1px rgba(15,181,154,.28)!important}
.welc{background:var(--grad)!important;
box-shadow:0 18px 50px rgba(143,184,245,.4)!important}
.welc h1,.welc p{color:#0b1016!important}
.welc h1 em{color:rgba(11,16,22,.6)!important}
.nrow,table.tf,table.st,.hero,section iframe,.tcside,
.gvbx,.dcard,#cardbx,.tcset,#skr,.tcsugbox{
background:var(--pnl)!important;
border:1px solid var(--line)!important;
backdrop-filter:blur(14px) saturate(1.4);
box-shadow:var(--gloss)!important}
.nrow:hover{border-color:rgba(15,181,154,.45)!important;
box-shadow:inset 0 1px 0 rgba(255,255,255,.95),
0 14px 36px rgba(15,181,154,.16)!important;
transform:translateY(-2px)}
.nrow a,.pg h2,.gvhd b,.tcside h3,.tcchip b,.tcrow b,
.skrow b,.dcard h3,.gvt b{color:var(--tx)!important}
.pg h2{background:linear-gradient(92deg,#0d1119,#0fb59a 55%,
#6f6ae6);-webkit-background-clip:text;background-clip:text;
-webkit-text-fill-color:transparent!important}
.pg h3{color:var(--tx)!important}
.pg .sub,.pg .note,.hnote,.nmeta,.hsec,.gvsub,.gvmut,
.tctot,.dnote{color:var(--dm)!important}
.pg .note b{color:var(--tx)!important}
.brk{background:var(--grad)!important;color:#0b1016!important}
table.tf th,table.st th{color:var(--dm)!important;
border-bottom:1px solid var(--line)!important}
table.tf td,table.st td{color:var(--tx)!important;
border-bottom:1px solid rgba(16,20,28,.06)!important}
table.tf td span{color:var(--dm)!important}
table.tf td.n{color:var(--aqua)!important;text-shadow:none!important}
table.tf td.n.d{color:var(--dm)!important}
table.tf td.w{color:#0a9c84!important}
table.tf td.l,table.tf td.g{color:var(--pink)!important}
table.tf td.r{color:#0a9c84!important}
table.tf td.tg{color:var(--lav)!important}
table.tf td.bb{background:rgba(16,20,28,.06)!important}
table.tf td.bb .med{background:#0d1119!important}
table.tf td.tag.ceiling{color:var(--lav)!important}
table.tf td.tag.floor{color:var(--aqua)!important}
.tcin input,#skq{background:#fff!important;
color:var(--tx)!important;
border:1px solid rgba(16,20,28,.14)!important}
.tcin input:focus,#skq:focus{
border-color:var(--aqua)!important;
box-shadow:0 0 0 3px rgba(15,181,154,.16)!important}
.tcset select{background:#fff!important;color:var(--tx)!important;
border:1px solid rgba(16,20,28,.14)!important}
.tcset label{color:var(--dm)!important}
.tcchip{background:rgba(255,255,255,.9)!important;
border:1px solid var(--line)!important}
.tcchip span,.tcsug span,.skrow span,.tcrow span,
.tcempty{color:var(--dm)!important}
.tcsug:hover,.skrow:hover{background:rgba(95,240,208,.2)!important}
.tcsug u,.tcchip u,.tcrow u,.skrow u{color:var(--aqua)!important}
.skrow.pg b{color:var(--lav)!important}
.tcv{background:var(--pnl)!important;color:var(--dm)!important;
border:1px solid var(--line)!important}
.tcv.even{color:var(--tx)!important}
.tcv.a,.tcv.b{background:var(--grad)!important;
color:#0b1016!important;
box-shadow:0 12px 34px rgba(95,240,208,.4)!important}
.tcclr{color:var(--dm)!important;
border:1px solid rgba(16,20,28,.14)!important}
.gvov,#cardov{background:rgba(226,231,242,.82)!important;
backdrop-filter:blur(10px)}
.gvcl,#cardx{background:rgba(255,255,255,.95)!important;
color:var(--dm)!important;
border:1px solid rgba(16,20,28,.14)!important}
.gvhd{border-bottom:1px solid var(--line)!important}
.gvhd span{color:var(--dm)!important}
.gvbar{background:rgba(16,20,28,.1)!important}
.gvpl{border-bottom:1px solid rgba(16,20,28,.07)!important}
.gvpl span,.gvpl i,.gvpl b{color:var(--dm)!important}
.gvpl u{color:var(--tx)!important}
.gvpl b.up{color:#0a9c84!important}
.gvpl b.dn{color:var(--pink)!important}
.gvpl.big{background:rgba(95,240,208,.16)!important}
.gvqt td{color:var(--tx)!important;
border-bottom:1px solid rgba(16,20,28,.07)!important}
.gvqt td:last-child{color:var(--aqua)!important}
.gvrp{border-bottom:1px solid rgba(16,20,28,.07)!important}
.gvrp span{color:var(--dm)!important}
.gvgrid h4,.tceq h4{color:var(--dm)!important}
#cardfr{background:#fff!important}
.dp{color:var(--tx)!important}
.dp.clk:hover{background:rgba(95,240,208,.2)!important;
box-shadow:inset 0 0 0 1px rgba(15,181,154,.3)!important}
.tmrow{color:var(--tx)!important}
.soon,.soon p{color:var(--dm)!important}
.soon h3{color:var(--tx)!important}
a{color:var(--ice)!important}
::selection{background:rgba(95,240,208,.4);color:#0d1119}
::-webkit-scrollbar-thumb{
background:rgba(111,106,230,.3)!important}
::-webkit-scrollbar-thumb:hover{
background:rgba(15,181,154,.45)!important}
</style>'''

H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<style id="lightcss">.*?</style>', "", H,
           flags=re.S)
bl = list(re.finditer(r'<style id="[\w-]+">', H))
last = max(bl, key=lambda x: x.start())
j = H.index("</style>", last.start()) + 8
H = H[:j] + CSS + H[j:]
assert H.count('id="lightcss"') == 1
assert "</script></body></html>" in H, "tail broken"
assert len(H) > n0 * 0.9
open("vaporai.html", "w").write(H)
i = H.index('id="lightcss"')
o = H.index('id="iricss"') if 'id="iricss"' in H else -1
print("injected after %s" % last.group(0))
print("light last: %s (iri@%d light@%d)" % (i > o, o, i))
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
