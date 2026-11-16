import re

CSS = '''<style id="polishcss">
html body nav{display:none!important}
#subbar{position:relative!important;top:auto!important;
z-index:5!important;background:rgba(14,16,20,.72)!important;
backdrop-filter:blur(14px) saturate(1.5);
border-top:1px solid rgba(255,255,255,.05)}
body{background:
radial-gradient(1100px 560px at 12% -12%,
rgba(79,140,255,.11),transparent 62%),
radial-gradient(900px 480px at 96% -4%,
rgba(168,85,247,.10),transparent 58%),
#07080a!important;
font-variant-numeric:tabular-nums}
#rail{background:rgba(11,13,16,.86)!important;
backdrop-filter:blur(16px) saturate(1.4);
border-right:1px solid rgba(255,255,255,.06)!important}
#rail button.on i{
box-shadow:0 0 0 1px rgba(79,140,255,.55),
0 10px 30px rgba(79,140,255,.42)!important}
#rail button i{border:1px solid rgba(255,255,255,.05)}
#subbar button.on{background:rgba(79,140,255,.14)!important;
box-shadow:inset 0 -2px 0 #4f8cff,
0 0 22px rgba(79,140,255,.18)!important}
.nrow,table.tf,table.st,.hero,section iframe{
border:1px solid rgba(255,255,255,.07)!important;
background:rgba(18,21,26,.66)!important;
backdrop-filter:blur(8px)}
.nrow:hover{border-color:rgba(79,140,255,.42)!important;
box-shadow:0 10px 34px rgba(0,0,0,.5),
0 0 0 1px rgba(79,140,255,.18)}
.welc{position:relative;border:1px solid
rgba(255,255,255,.10)!important;
background:linear-gradient(135deg,#4f8cff 0%,
#7c5cff 48%,#a855f7 100%)!important;
box-shadow:0 18px 60px rgba(79,140,255,.28)}
.welc::after{content:"";position:absolute;inset:0;
background:radial-gradient(600px 200px at 85% 0%,
rgba(255,255,255,.22),transparent 60%);
pointer-events:none}
.scorebar{background:rgba(14,16,20,.72)!important;
backdrop-filter:blur(14px) saturate(1.5);
border-bottom:1px solid rgba(255,255,255,.06)!important}
.sbc:hover{background:rgba(79,140,255,.09)!important;
box-shadow:inset 0 0 0 1px rgba(79,140,255,.22)}
table.tf td.n{color:#7fb2ff!important;
text-shadow:0 0 14px rgba(79,140,255,.35)}
.pg h2{background:linear-gradient(90deg,#fff,#9dc0ff);
-webkit-background-clip:text;background-clip:text;
-webkit-text-fill-color:transparent}
.dp.clk{cursor:pointer;border-radius:8px;transition:background .13s,box-shadow .13s}
.dp.clk:hover{background:rgba(79,140,255,.13);box-shadow:inset 0 0 0 1px rgba(79,140,255,.3)}
.dp.clk:active{transform:scale(.99)}
.pg h3{margin:28px 0 10px;font-size:15px;color:#e9ecef}
.pg .note{color:#8b9299;font-size:12px;line-height:1.65;max-width:680px;margin:10px 0 0}
.pg .note b{color:#e9ecef}
table.tf td.w{color:#81c995!important}
table.tf td.l{color:#f28b82!important}
#cardov{position:fixed;inset:0;z-index:9500;background:rgba(4,5,7,.88);display:none;align-items:flex-start;justify-content:center;padding:30px 16px;overflow-y:auto;backdrop-filter:blur(7px)}
#cardbx{position:relative;width:100%;max-width:940px;background:#0d0e10;border:1px solid rgba(255,255,255,.09);border-radius:16px;overflow:hidden;box-shadow:0 30px 90px rgba(0,0,0,.72)}
#cardfr{width:100%;height:78vh;border:0;display:block;background:#0d0e10}
#cardx{position:absolute;top:12px;right:14px;z-index:2;background:rgba(26,28,31,.92);color:#9aa0a6;border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:6px 12px;cursor:pointer;font-size:11px}
table.tf td.tg{color:#8ab4f8;font-weight:700;width:42px}
table.tf td.bb{position:relative;height:16px;min-width:170px;background:rgba(255,255,255,.04);border-radius:8px}
table.tf td.bb .bar{position:absolute;top:4px;height:8px;border-radius:5px;background:linear-gradient(90deg,#4f8cff,#a855f7)}
table.tf td.bb .med{position:absolute;top:1px;width:2px;height:14px;background:#fff;opacity:.85}
table.tf td.tag{font-size:10px;text-transform:uppercase;letter-spacing:.07em}
table.tf td.tag.ceiling{color:#a855f7}
table.tf td.tag.floor{color:#81c995}
.tcgrid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0}
.tcside{background:rgba(18,21,26,.66);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:16px 16px 18px}
.tcside h3{margin:0 0 12px;font-size:16px;color:#e9ecef}
.tcin{position:relative}
.tcin input{width:100%;background:rgba(9,11,14,.9);border:1px solid rgba(255,255,255,.12);border-radius:10px;padding:11px 13px;color:#e9ecef;font-size:13px;outline:none;box-sizing:border-box}
.tcin input:focus{border-color:rgba(79,140,255,.6);box-shadow:0 0 0 3px rgba(79,140,255,.14)}
.tcsugbox{position:absolute;left:0;right:0;top:46px;z-index:40;background:#0f1216;border:1px solid rgba(255,255,255,.12);border-radius:10px;overflow:hidden;box-shadow:0 18px 44px rgba(0,0,0,.6)}
.tcsug{display:flex;align-items:center;gap:9px;padding:9px 12px;cursor:pointer;font-size:13px}
.tcsug:hover{background:rgba(79,140,255,.14)}
.tcsug b{flex:1;color:#e9ecef;font-weight:600}
.tcsug span{color:#8b9299;font-size:11px}
.tcsug u{text-decoration:none;color:#8ab4f8;font-weight:700;font-size:12px}
.tcchip{display:flex;align-items:center;gap:9px;background:rgba(9,11,14,.7);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:9px 11px;margin-top:9px;cursor:pointer}
.tcchip:hover{border-color:rgba(242,139,130,.5)}
.tcchip b{flex:1;font-size:13px;color:#e9ecef}
.tcchip span{color:#8b9299;font-size:11px}
.tcchip u{text-decoration:none;color:#8ab4f8;font-weight:700;font-size:12px}
.tcchip em{font-style:normal;color:#5f6368;font-size:14px}
.tcempty{color:#5f6368;font-size:12px;padding:14px 2px}
.tctot{display:flex;justify-content:space-between;align-items:center;margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,.08);color:#8b9299;font-size:11px;text-transform:uppercase;letter-spacing:.08em}
.tctot b{font-size:21px;color:#e9ecef;letter-spacing:0}
.tcv{border-radius:12px;padding:15px 18px;font-size:14px;font-weight:600;text-align:center;color:#8b9299;background:rgba(18,21,26,.66);border:1px solid rgba(255,255,255,.08)}
.tcv.even{color:#e9ecef;border-color:rgba(255,255,255,.18)}
.tcv.a,.tcv.b{color:#fff;border-color:transparent;background:linear-gradient(135deg,#4f8cff,#a855f7);box-shadow:0 12px 36px rgba(79,140,255,.28)}
.tcclr{margin-top:12px;background:none;border:1px solid rgba(255,255,255,.14);color:#8b9299;border-radius:9px;padding:8px 14px;font-size:11px;cursor:pointer}
.tcclr:hover{color:#e9ecef;border-color:rgba(79,140,255,.5)}
.tceq{margin-top:22px}
.tceq h4{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:#8b9299;margin:0 0 10px}
.tcrow{display:flex;align-items:center;gap:10px;padding:9px 12px;border-bottom:1px solid #1c1f24;font-size:13px}
.tcrow b{flex:1;color:#e9ecef;font-weight:600}
.tcrow span{color:#8b9299;font-size:11px}
.tcrow u{text-decoration:none;color:#8ab4f8;font-weight:700}
#skwrap{margin-left:auto;position:relative;flex:0 0 260px}
#skq{width:100%;background:rgba(9,11,14,.85);border:1px solid rgba(255,255,255,.12);border-radius:9px;padding:8px 12px;color:#e9ecef;font-size:12.5px;outline:none;box-sizing:border-box}
#skq:focus{border-color:rgba(79,140,255,.6);box-shadow:0 0 0 3px rgba(79,140,255,.14)}
#skr{display:none;position:absolute;right:0;left:0;top:40px;z-index:600;background:#0f1216;border:1px solid rgba(255,255,255,.12);border-radius:11px;overflow:hidden;box-shadow:0 20px 50px rgba(0,0,0,.65)}
#skr.on{display:block}
.skrow{display:flex;align-items:center;gap:9px;padding:9px 12px;cursor:pointer;font-size:12.5px}
.skrow:hover{background:rgba(79,140,255,.15)}
.skrow b{flex:1;color:#e9ecef;font-weight:600}
.skrow span{color:#8b9299;font-size:10.5px;text-transform:uppercase;letter-spacing:.06em}
.skrow u{text-decoration:none;color:#8ab4f8;font-weight:700;font-size:11.5px}
.skrow.pg b{color:#8ab4f8;text-transform:capitalize}
.tcset{display:flex;gap:14px;flex-wrap:wrap;align-items:center;background:rgba(18,21,26,.66);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:12px 16px;margin:16px 0}
.tcset label{display:flex;align-items:center;gap:8px;font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#8b9299}
.tcset select{background:#0b0d10;color:#e9ecef;border:1px solid rgba(255,255,255,.14);border-radius:8px;padding:6px 9px;font-size:12.5px;text-transform:none;letter-spacing:0}
.tcset .tcsw{cursor:pointer}
.tcset input[type=checkbox]{width:16px;height:16px;accent-color:#4f8cff;cursor:pointer}
.gvpl{display:grid;grid-template-columns:64px 58px 1fr 56px;gap:9px;align-items:baseline;padding:9px 0;border-bottom:1px solid #1c1f24;font-size:12.5px;line-height:1.5}
.gvpl span{color:#5f6368;font-size:10px;letter-spacing:.05em}
.gvpl i{font-style:normal;color:#8b9299;font-size:10px;text-transform:uppercase;letter-spacing:.05em}
.gvpl u{text-decoration:none;color:#c8ccd0}
.gvpl b{text-align:right;font-size:11.5px;color:#5f6368;font-weight:700}
.gvpl b.up{color:#81c995}
.gvpl b.dn{color:#f28b82}
.gvpl.big u{color:#e9ecef;font-weight:600}
.gvpl.big{background:rgba(79,140,255,.07);border-radius:8px;padding-left:8px;padding-right:8px}
.gvhd b{display:flex;align-items:center;gap:9px}
.gvlg{width:30px;height:30px;object-fit:contain;flex:0 0 auto}
.gvhd b em{font-style:normal;color:#5f6368;font-size:14px;margin:0 3px}
.gvteam{margin-bottom:16px}
.gvteam h5{display:flex;align-items:center;gap:7px;margin:0 0 6px;padding-bottom:6px;font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:#e9ecef;font-weight:700;border-bottom:2px solid #4f8cff}
.gvteam h5 img{width:18px;height:18px;object-fit:contain}
.ssbar{display:flex;gap:10px;margin:16px 0 20px}
.ssbar input{flex:1;max-width:320px;background:#0f0f12;border:1px solid rgba(255,255,255,.13);border-radius:9px;padding:10px 13px;color:#f2f3f5;font-size:13px}
.ssbar button{border:0;border-radius:9px;padding:10px 20px;font-size:13px;font-weight:600;cursor:pointer}
.ssteam{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.ssteam span{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#8b8d94}
.ssteam .dim2{text-transform:none;letter-spacing:0;font-size:12px}
.ssteam select{background:#0f0f12;color:#f2f3f5;border:1px solid rgba(255,255,255,.13);border-radius:8px;padding:7px 10px;font-size:13px}
.ssrow{display:grid;grid-template-columns:74px 1fr 62px;gap:10px;align-items:baseline;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:13px}
.ssrow span{color:#8b8d94;font-size:10px;letter-spacing:.07em;text-transform:uppercase}
.ssrow b{color:#f2f3f5;font-weight:600}
.ssrow b em{font-style:normal;color:#8b8d94;font-size:11px;margin-left:6px}
.ssrow u{text-decoration:none;text-align:right;color:#fff;font-weight:700}
.ssrow.ssh{border-bottom:1px solid rgba(255,255,255,.14)}
.ssrow.ssh b,.ssrow.ssh u{color:#8b8d94;font-size:10px;text-transform:uppercase;letter-spacing:.07em;font-weight:600}
.ssrow.dim b,.ssrow.dim u{color:#8b8d94}
.sstot{display:flex;justify-content:space-between;align-items:center;padding:14px 0 4px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8b8d94}
.sstot b{font-size:24px;color:#fff;letter-spacing:0}
.ssvs{display:grid;grid-template-columns:1fr 40px 1fr;align-items:center;gap:12px;margin:20px 0}
.ssvs i{font-style:normal;text-align:center;color:#8b8d94;font-size:11px;text-transform:uppercase}
.sscard{background:rgba(19,19,22,.72);border:1px solid rgba(255,255,255,.09);border-radius:12px;padding:16px}
.sscard h5{margin:0 0 3px;font-size:15px;color:#f2f3f5}
.sscard span{color:#8b8d94;font-size:11px}
.ssnum{font-size:30px;font-weight:700;color:#fff;margin:8px 0 2px}
.ssfc{color:#8b8d94;font-size:11px}
.ssverdict{border-radius:12px;padding:15px 18px;text-align:center;font-size:15px;font-weight:600;color:#fff}
.ssverdict.go{background:#1668f0}
.ssverdict.even{background:rgba(19,19,22,.72);border:1px solid rgba(255,255,255,.12);color:#8b8d94}
@media(max-width:900px){.ssvs{grid-template-columns:1fr!important}
.ssvs i{padding:4px 0}
.ssrow{grid-template-columns:56px 1fr 52px!important}
.gvpl{grid-template-columns:52px 1fr 50px!important}
.gvpl i{display:none}
#skwrap{flex:1 1 100%!important;margin:6px 0 0!important;order:9}
#skq{font-size:16px!important}
.tcgrid{grid-template-columns:1fr!important}

html body{padding-left:0!important;
padding-bottom:76px!important}
#rail{top:auto!important;right:0;width:auto!important;
height:68px;flex-direction:row!important;
justify-content:space-around;overflow-x:auto;
border-right:0!important;
border-top:1px solid rgba(255,255,255,.07)!important;
padding:6px 4px!important}
#rail .lg{display:none}
#rail button{font-size:9px!important;padding:5px 2px!important;
min-width:56px}
#rail button i{width:28px!important;height:28px!important;
font-size:15px!important}
#subbar{padding:9px 12px!important}
#subbar button{font-size:12px;padding:7px 12px}
section,.pg{padding-left:14px!important;
padding-right:14px!important}
.hgrid{grid-template-columns:1fr!important}
.welc{padding:20px 17px!important}
.welc h1{font-size:21px!important}
.hero img{height:190px!important}
table.tf,table.st{display:block;overflow-x:auto;
white-space:nowrap}
.gvbx{padding:16px 14px!important}
.gvgrid{grid-template-columns:1fr!important}
.sbc{flex:0 0 150px!important}}

@media(max-width:900px){
html body{padding-left:0!important;
padding-bottom:82px!important;-webkit-text-size-adjust:100%}
#rail{position:fixed!important;left:0;right:0;bottom:0;
top:auto!important;height:74px!important;width:auto!important;
flex-direction:row!important;justify-content:space-evenly;
align-items:center;padding:4px 2px!important;
overflow-x:auto;overflow-y:hidden;
background:rgba(10,12,15,.97)!important;
backdrop-filter:blur(18px) saturate(1.5);
border-right:0!important;
border-top:1px solid rgba(255,255,255,.09)!important;
box-shadow:0 -8px 30px rgba(0,0,0,.5)}
#rail .lg{display:none!important}
#rail button{flex:1 1 0;min-width:0;font-size:9.5px!important;
gap:3px!important;padding:6px 1px!important}
#rail button i{width:26px!important;height:26px!important;
font-size:14px!important;border-radius:9px!important}
#rail button span{overflow:hidden;text-overflow:ellipsis;
white-space:nowrap;max-width:100%}
#subbar{padding:8px 10px!important;gap:6px!important;
-webkit-overflow-scrolling:touch}
#subbar button{font-size:12.5px!important;
padding:9px 14px!important;flex:0 0 auto}
.scorebar{border-radius:0!important}
.sbc{flex:0 0 138px!important;padding:7px 10px!important}
section,.pg{padding-left:13px!important;
padding-right:13px!important}
.pg h2{font-size:20px!important}
.hgrid{grid-template-columns:1fr!important;gap:18px!important}
.welc{padding:19px 16px!important;border-radius:14px!important}
.welc h1{font-size:20px!important}
.welc p{font-size:13px!important}
.hero img{height:172px!important}
.nrow{padding:10px!important}
.nrow img{width:66px!important;height:44px!important}
.tcgrid{grid-template-columns:1fr!important;gap:14px!important}
.tcin input{font-size:16px!important}
table.tf,table.st{display:block;overflow-x:auto;
white-space:nowrap;-webkit-overflow-scrolling:touch}
.gvbx{padding:15px 13px!important;border-radius:14px!important}
.gvgrid{grid-template-columns:1fr!important}
#cardfr{height:70vh!important}
.dgrid{grid-template-columns:1fr 1fr!important}
}
@media(max-width:430px){
#rail button span{font-size:8.5px!important}
.dgrid{grid-template-columns:1fr!important}
.sbc{flex:0 0 124px!important}}
</style>'''

H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<style id="polishcss">.*?</style>', "", H,
           flags=re.S)

blocks = [mm for mm in
          re.finditer(r'<style id="[\w-]+">', H)]
if blocks:
    last = max(blocks, key=lambda x: x.start())
    j = H.index("</style>", last.start()) + 8
    H = H[:j] + CSS + H[j:]
    where = "after %s" % last.group(0)
else:
    mb = re.search(r"<body[^>]*>", H)
    H = H[:mb.end()] + CSS + H[mb.end():]
    where = "body start"

assert H.count('id="polishcss"') == 1
assert "</script></body></html>" in H, "tail broken"
assert len(H) > n0 * 0.9
open("vaporai.html", "w").write(H)
i1 = H.index('id="nav2css"') if 'id="nav2css"' in H else -1
i2 = H.index('id="shellcss"') if 'id="shellcss"' in H else -1
i3 = H.index('id="polishcss"')
print("injected %s" % where)
print("cascade order: shell@%d nav2@%d polish@%d"
      % (i2, i1, i3))
print("polish last: %s" % (i3 > i2 and i3 > i1))
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
