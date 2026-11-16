import re

CSS = '''<style id="hawkcss">
header,header .wrap,header .bar{display:none!important}
.lbwrap{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));margin:8px 0 18px}
.lbcol{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:10px 12px}
.lbcol h5{margin:0 0 8px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#9ca3af}
.lbrow{display:flex;align-items:center;gap:7px;padding:4px 0;font-size:13px}
.lbrow i{width:14px;color:#6b7280;font-style:normal;font-size:11px}
.lbrow b{flex:1;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lbrow u{text-decoration:none;color:#9ca3af;font-size:10px}
.lbrow span{font-variant-numeric:tabular-nums;font-weight:800}
.lbrow span.fin{color:#10b981}
.lbrow span.liv{color:#ffbe28}
.gvpbx{max-height:240px;overflow-y:auto;border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:6px 8px;background:rgba(0,0,0,.18)}
.gvfw{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:6px}
.gvfp h5{display:flex;align-items:center;gap:6px;margin:0 0 6px;font-size:12px;letter-spacing:.06em;text-transform:uppercase}
.gvfp h5 img{width:18px;height:18px}
.gvfp .gvrp span{font-variant-numeric:tabular-nums;font-weight:700}
.sbc.livegame{background:rgba(105,190,40,.1)!important;box-shadow:inset 0 2px 0 #10b981!important}
.sbrow span.vv.win{color:#10b981!important;font-weight:800}
a.hero{display:block;text-decoration:none;transition:transform .15s,box-shadow .15s}
a.hero:hover{transform:translateY(-2px);box-shadow:0 14px 38px rgba(0,10,20,.55)!important;border-color:#10b981!important}
a.hero h2{color:#fff!important}
a.hero p{color:#d1d5db!important}
.htag{background:#10b981!important;color:#111827!important;font-weight:700}
.dsub{margin:22px 0 10px;font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:#10b981!important;font-weight:700;border-top:1px solid rgba(165,172,175,.2);padding-top:16px}
html body{padding-left:92px!important}
@media(max-width:900px){html body{padding-left:0!important}}
.scorebar{margin:0!important}
:root{
--bg:#111827!important;--pnl:#1f2937!important;
--pnl2:#374151!important;--line:rgba(165,172,175,.24)!important;
--tx:#ffffff!important;--dm:#9ca3af!important;
--acc:#10b981!important;--acc2:#0e9f70!important;
--grad:linear-gradient(135deg,#10b981,#0b7f59)!important;}
html,html body{background-color:#111827!important;
background-image:
radial-gradient(1100px 560px at 8% -12%,
rgba(105,190,40,.14),transparent 62%),
radial-gradient(920px 480px at 94% -6%,
rgba(165,172,175,.10),transparent 58%)!important;
color:#ffffff!important}
#rail{background:rgba(0,19,37,.94)!important;
border-right:1px solid rgba(165,172,175,.2)!important}
#rail button{color:#9ca3af!important}
#rail button i{background:rgba(255,255,255,.06)!important;
border:1px solid rgba(165,172,175,.16)!important}
#rail button:hover{color:#fff!important}
#rail button:hover i{background:rgba(105,190,40,.22)!important}
#rail button.on{color:#ffffff!important}
#rail button.on i{color:#111827!important}
#rail button i{color:#f9fafb!important}
#rail button span{color:inherit!important}
.railout{display:flex!important;flex-direction:column;align-items:center;gap:5px;width:100%;background:none;border:0;color:#9ca3af!important;padding:10px 2px;border-radius:12px;cursor:pointer;font-size:11px;font-weight:600;margin-bottom:6px}
.railout i{font-style:normal;font-size:17px;width:38px;height:38px;border-radius:11px;display:flex;align-items:center;justify-content:center;background:rgba(255,138,155,.14)!important;border:1px solid rgba(255,138,155,.3)!important;color:#ff8a9b!important}
.railout:hover{color:#fff!important}
.railout:hover i{background:rgba(255,138,155,.28)!important}
#rail button.on i{background:#10b981!important;
border-color:#10b981!important;
box-shadow:0 5px 18px rgba(105,190,40,.5)!important}
#rail .lg{background:#10b981!important}
#rail .lg svg ellipse,#rail .lg svg circle{
fill:#1f2937!important;stroke:#1f2937!important}
#subbar{background:rgba(0,19,37,.94)!important;
border-bottom:1px solid rgba(165,172,175,.2)!important;
border-top:0!important}
#subbar button{color:#9ca3af!important}
#subbar button:hover{background:rgba(255,255,255,.08)
!important;color:#fff!important}
#subbar button.on{background:rgba(105,190,40,.2)!important;
color:#fff!important;box-shadow:inset 0 -2px 0 #10b981
!important}
.scorebar{background:rgba(0,19,37,.94)!important;
border-bottom:1px solid rgba(165,172,175,.2)!important}
.sbrow{color:#fff!important}
.sbrow span.vv,.sbmeta{color:#9ca3af!important}
.sbc{border-right:1px solid rgba(165,172,175,.2)!important}
.sbc:hover{background:rgba(105,190,40,.14)!important;
box-shadow:inset 0 0 0 1px rgba(105,190,40,.45)!important}
.nrow,table.tf,table.st,.hero,section iframe,.tcside,
.gvbx,.dcard,#cardbx,.tcset,#skr,.tcsugbox,.sscard,
.authbx,.lfeat div{background:#1f2937!important;
border:1px solid rgba(165,172,175,.22)!important;
box-shadow:0 8px 26px rgba(0,10,20,.4)!important}
.nrow:hover{border-color:#10b981!important;
box-shadow:0 12px 32px rgba(105,190,40,.22)!important}
.welc{background:linear-gradient(135deg,#1f2937,#374151 55%,
#1f2937)!important;border:1px solid #10b981!important}
.welc h1{color:#fff!important}
.welc h1::before{content:""!important;margin:0!important}
.welc h1 em{color:#10b981!important}
.welc p{color:#e5e7eb!important}
.pg h2,.lwrap h1{color:#fff!important;
-webkit-text-fill-color:#fff!important;background:none
!important}
.pg h2::before{content:""!important;margin:0!important}
.pg h3,.gvteam h5,.hsec,.gvgrid h4,.tceq h4{
color:#10b981!important}
.pg .sub,.pg .note,.hnote,.dnote,.gvmut,.tcempty,.nmeta,
.soon p,.lwrap p.lsub,.lfeat p,.authp,.tcsug span,
.tcchip span,.skrow span,.tcrow span,.gvrp span,
.ssrow span,.sscard span,.ssfc,.tctot,.ssteam span,
.tcset label,.lnote,.authfine,.authmsg,.gvhd span,
.gvsub,.ssrow b em{color:#d1d5db!important}
.pg .note b{color:#fff!important}
.brk{background:#10b981!important;color:#111827!important}
table.tf th,table.st th{color:#9ca3af!important;
background:#374151!important;
border-bottom:1px solid rgba(165,172,175,.28)!important}
table.tf td,table.st td{color:#fff!important;
border-bottom:1px solid rgba(165,172,175,.14)!important}
table.tf td span{color:#d1d5db!important}
table.tf td.n{color:#10b981!important;font-weight:700
!important;text-shadow:none!important}
table.tf td.n.d,table.tf td.tg{color:#9ca3af!important}
table.tf td.w,table.tf td.r{color:#10b981!important}
table.tf td.l,table.tf td.g{color:#ff8a9b!important}
table.tf td.bb{background:rgba(255,255,255,.1)!important}
table.tf td.bb .bar{background:linear-gradient(90deg,
#9ca3af,#10b981)!important}
table.tf td.bb .med{background:#fff!important}
table.tf td.tag.ceiling{color:#9ca3af!important}
table.tf td.tag.floor{color:#10b981!important}
.tcin input,#skq,.tcset select,.ssbar input,
.authbx input[type=email],.ssteam select{
background:#111827!important;color:#fff!important;
border:1px solid rgba(165,172,175,.32)!important}
.tcin input:focus,#skq:focus,
.authbx input[type=email]:focus{border-color:#10b981
!important;box-shadow:0 0 0 3px rgba(105,190,40,.22)
!important}
.tcsug:hover,.skrow:hover{
background:rgba(105,190,40,.18)!important}
.tcsug u,.tcchip u,.tcrow u,.skrow u,.ssrow u,
.gvqt td:last-child{color:#10b981!important}
.tcchip{background:#374151!important}
.tcv{background:#1f2937!important;color:#d1d5db!important}
.tcv.even{color:#fff!important}
.tcv.a,.tcv.b,.ssverdict.go{background:#10b981!important;
color:#111827!important;border:0!important}
.ssverdict.even{background:#1f2937!important;
color:#d1d5db!important}
.ssnum,.sstot b,.ssrow b,.sscard h5,.gvhd b,.gvt b,
.dcard h3,.tcside h3,.authbx h3,.lfeat h4,.soon h3,
.nrow a,.gvqt td,.dp,.tmrow,.gvpl u{color:#fff!important}
.ssrow.ssh b,.ssrow.ssh u{color:#9ca3af!important}
.gvov,#cardov,#authov{background:rgba(0,12,24,.93)!important}
.gvcl,#cardx,.authx,.tcclr,.authout,.acctb{
background:#374151!important;color:#d1d5db!important;
border:1px solid rgba(165,172,175,.3)!important}
.acctb.on{background:#10b981!important;color:#111827
!important;border-color:#10b981!important}
.gvbar{background:rgba(255,255,255,.16)!important}
.gvpl{border-bottom:1px solid rgba(165,172,175,.14)
!important}
.gvpl span,.gvpl i,.gvpl b{color:#9ca3af!important}
.gvpl b.up{color:#10b981!important}
.gvpl b.dn{color:#ff8a9b!important}
.gvpl.big{background:rgba(105,190,40,.12)!important}
.gvqt td,.gvrp{border-bottom:1px solid
rgba(165,172,175,.14)!important}
.dp.clk:hover{background:rgba(105,190,40,.18)!important;
box-shadow:inset 0 0 0 1px rgba(105,190,40,.4)!important}
#land{background:radial-gradient(900px 520px at 20% -10%,
rgba(105,190,40,.2),transparent 60%),#111827!important}
.llogo{background:#10b981!important}
.llogo svg ellipse,.llogo svg circle{fill:#1f2937!important}
.lskip{color:#9ca3af!important}
.lskip:hover{color:#fff!important}
a{color:#10b981!important}
::selection{background:rgba(105,190,40,.4);color:#fff}
::-webkit-scrollbar-thumb{
background:rgba(165,172,175,.32)!important}
::-webkit-scrollbar-thumb:hover{background:#10b981!important}
</style>'''

H = open("vaporai.html").read()
n0 = len(H)
for sid in ("hawkcss", "royalcss"):
    H = re.sub(r'<style id="%s">.*?</style>' % sid, "", H,
               flags=re.S)
bl = list(re.finditer(r'<style id="[\w-]+">', H))
last = max(bl, key=lambda x: x.start())
j = H.index("</style>", last.start()) + 8
H = H[:j] + CSS + H[j:]
assert H.count('id="hawkcss"') == 1
assert 'id="royalcss"' not in H, "royal not removed"
assert "</script></body></html>" in H, "tail broken"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav changed: %d" % nav
i = H.index('id="hawkcss"')
ok = all(i > H.index('id="%s"' % k) for k in
         ("finalcss", "readcss", "landcss", "authcss")
         if 'id="%s"' % k in H)
print("hawks last: %s | nav %d" % (ok, nav))
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
