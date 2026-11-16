import re

POSC = {"QB": "#10b981", "RB": "#3b82f6",
        "WR": "#ec4899", "TE": "#f59e0b",
        "K": "#a855f7", "DEF": "#64748b",
        "DST": "#64748b"}

CSS = """
*{box-sizing:border-box}
body{margin:0;padding:0 2px 30px;background:transparent;
color:#EAF2F8;font:14px/1.45 -apple-system,sans-serif}
.wrap{max-width:1240px;margin:0 auto}
.hd{display:flex;align-items:flex-start;gap:26px;
flex-wrap:wrap;margin:6px 0 16px}
.hd h2{margin:0;font-size:26px;letter-spacing:-.6px;
color:#FFC20E}
.hd .tag{color:#93AFC6;font-size:13px;margin-top:2px}
.ctl{display:flex;gap:26px;flex-wrap:wrap;
align-items:flex-end;flex:1}
.fld label{display:block;font-size:12px;color:#93AFC6;
margin-bottom:5px}
.fld select{background:#0A1E33;color:#EAF2F8;
border:1px solid #1C4265;border-radius:9px;
padding:9px 13px;font-size:13px;font-weight:600}
.mode{display:flex;gap:4px;background:#0A1E33;
border:1px solid #1C4265;border-radius:10px;padding:4px}
.mode button{background:none;border:0;color:#93AFC6;
padding:7px 18px;border-radius:7px;font-size:13px;
font-weight:600;cursor:pointer}
.mode button.on{background:#EAF2F8;color:#04121F}
.mode button:disabled{opacity:.4;cursor:not-allowed}
.msg{text-align:center;color:#93AFC6;font-size:14px;
margin:18px 0 10px}
.board{background:#0A1E33;border:1px solid #1C4265;
border-radius:16px;padding:18px;display:grid;
grid-template-columns:1fr 1px 1fr;gap:18px}
@media(max-width:900px){.board{grid-template-columns:1fr}
.divider{display:none}}
.divider{background:#1C4265}
.side h3{margin:0 0 12px;font-size:20px}
.srch{position:relative;margin-bottom:12px}
.srch input{width:100%;padding:12px 38px 12px 16px;
border-radius:12px;border:1px solid #1C4265;
background:#04121F;color:#EAF2F8;font-size:14px}
.srch button{position:absolute;right:10px;top:50%;
transform:translateY(-50%);background:none;border:0;
color:#6F8CA6;font-size:17px;cursor:pointer}
.picked{display:flex;gap:9px;overflow-x:auto;
padding-bottom:6px;min-height:8px;margin-bottom:10px}
.rail{display:flex;gap:9px;overflow-x:auto;
padding-bottom:8px}
.pcard{flex:0 0 118px;border-radius:12px;overflow:hidden;
background:#04121F;border:1px solid #1C4265;
cursor:pointer;position:relative}
.pcard:hover{border-color:#0080C6}
.pcard .ph{height:92px;display:flex;align-items:flex-end;
justify-content:center;overflow:hidden}
.pcard .ph img{width:92px;height:92px;object-fit:cover}
.pcard .ft{padding:7px 8px;background:#04121F}
.pcard .pos{display:inline-block;font-size:10px;
font-weight:800;padding:2px 7px;border-radius:5px;
color:#04121F}
.pcard .nm{font-size:12px;font-weight:600;margin-top:4px;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pcard .vl{position:absolute;top:6px;right:7px;
background:rgba(4,18,31,.86);color:#FFC20E;font-size:11px;
font-weight:800;padding:2px 6px;border-radius:6px}
.pcard.sel{border-color:#FFC20E}
.pcard .rm{position:absolute;top:6px;left:7px;
background:rgba(4,18,31,.86);border:0;color:#F87171;
font-size:13px;line-height:1;padding:2px 6px;
border-radius:6px;cursor:pointer}
.tot{font-size:13px;color:#93AFC6;margin-top:8px}
.tot b{color:#FFC20E;font-size:17px}
.verdict{background:#0A1E33;border:1px solid #1C4265;
border-radius:16px;padding:18px;margin-top:16px}
.verdict h3{margin:0 0 10px;font-size:19px}
.bar{height:12px;border-radius:99px;background:#12293F;
display:flex;overflow:hidden;margin:12px 0 8px}
.bar i{display:block;height:100%}
.legend{display:flex;justify-content:space-between;
font-size:13px;color:#93AFC6}
.legend b{color:#EAF2F8}
table{width:100%;border-collapse:collapse;font-size:12px;
margin-top:14px}
th{color:#93AFC6;font-size:10px;font-weight:700;
text-transform:uppercase;letter-spacing:.5px;padding:7px;
text-align:right;border-bottom:1px solid #1C4265}
th.l{text-align:left}
td{padding:7px;text-align:right;
border-bottom:1px solid #12293F;
font-variant-numeric:tabular-nums}
td.l{text-align:left}
.up{color:#4ADE80;font-weight:700}
.dn{color:#F87171;font-weight:700}
.mut{color:#93AFC6;font-size:12px}
.note{font-size:11px;color:#6F8CA6;margin-top:12px;
line-height:1.65}
"""
print("part 1 ok")

