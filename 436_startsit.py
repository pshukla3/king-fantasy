import re

CSS = """
*{box-sizing:border-box}
body{margin:0;padding:0 2px 30px;background:transparent;
color:#EAF2F8;font:14px/1.45 -apple-system,sans-serif}
.wrap{max-width:1180px;margin:0 auto}
.top{display:flex;align-items:center;gap:10px;
margin:8px 0 14px;flex-wrap:wrap}
.top h2{margin:0;font-size:22px;letter-spacing:-.5px}
.seg{display:flex;gap:3px;background:#0A1E33;
border:1px solid #1C4265;border-radius:99px;padding:3px}
.seg button{background:none;border:0;color:#93AFC6;
padding:6px 14px;border-radius:99px;font-size:12px;
font-weight:700;cursor:pointer}
.seg button.on{background:#0080C6;color:#fff}
.clr{margin-left:auto;background:#0A1E33;
border:1px solid #1C4265;color:#93AFC6;border-radius:8px;
padding:6px 12px;font-size:12px;cursor:pointer}
.cols{display:grid;grid-template-columns:320px 1fr;gap:14px}
@media(max-width:820px){.cols{grid-template-columns:1fr}}
.pane{background:#0A1E33;border:1px solid #1C4265;
border-radius:14px;padding:12px}
input.s{width:100%;padding:10px 13px;border-radius:10px;
border:1px solid #1C4265;background:#102C47;color:#EAF2F8;
font-size:14px;margin-bottom:8px}
.lst{max-height:560px;overflow:auto}
.pc{display:flex;align-items:center;gap:10px;padding:8px;
border:1px solid transparent;border-radius:10px;
cursor:pointer}
.pc:hover{border-color:#1C4265;background:#102C47}
.pc.on{border-color:#FFC20E;background:#12314B}
.pc img{width:42px;height:42px;border-radius:9px;
background:#102C47;object-fit:cover;flex:none}
.pc b{display:block;font-size:14px}
.tags{display:flex;gap:5px;margin-top:3px}
.tg{font-size:10px;font-weight:800;padding:2px 7px;
border-radius:6px;background:#1C4265;color:#BFD6E8}
.tg.pos{background:#0080C6;color:#fff}
.empty{border:2px dashed #1C4265;border-radius:14px;
padding:60px 20px;text-align:center;color:#93AFC6}
.empty b{display:block;font-size:18px;color:#EAF2F8;
margin-bottom:6px}
.hdr{display:grid;gap:10px}
.ph{background:#102C47;border:1px solid #1C4265;
border-radius:12px;padding:12px;text-align:center;
position:relative}
.ph.best{border-color:#FFC20E}
.ph img{width:60px;height:60px;border-radius:50%;
background:#0A1E33;object-fit:cover}
.ph b{display:block;font-size:15px;margin-top:6px;
cursor:pointer}
.ph span{font-size:11px;color:#93AFC6}
.ph .x{position:absolute;top:6px;right:8px;background:none;
border:0;color:#6F8CA6;cursor:pointer;font-size:15px}
.verdict{position:absolute;top:-9px;left:50%;
transform:translateX(-50%);font-size:9px;font-weight:800;
letter-spacing:.6px;padding:2px 10px;border-radius:99px;
background:#1C4265;color:#93AFC6}
.ph.best .verdict{background:#FFC20E;color:#04121F}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:#93AFC6;font-size:10px;font-weight:700;
text-transform:uppercase;letter-spacing:.5px;padding:8px;
text-align:center;border-bottom:1px solid #1C4265}
th.l{text-align:left}
td{padding:8px;text-align:center;
border-bottom:1px solid #12293F;
font-variant-numeric:tabular-nums}
td.l{text-align:left;color:#93AFC6}
td.hi{color:#4ADE80;font-weight:700}
.mut{color:#93AFC6;font-size:12px}
.note{font-size:11px;color:#6F8CA6;margin-top:12px;
line-height:1.6}
"""
print("part 1 ok")

