import re

CSS = """
#scores .wrap{max-width:1060px;margin:0 auto}
#scores .hd{display:flex;align-items:center;gap:12px;
margin:6px 0 16px;flex-wrap:wrap}
#scores .hd h2{margin:0;font-size:26px;letter-spacing:-.6px}
#scores .wk{margin-left:auto;background:#0A1E33;
color:#EAF2F8;border:1px solid #1C4265;border-radius:10px;
padding:8px 14px;font-size:14px;font-weight:600}
#scores .pills{display:flex;gap:3px;background:#0A1E33;
border:1px solid #1C4265;border-radius:99px;padding:3px;
margin-bottom:14px;flex-wrap:wrap}
#scores .pills button{background:none;border:0;
color:#93AFC6;padding:7px 16px;border-radius:99px;
font-size:13px;font-weight:700;cursor:pointer}
#scores .pills button.on{background:#0080C6;color:#fff}
#scores h4.grp{margin:20px 0 4px;font-size:12px;
text-transform:uppercase;letter-spacing:.9px;color:#FFC20E;
font-weight:800;border-bottom:1px solid #1C4265;
padding-bottom:6px}
#scores h4.grp i{float:right;font-style:normal;
color:#6F8CA6;font-weight:600;text-transform:none;
letter-spacing:0;font-size:11px}
#scores .lr{display:grid;
grid-template-columns:34px 42px 1fr auto;gap:11px;
align-items:center;padding:9px 10px;
border-bottom:1px solid #12293F;border-radius:8px;
cursor:pointer}
#scores .lr:hover{background:#0A1E33}
#scores .lr .rk{text-align:center;font-weight:800;
font-size:15px;color:#6F8CA6}
#scores .lr.top1 .rk{color:#FFC20E}
#scores .lr img{width:42px;height:42px;border-radius:50%;
background:#102C47;object-fit:cover}
#scores .lr .nm b{display:block;font-size:15px}
#scores .lr .nm span{font-size:12px;color:#93AFC6}
#scores .lr .pt{text-align:right;font-size:21px;
font-weight:800;letter-spacing:-.5px;
font-variant-numeric:tabular-nums}
#scores .lr .pt em{display:block;font-style:normal;
font-size:10px;color:#6F8CA6;font-weight:600;
letter-spacing:.4px;text-transform:uppercase}
#scores .bk{background:#071A2B;border:1px solid #1C4265;
border-radius:10px;margin:2px 0 10px;padding:10px 14px}
#scores .bk table{width:100%;border-collapse:collapse;
font-size:12px}
#scores .bk td{padding:4px 6px;
border-bottom:1px solid #12293F;
font-variant-numeric:tabular-nums}
#scores .bk td.l{text-align:left}
#scores .bk td.n{text-align:right;color:#93AFC6}
#scores .bk td.p{text-align:right;font-weight:700}
#scores .bk tr.tot td{border:0;border-top:1px solid #1C4265;
font-weight:800;color:#FFC20E;padding-top:7px}
#scores .live{display:inline-block;width:7px;height:7px;
border-radius:50%;background:#4ADE80;margin-right:5px;
animation:kfp 1.6s infinite}
@keyframes kfp{0%,100%{opacity:1}50%{opacity:.25}}
#scores .empty{text-align:center;padding:60px 20px;
color:#93AFC6}
#scores .empty h3{font-size:20px;color:#EAF2F8;margin:0 0 6px}
#scores .st{font-size:11px;color:#6F8CA6;margin-top:14px;
line-height:1.6}
#scores .mut{color:#93AFC6;font-size:12px}
"""

