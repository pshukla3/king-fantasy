import re

JS = r'''(function(){
var D=null,POS="ALL",Q="",SORT="live",DIR=-1;
function esc(x){return String(x==null?"":x)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;");}
function rows(){
 var z=(D.rows||[]).filter(function(r){
  if(POS!=="ALL"&&r.pos!==POS)return false;
  if(Q&&r.n.toLowerCase().indexOf(Q)<0)return false;
  return true;});
 z.sort(function(a,b){
  var x=a[SORT],y=b[SORT];
  if(typeof x==="string")return DIR*x.localeCompare(y);
  return DIR*((x||0)-(y||0));});
 return z;}
function draw(){
 var h=document.getElementById("rklive");
 if(!h){
  var sec=document.getElementById("rank");
  if(!sec)return;
  h=document.createElement("div");h.id="rklive";
  sec.insertBefore(h,sec.firstChild);}
 if(!D){h.innerHTML="";return;}
 var P=["ALL","QB","RB","WR","TE","K","DST"];
 var z=rows();
 var s='<h2>Rankings</h2><p class="sub">Updated through '
  +'week '+D.week+'. Each projection is pulled '
  +Math.round(D.lam*100)+'% toward observed production '
  +'per game played, a weight measured by walk-forward '
  +'validation (out-of-sample MAE 1.121 &rarr; 1.047). '
  +'Base is the preseason model; Updated is what the '
  +'board says now.</p>'
  +'<div class="rkbar">'
  +P.map(function(p){return '<button data-p="'+p+'" class="'
   +(p===POS?"on":"")+'">'+p+'</button>';}).join("")
  +'<input id="rkq" placeholder="search player" value="'
  +esc(Q)+'"></div>'
  +'<div class="rkn">'+z.length+' players</div>'
  +'<table class="rktab"><thead><tr>'
  +'<th>#</th><th data-s="n">Player</th>'
  +'<th data-s="pos">Pos</th>'
  +'<th class="n" data-s="base">Base</th>'
  +'<th class="n" data-s="live">Updated</th>'
  +'<th class="n" data-s="move">&Delta;</th>'
  +'<th class="n" data-s="snap">Snap</th>'
  +'<th>Status</th></tr></thead><tbody>';
 z.forEach(function(r,i){
  var mv=r.move||0;
  var cls=mv>0.05?"up":(mv<-0.05?"dn":"");
  s+='<tr><td class="rkr">'+(i+1)+'</td>'
   +'<td class="rkn2">'+esc(r.n)+'</td>'
   +'<td class="pos">'+esc(r.pos)+' '+esc(r.tm)+'</td>'
   +'<td class="n">'+r.base.toFixed(2)+'</td>'
   +'<td class="n"><b>'+r.live.toFixed(2)+'</b></td>'
   +'<td class="n '+cls+'">'
   +(mv>0?"+":"")+mv.toFixed(2)+'</td>'
   +'<td class="n">'+(r.snap==null?"-":
     (Math.round(r.snap*100)+"%"))+'</td>'
   +'<td class="inj">'+esc(r.inj||"")+'</td></tr>';});
 h.innerHTML=s+'</tbody></table>';
 Array.prototype.forEach.call(
  h.querySelectorAll(".rkbar button"),function(b){
  b.onclick=function(){POS=b.getAttribute("data-p");
   draw();};});
 var q=document.getElementById("rkq");
 if(q){q.oninput=function(){Q=q.value.toLowerCase();
  draw();var e=document.getElementById("rkq");
  if(e){e.focus();e.setSelectionRange(e.value.length,
   e.value.length);}};}
 Array.prototype.forEach.call(
  h.querySelectorAll("th[data-s]"),function(t){
  t.style.cursor="pointer";
  t.onclick=function(){
   var k=t.getAttribute("data-s");
   if(SORT===k)DIR=-DIR;else{SORT=k;DIR=-1;}
   draw();};});}
function boot(){
 fetch("_ranklive.json").then(function(r){
  return r.json();}).then(function(d){D=d;draw();})
 .catch(function(e){
  console.log("ranklive: "+e.message);});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",
  function(){setTimeout(boot,600);});}
else{setTimeout(boot,600);}})();'''
open("site/_ranklive.js", "w").write(JS)
print("wrote site/_ranklive.js (%d bytes)" % len(JS))

TAG = '<script src="_ranklive.js"></script>'
H = open("vaporai.html").read()
n0 = len(H)
H = H.replace(TAG, "")
assert H.count("</script></body></html>") == 1
H = H.replace("</script></body></html>",
              "</script>" + TAG + "</body></html>", 1)
assert H.count(TAG) == 1
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav changed: %d" % nav
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d | nav %d" % (n0, len(H), nav))