JS = r"""
var BD=null,SL=null,HIST=null,DR=null,RS=null;
var PICK=[],SRC="mine",Q="",MODE="avg",MYID=1;

function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function n1(v){return (v==null||v!==v)?"\u2013":
 (Math.round(v*10)/10).toFixed(1);}
function norm(s){return String(s||"").toLowerCase()
 .replace(/[^a-z ]/g,"").replace(/\s+/g," ").trim().replace(/ (jr|sr|iii|ii|iv|v)$/,"");}

var BM={},BDST={};
function index(){
 (BD.rows||[]).forEach(function(r){
  var p=String(r.pos||"");
  if(p==="DEF"||p==="DST")BDST[String(r.tm||"")]=r;
  else BM[norm(r.n)]=r;});
}
function myRoster(){
 var me=null;
 (SL.teams||[]).forEach(function(t){
  if(Number(t.id)===Number(MYID))me=t;});
 if(!me)return [];
 var out=[];
 (me.players||[]).forEach(function(p){
  var b=(p.pos==="DEF"||p.pos==="DST")
   ?BDST[p.tm]:BM[p.k||norm(p.n)];
  if(b)out.push(b);});
 return out;
}
function pool(){
 var a=(SRC==="mine")?myRoster():(BD.rows||[]);
 if(Q)a=a.filter(function(r){
  return norm(r.n).indexOf(Q)>=0;});
 return a.slice().sort(function(x,y){
  return (x.rk||9999)-(y.rk||9999);});
}
function lazy(){
 var jobs=[];
 if(!HIST)jobs.push(fetch("_hist.json")
  .then(function(r){return r.json();})
  .then(function(d){HIST=d;}).catch(function(){HIST={};}));
 if(!DR)jobs.push(fetch("_dr.json")
  .then(function(r){return r.json();})
  .then(function(d){DR={};
   d.forEach(function(r){DR[norm(r.n)]=r;});})
  .catch(function(){DR={};}));
 if(!RS)jobs.push(fetch("_reasons.json")
  .then(function(r){return r.json();})
  .then(function(d){RS=d;}).catch(function(){RS={};}));
 return Promise.all(jobs);
}
function hist(r){
 var a=(HIST&&r.pid&&HIST[r.pid])||[];
 var g=a.length,tot=0;
 a.forEach(function(x){tot+=x.p;});
 return {g:g,tot:tot,avg:g?tot/g:null};
}
function rowOf(label,vals,fmt,hiBig){
 var nums=vals.map(function(v){
  return (typeof v==="number"&&v===v)?v:null;});
 var best=null;
 nums.forEach(function(v){
  if(v==null)return;
  if(best==null)best=v;
  else best=hiBig?Math.max(best,v):Math.min(best,v);});
 var h='<tr><td class="l">'+esc(label)+'</td>';
 vals.forEach(function(v,i){
  var isBest=(nums[i]!=null&&best!=null
   &&Math.abs(nums[i]-best)<1e-9&&vals.length>1);
  h+='<td'+(isBest?' class="hi"':'')+'>'
   +(fmt?fmt(v):(v==null?"\u2013":v))+'</td>';});
 return h+'</tr>';
}
function find(nm){
 var out=null;
 (BD.rows||[]).forEach(function(r){
  if(r.n===nm)out=r;});
 return out;
}
function kfCur(){var A=Date.UTC(2026,8,8);
 return Math.max(1,Math.min(18,
  Math.floor((Date.now()-A)/604800000)+1));}
function wkE(r){var w=(r&&r.wk)||[],c=kfCur();
 for(var i=0;i<w.length;i++)
  if(Number(w[i].w)===c)return w[i];
 return w[0]||null;}
function wkP(r){var e=wkE(r);
 if(!e)return (r.live==null?null:r.live);
 if(e.o==="BYE"||e.out)return 0;
 return (e.m==null?(r.live==null?null:r.live):e.m);}
function wkO(r){var e=wkE(r);
 if(!e)return "-";
 if(e.o==="BYE")return "BYE";
 return (e.h?"vs ":"@ ")+e.o;}
function wkS(r){var e=wkE(r);
 if(e&&e.o==="BYE")return "BYE - cannot start";
 if(e&&e.out)return "OUT - cannot start";
 return r.inj||"Active";}
function compare(){
 if(!PICK.length)
  return '<div class="empty"><b>Add a player to start'
   +'</b>Pick a player from the list, then add another '
   +'to compare them.</div>';
 var best=null,bv=-1e9;
 PICK.forEach(function(r){
  var v=wkP(r);
  if(v!=null&&v>bv){bv=v;best=r;}});
 var h='<div class="hdr" style="grid-template-columns:'
  +'repeat('+PICK.length+',1fr)">';
 PICK.forEach(function(r){
  var win=(PICK.length>1&&best&&r===best);
  h+='<div class="ph'+(win?" best":"")+'">'
   +(PICK.length>1?'<span class="verdict">'
     +(win?"START":"SIT")+'</span>':'')
   +'<button class="x" data-rm="'+esc(r.n)+'">&times;'
   +'</button>'
   +(r.img?'<img src="'+esc(r.img)+'">':'')
   +'<b data-kfp="'+esc(r.n)+'">'+esc(r.n)+'</b>'
   +'<span>'+esc(r.pos||"")+(r.posrk||"")
   +' \u00b7 '+esc(r.tm||"")+'</span></div>';});
 h+='</div><div class="pane" style="margin-top:10px">'
  +'<table><thead><tr><th class="l">Stat</th>';
 PICK.forEach(function(r){
  h+='<th>'+esc(String(r.n).split(" ").slice(-1)[0])
   +'</th>';});
 h+='</tr></thead><tbody>';
 h+=rowOf("Projected this week",
   PICK.map(wkP),n1,true);
 h+=rowOf("Opponent",
   PICK.map(wkO),function(v){return esc(String(v));},false);
 h+=rowOf("Season ppg",
   PICK.map(function(r){return r.live;}),n1,true);
 h+=rowOf("Floor",
   PICK.map(function(r){return r.floor;}),n1,true);
 h+=rowOf("Ceiling",
   PICK.map(function(r){return r.ceil;}),n1,true);
 h+=rowOf("Overall rank",
   PICK.map(function(r){return r.rk;}),
   function(v){return v==null?"\u2013":"#"+v;},false);
 h+=rowOf("Position rank",
   PICK.map(function(r){return r.posrk;}),null,false);
 h+=rowOf("Tier",
   PICK.map(function(r){return r.tier;}),null,false);
 h+=rowOf("Bust risk",
   PICK.map(function(r){
    return r.risk==null?null:r.risk*100;}),
   function(v){return v==null?"\u2013":
    (Math.round(v)+"%");},false);
 var hs=PICK.map(hist);
 h+=rowOf("Games played",
   hs.map(function(x){return x.g;}),null,true);
 h+=rowOf(MODE==="avg"?"Points per game":"Total points",
   hs.map(function(x){
    return MODE==="avg"?x.avg:x.tot;}),n1,true);

 if(RS){
  h+=rowOf("Snap share",
    PICK.map(function(r){
     var x=RS[norm(r.n)];
     return (x&&x.snap!=null)?x.snap*100:null;}),
    function(v){return v==null?"\u2013":
     (Math.round(v)+"%");},true);
 }
 h+=rowOf("Bye week",
   PICK.map(function(r){return r.bye||null;}),null,false);
 h+=rowOf("Status",
   PICK.map(wkS),
   function(v){return esc(String(v));},false);
 h+='</tbody></table>';
 if(PICK.length>1&&best){
  var oth=PICK.filter(function(r){return r!==best;});
  var gap=wkP(best)-Math.max.apply(null,
   oth.map(function(r){
    var v=wkP(r);return v==null?-99:v;}));
  var safe=PICK.slice().sort(function(a,b){
   return (b.floor||0)-(a.floor||0);})[0];
  var up=PICK.slice().sort(function(a,b){
   return (b.ceil||0)-(a.ceil||0);})[0];
  h+='<p class="note"><b>'+esc(best.n)+'</b> projects '
   +n1(gap)+' higher than the next option'
   +(gap<1.5?' \u2014 close enough that this is nearly '
     +'a coin flip':'')+'. ';
  if(safe!==best)h+='<b>'+esc(safe.n)+'</b> has the '
   +'higher floor ('+n1(safe.floor)+'), better if you '
   +'are favoured and just need a safe week. ';
  if(up!==best)h+='<b>'+esc(up.n)+'</b> has the higher '
   +'ceiling ('+n1(up.ceil)+') if you need a big score.';
  h+='</p>';
 }
 h+='<p class="note">Green marks the better value per '
  +'row. Floor and ceiling are 10th and 90th percentile '
  +'outcomes, not guarantees.</p></div>';
 return h;
}
function draw(){
 var a=pool();
 var h='<div class="wrap"><div class="top">'
  +'<h2>Start / Sit</h2><div class="seg">'
  +'<button data-src="mine"'+(SRC==="mine"?' class="on"':'')
  +'>My roster</button>'
  +'<button data-src="all"'+(SRC==="all"?' class="on"':'')
  +'>All players</button></div><div class="seg">'
  +'<button data-mode="avg"'+(MODE==="avg"?' class="on"':'')
  +'>Average</button>'
  +'<button data-mode="tot"'+(MODE==="tot"?' class="on"':'')
  +'>Total</button></div>'
  +(PICK.length?'<button class="clr" id="clr">Clear '
   +PICK.length+'</button>':'')
  +'</div><div class="cols"><div class="pane">'
  +'<input class="s" id="q" placeholder="Search players'
  +'\u2026" value="'+esc(Q)+'"><div class="lst">';
 if(!a.length)h+='<p class="mut">No players match.</p>';
 a.slice(0,200).forEach(function(r){
  var on=PICK.indexOf(r)>=0;
  h+='<div class="pc'+(on?" on":"")+'" data-add="'
   +esc(r.n)+'">'
   +(r.img?'<img src="'+esc(r.img)+'">':
     '<div style="width:42px;height:42px"></div>')
   +'<div><b>'+esc(r.n)+'</b><div class="tags">'
   +'<span class="tg pos">'+esc(r.pos||"")+(r.posrk||"")
   +'</span><span class="tg">'+esc(r.tm||"FA")
   +'</span></div></div></div>';});
 h+='</div></div><div>'+compare()+'</div></div></div>';
 $("v").innerHTML=h;
 wire();
 try{parent.postMessage(
  {kfh:document.body.scrollHeight+24},"*");}catch(e){}
}
function wire(){
 var q=$("q");
 if(q)q.oninput=function(){
  Q=norm(q.value);draw();
  var e=$("q");if(e){e.focus();
   e.setSelectionRange(e.value.length,e.value.length);}};
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-src]"),function(e){
  e.onclick=function(){SRC=e.getAttribute("data-src");
   draw();};});
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-mode]"),function(e){
  e.onclick=function(){MODE=e.getAttribute("data-mode");
   draw();};});
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-add]"),function(e){
  e.onclick=function(){
   var r=find(e.getAttribute("data-add"));
   if(!r)return;
   var i=PICK.indexOf(r);
   if(i>=0)PICK.splice(i,1);
   else if(PICK.length<4)PICK.push(r);
   lazy().then(draw);};});
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-rm]"),function(e){
  e.onclick=function(ev){
   ev.stopPropagation();
   var r=find(e.getAttribute("data-rm"));
   var i=PICK.indexOf(r);
   if(i>=0)PICK.splice(i,1);
   draw();};});
 var c=$("clr");
 if(c)c.onclick=function(){PICK=[];draw();};
}
function boot(){
 try{var m=localStorage.getItem("kf_myteam");
  if(m)MYID=Number(m);}catch(e){}
 Promise.all([
  fetch("_board.json").then(function(r){return r.json();}),
  fetch("_slteams.json").then(function(r){return r.json();})
   .catch(function(){return {teams:[]};})
 ]).then(function(a){
  BD=a[0];SL=a[1];index();
  if(!myRoster().length)SRC="all";
  draw();
 }).catch(function(e){
  $("v").innerHTML='<p class="mut">Could not load: '
   +esc(e.message)+'</p>';});
}
boot();
"""

HTML = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,'
        'initial-scale=1"><style>__CSS__</style></head>'
        '<body><div id="v" class="mut">Loading\u2026</div>'
        '<script src="_card.js"></script>'
        '<script>__JS__</script></body></html>')
HTML = HTML.replace("__CSS__", CSS).replace("__JS__", JS)
open("site/startsit.html", "w").write(HTML)
print("wrote site/startsit.html (%d KB)" % (len(HTML) // 1024))

STY = 'width:100%;height:1400px;border:0;background:transparent'
SEC = ('<section id="tstart"><iframe data-src="startsit.html"'
       ' style="%s"></iframe></section>' % STY)
H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<section id="tstart">.*?</section>', SEC, H,
           count=1, flags=re.S)
assert H.count('<section id="tstart">') == 1
assert 'data-src="startsit.html"' in H, "iframe missing"
assert H.count("</script></body></html>") == 1, "tail"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav %d" % nav
open("vaporai.html", "w").write(H)
print("tstart -> startsit.html | %d -> %d | nav %d"
      % (n0, len(H), nav))