JS = r"""
(function(){
var WK=null,POS="ALL",ROWS=[],TS=null,BUSY=0,OPEN=null;
var PMAP={},TIMER=null,LIVE=0;

function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function n1(v){return (Math.round(v*100)/100).toFixed(2);}

// Same Tuesday rollover fpts.nflweek() uses, computed in
// the browser so the page advances without a rebuild.
function curWeek(){
 var A=Date.UTC(2026,8,8);
 var d=Math.floor((Date.now()-A)/604800000)+1;
 return Math.max(1,Math.min(18,d));
}

function head(pid,pos,tm){
 if(pos==="DEF"||pos==="DST")
  return "https://sleepercdn.com/images/team_logos/nfl/"
   +String(tm||"").toLowerCase()+".png";
 return "https://sleepercdn.com/content/nfl/players/thumb/"
  +pid+".jpg";
}

function load(){
 if(BUSY)return;
 BUSY=1;
 fetch("https://api.sleeper.app/v1/stats/nfl/regular/"
   +"2026/"+WK)
  .then(function(r){return r.json();})
  .then(function(d){
   var out=[];
   Object.keys(d||{}).forEach(function(pid){
    var st=d[pid];
    if(!st)return;
    var p=KFscore.score(st);
    if(Math.abs(p)<0.005)return;
    var m=PMAP[pid]||{};
    var nm=m.n||pid;
    var pos=m.p||"";
    if(/^TEAM_/.test(pid))return;   // team aggregates
    out.push({pid:pid,n:nm,pos:pos,tm:m.t||"",
      pts:p,st:st});
   });
   out.sort(function(a,b){return b.pts-a.pts;});
   ROWS=out;TS=new Date();BUSY=0;draw();
  }).catch(function(e){
   BUSY=0;
   var v=$("scbody");
   if(v)v.innerHTML='<p class="mut">Could not load '
    +'scores: '+esc(e.message)+'</p>';});
}

function breakdown(r){
 var parts=KFscore.explain(r.st);
 if(!parts.length)return "";
 var h='<div class="bk"><table>';
 parts.forEach(function(x){
  h+='<tr><td class="l">'+esc(KFscore.label(x.k))
   +'</td><td class="n">'+x.v+' &times; '+x.w
   +'</td><td class="p">'
   +(x.p>=0?"+":"")+n1(x.p)+'</td></tr>';});
 h+='<tr class="tot"><td class="l">Total</td>'
  +'<td class="n"></td><td class="p">'+n1(r.pts)
  +'</td></tr></table></div>';
 return h;
}

function row(r,i){
 var op=(OPEN===r.pid);
 return '<div class="lr'+(i===0?" top1":"")
  +'" data-sr="'+esc(r.pid)+'">'
  +'<div class="rk">'+(i+1)+'</div>'
  +'<img src="'+esc(head(r.pid,r.pos,r.tm))
  +'" onerror="this.style.visibility=\'hidden\'">'
  +'<div class="nm"><b>'+esc(r.n)+'</b><span>'
  +esc(r.pos||"?")+' &middot; '+esc(r.tm||"")
  +' &middot; '+(op?"hide":"show")+' math</span></div>'
  +'<div class="pt">'+n1(r.pts)+'<em>pts</em></div>'
  +'</div>'+(op?breakdown(r):"");
}

function draw(){
 var v=$("scbody");
 if(!v)return;
 var h='<div class="pills">';
 ["ALL","QB","RB","WR","TE","K","DEF"].forEach(function(p){
  h+='<button data-sp="'+p+'"'+(POS===p?' class="on"':'')
   +'>'+p+'</button>';});
 h+='</div>';

 function grp(ps){
  return ROWS.filter(function(r){
   if(ps==="DEF")return r.pos==="DEF"||r.pos==="DST";
   if(ps==="K")return r.pos==="K"||r.pos==="PK";
   return r.pos===ps;});
 }

 if(!ROWS.length){
  h+='<div class="empty"><h3>Players have yet to play'
   +'</h3><p>Leaders appear here once week '+WK
   +' games begin.</p></div>';
 }else if(POS==="ALL"){
  var cnt={};
  ROWS.forEach(function(r){
   var p=r.pos||"?";
   if(p==="PK")p="K";
   if(p==="DST")p="DEF";
   cnt[p]=(cnt[p]||0)+1;});
  var lbl=["QB","RB","WR","TE","K","DEF"]
   .filter(function(p){return cnt[p];})
   .map(function(p){return cnt[p]+" "+p;}).join(" \u00b7 ");
  h+='<h4 class="grp">All positions<i>'+lbl+'</i></h4>';
  ROWS.slice(0,150).forEach(function(r,i){h+=row(r,i);});
  if(ROWS.length>150)
   h+='<p class="mut" style="padding:8px 10px">Showing '
    +'top 150 of '+ROWS.length+' scorers. Use the '
    +'position filters above to see more of one '
    +'position.</p>';
 }else{
  var g=grp(POS);
  if(!g.length)h+='<p class="mut">No '+POS
   +' scores yet for week '+WK+'.</p>';
  g.slice(0,150).forEach(function(r,i){h+=row(r,i);});
 }

 h+='<p class="st">Scored with <b>your league\u2019s '
  +'exact settings</b> \u2014 every stat multiplied by '
  +'its own rule and summed. Tap any player to see the '
  +'arithmetic. Field goals score by distance (50+ is '
  +'worth '+(KFscore.settings().fgm_50p||0)+') and '
  +'defenses include points-allowed and yards-allowed '
  +'tiers.<br>Refreshes every 5 minutes'
  +(TS?(' &middot; updated '+TS.toLocaleTimeString()):'')
  +'.</p>';
 v.innerHTML=h;

 Array.prototype.forEach.call(
  document.querySelectorAll("[data-sp]"),function(e){
  e.onclick=function(){POS=e.getAttribute("data-sp");
   OPEN=null;draw();};});
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-sr]"),function(e){
  e.onclick=function(){
   var id=e.getAttribute("data-sr");
   OPEN=(OPEN===id)?null:id;draw();};});
}

function boot(){
 var s=$("scores");
 if(!s)return;
 WK=curWeek();
 var h='<div class="wrap"><div class="hd">'
  +'<h2>Game Center</h2><select class="wk" id="scwk">';
 for(var w=1;w<=18;w++)h+='<option value="'+w+'"'
  +(w===WK?' selected':'')+'>Week '+w+'</option>';
 h+='</select></div><div id="scbody" class="mut">'
  +'Loading\u2026</div></div>';
 s.innerHTML=h;
 var sel=$("scwk");
 if(sel)sel.onchange=function(){
  WK=Number(sel.value);ROWS=[];TS=null;OPEN=null;
  $("scbody").innerHTML='<p class="mut">Loading\u2026</p>';
  load();};

 fetch("_pmap.json").then(function(r){return r.json();})
  .then(function(d){PMAP=d||{};})
  .catch(function(){})
  .then(function(){
   KFscore.ready(function(){
    load();
    if(TIMER)clearInterval(TIMER);
    TIMER=setInterval(function(){
     if(!document.hidden)load();},300000);
   });
  });
}

if(document.readyState!=="loading")boot();
else document.addEventListener("DOMContentLoaded",boot);
})();
"""