JS = r"""
var TC=null,BD={},SL=null,MYID=1,A=[],B=[];
var POSC={QB:"#10b981",RB:"#38bdf8",WR:"#ec4899",
TE:"#f59e0b",K:"#a855f7",DEF:"#94a3b8",DST:"#94a3b8"};

function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function n1(v){return (v==null||v!==v)?"\u2013":
 (Math.round(v*10)/10).toFixed(1);}
function norm(s){return String(s||"").toLowerCase()
 .replace(/[^a-z ]/g,"").replace(/\s+/g," ").trim().replace(/ (jr|sr|iii|ii|iv|v)$/,"");}
function meta(x){return BD[norm(x.n)]||{};}
function tot(L){var s=0;L.forEach(function(x){
 s+=(x.val||0);});return s;}

var EL={QB:["QB"],RB:["RB"],WR:["WR"],TE:["TE"],K:["K"],
DEF:["DEF","DST"],DST:["DEF","DST"],FLEX:["RB","WR","TE"],
SUPER_FLEX:["QB","RB","WR","TE"]};
function slots(){return ((SL&&SL.slots)||[]).filter(
 function(s){return s!=="BN"&&s!=="IR"&&s!=="TAXI";});}
function projOf(p){
 var b=BD[norm(p.n)];
 return (b&&b.live!=null)?b.live:(p.g||p.ppg||0);}
function myTeam(){
 var o=null;((SL&&SL.teams)||[]).forEach(function(t){
  if(Number(t.id)===Number(MYID))o=t;});return o;}
function bestLine(ps){
 var S=slots(),pool=ps.slice().sort(function(a,b){
  return projOf(b)-projOf(a);});
 var used={},t=0,fx=[];
 S.forEach(function(s){
  if(s.indexOf("FLEX")>=0){fx.push(s);return;}
  for(var j=0;j<pool.length;j++){
   var k=pool[j].pid||pool[j].n;
   if(used[k])continue;
   if((EL[s]||[]).indexOf(pool[j].pos||pool[j].p)>=0){
    used[k]=1;t+=projOf(pool[j]);break;}}});
 fx.forEach(function(s){
  for(var j=0;j<pool.length;j++){
   var k=pool[j].pid||pool[j].n;
   if(used[k])continue;
   if((EL[s]||[]).indexOf(pool[j].pos||pool[j].p)>=0){
    used[k]=1;t+=projOf(pool[j]);break;}}});
 return t;}

function row(x,side,i,pick){
 var m=meta(x),pos=x.p||m.pos||"";
 var c=POSC[pos]||"#94a3b8";
 var rk=m.posrk?(" "+m.posrk):"";
 return '<div class="prow"'
  +(pick?(' data-add="'+side+'" data-n="'+esc(x.n)+'"'):"")
  +'>'
  +(m.img?'<img src="'+esc(m.img)+'">':
    '<div style="width:46px;height:46px"></div>')
  +'<div class="mid"><div class="nm"'
  +(pick?"":' data-kfp="'+esc(x.n)+'"')+'>'+esc(x.n)
  +'</div><div class="badges">'
  +'<span class="pb" style="background:'+c+'">'
  +esc(pos)+rk+'</span>'
  +'<span class="ovr">'+x.val+' OVR</span>'
  +'</div></div>'
  +(pick?"":'<button class="x" data-rm="'+side
    +'" data-i="'+i+'">&times;</button>')
  +'</div>';}

function verdictTxt(){
 var ta=tot(A),tb=tot(B),d=tb-ta;
 if(!A.length||!B.length)
  return ["Please add players to both sides of the trade!",
          50];
 var sum=ta+tb||1;
 var pct=Math.round(100*tb/sum);
 var lbl;
 if(Math.abs(d)/Math.max(sum,1)<0.04)lbl="Even trade";
 else if(d>0)lbl="You win!";
 else lbl="You lose!";
 return [lbl,pct];}

function impact(){
 var me=myTeam();
 if(!me)return null;
 var gk=A.map(function(x){return norm(x.n);});
 var have=(me.players||[]).filter(function(p){
  return gk.indexOf(p.k||norm(p.n))>=0;});
 if(!have.length)return null;
 var before=bestLine(me.players||[]);
 var keep=(me.players||[]).filter(function(p){
  return gk.indexOf(p.k||norm(p.n))<0;});
 var got=B.map(function(x){
  var m=meta(x);
  return {pid:"NEW_"+norm(x.n),n:x.n,
   pos:x.p||m.pos,tm:x.t||m.tm};});
 return {b:before,a:bestLine(keep.concat(got)),
  n:have.length,
  size:[(me.players||[]).length,
        keep.length+got.length]};}

function draw(){
 var v=verdictTxt();
 var h='<div class="wrap"><div class="bar1">'
  +'<div class="fld"><label>League/Team:</label>'
  +'<select id="team"></select></div>'
  +'<div class="fld"><label>Link Platform:</label>'
  +'<select disabled><option>Sleeper (synced)</option>'
  +'</select></div>'
  +'<div class="fld"><label>Mode:</label>'
  +'<div class="mode">'
  +'<button disabled title="We only model '
  +'rest-of-season value">Dynasty</button>'
  +'<button class="on">Redraft</button></div></div>'
  +'</div>';
 h+='<div class="verdict">'+esc(v[0])+'</div>'
  +'<div class="vbar"><i style="left:0;width:'+v[1]
  +'%"></i><u></u></div>';
 h+='<div class="board">';
 [["A","They Receive"],["B","I Receive"]].forEach(
  function(sd,ix){
  var s=sd[0],L=(s==="A")?A:B;
  h+='<div class="side"><div class="hdr"><h3>'+sd[1]
   +'</h3><button class="trash" data-clr="'+s
   +'">&#128465;</button></div>';
  L.forEach(function(x,i){h+=row(x,s,i,false);});
  h+='<div class="srch"><input id="i'+s
   +'" placeholder="Search..."><button class="clr" '
   +'data-cl="'+s+'">&times;</button></div>'
   +'<div class="sug" id="s'+s+'"></div>'
   +'<div class="tot">Total <b>'+tot(L)+'</b></div>'
   +'</div>';
  if(ix===0)h+='<div class="dv"></div>';});
 h+='</div>';

 var im=impact();
 if(im){
  var d=im.a-im.b;
  h+='<div class="detail"><h3>Your starting lineup</h3>'
   +'<table><tbody>'
   +'<tr><td class="l">Before</td><td>'+n1(im.b)
   +'</td></tr><tr><td class="l">After</td><td>'+n1(im.a)
   +'</td></tr><tr><td class="l"><b>Weekly change</b></td>'
   +'<td class="'+(d>=0?"up":"dn")+'">'+(d>=0?"+":"")
   +n1(d)+'</td></tr>'
   +'<tr><td class="l">Roster size</td><td>'+im.size[0]
   +' &rarr; '+im.size[1]+'</td></tr></tbody></table>'
   +'<p class="note">Your best legal lineup before and '
   +'after. Value sums flatter whichever side receives '
   +'more players; this counts only what you can start. '
   +'Our per-player error is about 5 points a week, so '
   +'a change smaller than that is not a real edge.</p>'
   +'</div>';
 }
 h+='<p class="note">OVR is rest-of-season points above '
  +'a replacement-level player at that position, times '
  +'weeks remaining, scaled to 10,000. Replacement is '
  +'measured by filling every starting slot in your '
  +'league. Kickers and defenses are discounted because '
  +'you can stream them weekly. Values move each week as '
  +'production and injuries change the projections.</p>'
  +'</div>';
 $("v").innerHTML=h;
 wire();
 try{parent.postMessage(
  {kfh:document.body.scrollHeight+24},"*");}catch(e){}}

function sug(s){
 var inp=$("i"+s),box=$("s"+s);
 var q=norm(inp.value);
 if(!q){box.innerHTML="";return;}
 var hits=TC.filter(function(x){
  return norm(x.n).indexOf(q)>=0;}).slice(0,10);
 box.innerHTML=hits.map(function(x){
  return row(x,s,0,true);}).join("");
 Array.prototype.forEach.call(
  box.querySelectorAll("[data-add]"),function(e){
  e.onclick=function(){
   var nm=e.getAttribute("data-n"),f=null;
   TC.forEach(function(x){if(x.n===nm)f=x;});
   if(!f)return;
   (s==="A"?A:B).push(f);
   inp.value="";box.innerHTML="";draw();};});}

function wire(){
 ["A","B"].forEach(function(s){
  var e=$("i"+s);
  if(e)e.oninput=function(){sug(s);};});
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-rm]"),function(e){
  e.onclick=function(){
   var s=e.getAttribute("data-rm");
   (s==="A"?A:B).splice(
    Number(e.getAttribute("data-i")),1);draw();};});
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-clr]"),function(e){
  e.onclick=function(){
   if(e.getAttribute("data-clr")==="A")A=[];else B=[];
   draw();};});
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-cl]"),function(e){
  e.onclick=function(){
   var s=e.getAttribute("data-cl");
   $("i"+s).value="";$("s"+s).innerHTML="";};});
 var t=$("team");
 if(t&&SL&&SL.teams){
  t.innerHTML=SL.teams.map(function(x){
   return '<option value="'+x.id+'"'
    +(Number(x.id)===Number(MYID)?" selected":"")+'>'
    +esc(x.owner||("Team "+x.id))+'</option>';}).join("");
  t.onchange=function(){
   MYID=Number(t.value);
   try{localStorage.setItem("kf_myteam",t.value);}
   catch(e){}
   draw();};}}

function boot(){
 try{var m=localStorage.getItem("kf_myteam");
  if(m)MYID=Number(m);}catch(e){}
 Promise.all([
  fetch("_tc.json").then(function(r){return r.json();}),
  fetch("_board.json").then(function(r){return r.json();}),
  fetch("_slteams.json").then(function(r){return r.json();})
   .catch(function(){return {teams:[],slots:[]};})
 ]).then(function(a){
  TC=a[0];SL=a[2];
  (a[1].rows||[]).forEach(function(r){
   BD[norm(r.n)]=r;});
  draw();
 }).catch(function(e){
  $("v").innerHTML='<p class="mut">Could not load: '
   +esc(e.message)+'</p>';});}
boot();
"""

