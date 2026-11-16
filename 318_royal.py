import re

CSS = '''<style id="royalcss">
:root{
--bg:#faf8f3!important;--pnl:#ffffff!important;
--pnl2:#f4f1ea!important;--line:#e3ded1!important;
--tx:#141210!important;--dm:#5f5a52!important;
--gold:#9a7b1f!important;--gold2:#d4af37!important;
--acc:#9a7b1f!important;--acc2:#b8942f!important;
--grad:linear-gradient(135deg,#d4af37 0%,#f0d98a 50%,
#b8942f 100%)!important;}
html,html body{
background-color:#faf8f3!important;
background-image:
radial-gradient(1000px 520px at 8% -12%,
rgba(212,175,55,.16),transparent 62%),
radial-gradient(880px 460px at 94% -6%,
rgba(212,175,55,.10),transparent 58%),
url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='4'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)' opacity='.04'/%3E%3C/svg%3E")
!important;color:#141210!important}
#rail{background:rgba(255,255,255,.9)!important;
border-right:1px solid #e3ded1!important;
box-shadow:1px 0 18px rgba(20,18,16,.05)!important}
#rail button{color:#5f5a52!important}
#rail button i{background:#f4f1ea!important;
border:1px solid #e3ded1!important}
#rail button:hover{color:#141210!important}
#rail button:hover i{background:#f7edcd!important}
#rail button.on{color:#141210!important}
#rail button.on i{background:linear-gradient(135deg,
#d4af37,#f0d98a)!important;border-color:#c9a233!important;
box-shadow:0 5px 16px rgba(212,175,55,.45)!important}
#rail .lg{background:linear-gradient(135deg,#d4af37,
#f0d98a)!important;
box-shadow:0 6px 18px rgba(212,175,55,.4)!important}
#rail .lg svg ellipse{fill:#3a2f10!important;
stroke:#3a2f10!important}
#rail .lg svg circle{fill:#3a2f10!important}
#subbar{background:rgba(255,255,255,.92)!important;
border-bottom:1px solid #e3ded1!important;
border-top:0!important}
#subbar button{color:#5f5a52!important}
#subbar button:hover{background:#f4f1ea!important;
color:#141210!important}
#subbar button.on{background:#f7edcd!important;
color:#5c4708!important;
box-shadow:inset 0 -2px 0 #b8942f!important}
.scorebar{background:rgba(255,255,255,.92)!important;
border-bottom:1px solid #e3ded1!important}
.sbrow{color:#141210!important}
.sbrow span.vv,.sbmeta{color:#5f5a52!important}
.sbc{border-right:1px solid #e3ded1!important}
.sbc:hover{background:#fbf5e3!important;
box-shadow:inset 0 0 0 1px #ddc470!important}
.nrow,table.tf,table.st,.hero,section iframe,.tcside,
.gvbx,.dcard,#cardbx,.tcset,#skr,.tcsugbox,.sscard,
.authbx,.lfeat div{
background:#ffffff!important;
border:1px solid #e3ded1!important;
box-shadow:0 1px 2px rgba(20,18,16,.04),
0 8px 24px rgba(20,18,16,.05)!important}
.nrow:hover{border-color:#c9a233!important;
box-shadow:0 10px 28px rgba(212,175,55,.2)!important}
.welc{background:linear-gradient(135deg,#141210 0%,
#2a2318 55%,#141210 100%)!important;
border:1px solid #c9a233!important;
box-shadow:0 14px 40px rgba(20,18,16,.2)!important}
.welc h1{color:#f7edcd!important}
.welc h1::before{content:"\\2654 ";color:#d4af37}
.welc h1 em{color:#d4af37!important}
.welc p{color:#d8d2c4!important}
.pg h2,.lwrap h1{color:#141210!important;
-webkit-text-fill-color:#141210!important;
background:none!important}
.pg h2::before{content:"\\2654 ";color:#b8942f;
margin-right:6px}
.pg h3,.gvteam h5,.hsec,.gvgrid h4,.tceq h4{
color:#5c4708!important}
.pg .sub,.pg .note,.hnote,.dnote,.gvmut,.tcempty,
.nmeta,.soon p,.lwrap p.lsub,.lfeat p,.authp,
.tcsug span,.tcchip span,.skrow span,.tcrow span,
.gvrp span,.ssrow span,.sscard span,.ssfc,.tctot,
.ssteam span,.tcset label,.lnote,.authfine,.authmsg{
color:#5f5a52!important}
.pg .note b{color:#141210!important}
.brk{background:linear-gradient(135deg,#d4af37,#f0d98a)
!important;color:#3a2f10!important}
table.tf th,table.st th{color:#5c4708!important;
border-bottom:1px solid #e3ded1!important;
background:#faf7ee!important}
table.tf td,table.st td{color:#141210!important;
border-bottom:1px solid #efeade!important}
table.tf td span{color:#5f5a52!important}
table.tf td.n{color:#9a7b1f!important;
text-shadow:none!important;font-weight:700!important}
table.tf td.n.d,table.tf td.tg{color:#5f5a52!important}
table.tf td.w,table.tf td.r{color:#1d7a4a!important}
table.tf td.l,table.tf td.g{color:#b3324a!important}
table.tf td.bb{background:#f0ece1!important}
table.tf td.bb .bar{background:linear-gradient(90deg,
#d4af37,#9a7b1f)!important}
table.tf td.bb .med{background:#141210!important}
table.tf td.tag.ceiling{color:#7a5bb8!important}
table.tf td.tag.floor{color:#1d7a4a!important}
.tcin input,#skq,.tcset select,.ssbar input,
.authbx input[type=email],.ssteam select{
background:#ffffff!important;color:#141210!important;
border:1px solid #d9d2c2!important}
.tcin input:focus,#skq:focus,
.authbx input[type=email]:focus{
border-color:#b8942f!important;
box-shadow:0 0 0 3px rgba(212,175,55,.22)!important}
.tcsug:hover,.skrow:hover{background:#fbf5e3!important}
.tcsug u,.tcchip u,.tcrow u,.skrow u,.gvqt td:last-child,
.ssrow u{color:#9a7b1f!important}
.tcchip{background:#faf7ee!important;
border:1px solid #e3ded1!important}
.tcv{background:#ffffff!important;color:#5f5a52!important;
border:1px solid #e3ded1!important}
.tcv.even{color:#141210!important}
.tcv.a,.tcv.b,.ssverdict.go{
background:linear-gradient(135deg,#141210,#2a2318)!important;
color:#f7edcd!important;border:1px solid #c9a233!important;
box-shadow:0 10px 28px rgba(20,18,16,.18)!important}
.ssverdict.even{background:#ffffff!important;
color:#5f5a52!important;border:1px solid #e3ded1!important}
.ssnum,.sstot b{color:#141210!important}
.ssrow b,.sscard h5{color:#141210!important}
.ssrow b em{color:#5f5a52!important}
.ssrow.ssh b,.ssrow.ssh u{color:#5c4708!important}
.gvov,#cardov,#authov{
background:rgba(250,248,243,.9)!important}
.gvcl,#cardx,.authx,.tcclr,.authout,.acctb{
background:#ffffff!important;color:#5f5a52!important;
border:1px solid #d9d2c2!important}
.acctb.on{background:linear-gradient(135deg,#d4af37,
#f0d98a)!important;color:#3a2f10!important;
border-color:#c9a233!important}
.gvhd b,.gvt b,.dcard h3,.tcside h3,.authbx h3,
.lfeat h4,.soon h3,.nrow a{color:#141210!important}
.gvhd span,.gvsub{color:#5f5a52!important}
.gvbar{background:#e8e3d6!important}
.gvpl{border-bottom:1px solid #efeade!important}
.gvpl span,.gvpl i,.gvpl b{color:#5f5a52!important}
.gvpl u{color:#141210!important}
.gvpl b.up{color:#1d7a4a!important}
.gvpl b.dn{color:#b3324a!important}
.gvpl.big{background:#fbf5e3!important}
.gvqt td,.gvrp{border-bottom:1px solid #efeade!important}
.gvqt td{color:#141210!important}
.dp{color:#141210!important}
.dp.clk:hover{background:#fbf5e3!important;
box-shadow:inset 0 0 0 1px #ddc470!important}
.tmrow{color:#141210!important}
#land{background:
radial-gradient(900px 520px at 20% -10%,
rgba(212,175,55,.2),transparent 60%),#faf8f3!important}
.llogo{background:linear-gradient(135deg,#d4af37,#f0d98a)
!important}
.llogo svg ellipse,.llogo svg circle{fill:#3a2f10!important}
.lskip{color:#5f5a52!important}
.lskip:hover{color:#141210!important}
a{color:#9a7b1f!important}
::selection{background:rgba(212,175,55,.35);color:#141210}
::-webkit-scrollbar-thumb{background:#d9d2c2!important}
::-webkit-scrollbar-thumb:hover{background:#b8942f!important}
</style>'''

H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<style id="royalcss">.*?</style>', "", H, flags=re.S)
bl = list(re.finditer(r'<style id="[\w-]+">', H))
last = max(bl, key=lambda x: x.start())
j = H.index("</style>", last.start()) + 8
H = H[:j] + CSS + H[j:]
assert H.count('id="royalcss"') == 1
assert "</script></body></html>" in H, "tail broken"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav changed: %d" % nav
i = H.index('id="royalcss"')
ok = all(i > H.index('id="%s"' % k) for k in
         ("finalcss", "readcss", "landcss", "authcss")
         if 'id="%s"' % k in H)
print("royal last: %s | nav %d" % (ok, nav))
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