open("site/_scores.js", "w").write(JS)
print("wrote site/_scores.js (%d KB)" % (len(JS) // 1024))

H = open("vaporai.html").read()
n0 = len(H)

SEC = '<section id="scores"></section>'
BTN = '<button data-t="scores"></button>'
TAG = '<script src="_score.js"></script>' \
      '<script src="_scores.js"></script>'
STY = '<style id="kfsc">' + CSS + '</style>'

H = H.replace(SEC, "").replace(BTN, "")
H = H.replace('<script src="_scores.js"></script>', "")
H = H.replace('<script src="_score.js"></script>', "")
H = re.sub(r'<style id="kfsc">.*?</style>', "", H, flags=re.S)

A = '<button data-ic="\u21c4" data-t="trades">Trades</button>'
assert H.count(A) == 1, "trades anchor"
H = H.replace(A, BTN + A, 1)
B = '<section id="lgodds">'
assert H.count(B) == 1, "lgodds anchor"
H = H.replace(B, SEC + B, 1)
i = H.rfind("<script")
assert i > 0
H = H[:i] + STY + H[i:]
C = "</script></body></html>"
assert H.count(C) == 1, "tail anchor"
H = H.replace(C, "</script>" + TAG + "</body></html>", 1)
assert H.count(C) == 1, "tail anchor destroyed"

nav = len(re.findall(r'<button[^>]*data-t=', H))
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d | nav %d" % (n0, len(H), nav))