HTML = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,'
        'initial-scale=1"><style>__CSS__</style></head>'
        '<body><div id="v" class="mut">Loading\u2026</div>'
        '<script src="_card.js"></script>'
        '<script>__JS__</script></body></html>')
HTML = HTML.replace("__CSS__", CSS).replace("__JS__", JS)
open("site/tradecalc.html", "w").write(HTML)
print("wrote site/tradecalc.html (%d KB)" % (len(HTML) // 1024))

STY = 'width:100%;height:1250px;border:0;background:transparent'
IFR = ('<iframe data-src="tradecalc.html" style="%s">'
       '</iframe>' % STY)
H = open("vaporai.html").read()

# The legacy inline drawTrades() renders an NFL
# player-movement table into #trades at runtime,
# clobbering our iframe after the page loads.
CALL = 'safe(drawTrades,"trades");\n'
if CALL in H:
    H = H.replace(CALL, "", 1)
    print("removed legacy safe(drawTrades) call")
else:
    print("legacy drawTrades call already gone")

for sid in ("tcalc", "trades"):
    H = re.sub(r'<section id="%s">.*?</section>' % sid,
               '<section id="%s">%s</section>' % (sid, IFR),
               H, count=1, flags=re.S)
assert H.count('data-src="tradecalc.html"') == 2
assert H.count("</script></body></html>") == 1
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav %d" % nav
open("vaporai.html", "w").write(H)
print("tcalc + trades -> tradecalc.html | nav %d" % nav)
