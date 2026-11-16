import re

JS = r'''(function(){
var API="https://site.api.espn.com/apis/site/v2/sports/"
 +"football/nfl/scoreboard?dates=";
var E2N={"LAR":"LA","WSH":"WAS","JAC":"JAX","AZ":"ARI"};
function nz(a){a=(a||"").toUpperCase();return E2N[a]||a;}
function ymd(d){return d.getFullYear()
 +("0"+(d.getMonth()+1)).slice(-2)
 +("0"+d.getDate()).slice(-2);}
function fmt(iso){
 var d=new Date(iso);
 if(isNaN(d))return null;
 return d.toLocaleDateString(undefined,{weekday:"short",
  month:"short",day:"numeric"})+" \u00b7 "
  +d.toLocaleTimeString(undefined,{hour:"numeric",
  minute:"2-digit"});}
function pull(){
 var a=new Date(),b=new Date();
 b.setDate(b.getDate()+16);
 return fetch(API+ymd(a)+"-"+ymd(b))
  .then(function(r){return r.json();});}
function apply(sb){
 var M={},live=0;
 (sb.events||[]).forEach(function(e){
  var c=(e.competitions||[])[0];
  if(!c)return;
  var cp=c.competitors||[],o={};
  cp.forEach(function(x){
   o[nz((x.team||{}).abbreviation)]=x.score;});
  var k=Object.keys(o).sort().join("@");
  var st=(e.status||{}).type||{};
  M[k]={sc:o,state:st.state,det:st.shortDetail,
   date:e.date};
  if(st.state==="in")live++;});
 var n=0;
 Array.prototype.forEach.call(
  document.querySelectorAll(".sbc"),function(cd){
  var im=cd.querySelectorAll(".sbrow img");
  if(im.length<2)return;
  var A=nz(im[0].getAttribute("alt"));
  var H=nz(im[1].getAttribute("alt"));
  var g=M[[A,H].sort().join("@")];
  if(!g)return;
  var vv=cd.querySelectorAll(".sbrow span.vv");
  var me=cd.querySelector(".sbmeta");
  var wk=me?(me.textContent.match(/Week\s*\d+/i)
   ||[""])[0]:"";
  if(me&&!me.getAttribute("data-m0")){
   me.setAttribute("data-m0",me.textContent);}
  if(g.state==="pre"){
   var f=fmt(g.date);
   if(me&&f)me.textContent=(wk?wk+" \u00b7 ":"")+f;
  }else{
   var sa=g.sc[A],sh=g.sc[H];
   if(vv.length>=2&&sa!=null&&sh!=null){
    vv[0].textContent=sa;
    vv[1].textContent=sh;
    var ia=parseInt(sa,10),ih=parseInt(sh,10);
    vv[0].className="vv"+(ia>ih?" win":"");
    vv[1].className="vv"+(ih>ia?" win":"");}
   if(me){var d0=me.getAttribute("data-m0")||"";
    var dt=fmt(g.date)||d0.replace(/^Week\s*\d+\s*.\s*/i,"");
    me.textContent=(wk?wk+" \u00b7 ":"")+dt
     +" \u00b7 "+(g.det||"").toUpperCase();}
   cd.className="sbc"+(g.state==="in"?" livegame":"");}
  n++;});
 return {n:n,live:live};}
function tick(){
 if(document.hidden){setTimeout(tick,30000);return;}
 pull().then(function(sb){
  var r=apply(sb);
  console.log("scorebar: "+r.n+" games, "+r.live+" live");
  setTimeout(tick,30000);})
 .catch(function(e){
  console.log("scorebar update failed: "+e.message);
  setTimeout(tick,120000);});}
function boot(){
 if(!document.querySelectorAll(".sbc").length){
  setTimeout(boot,400);return;}
 tick();}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",boot);}
else{setTimeout(boot,300);}})();'''
open("site/_live.js", "w").write(JS)
print("wrote site/_live.js (%d bytes)" % len(JS))

OLD = '<script src="_time.js"></script>'
TAG = '<script src="_live.js"></script>'
H = open("vaporai.html").read()
n0 = len(H)
H = H.replace(OLD, "").replace(TAG, "")
H = H.replace("</script></body></html>",
              "</script>" + TAG + "</body></html>", 1)
assert H.count(TAG) == 1 and OLD not in H
assert "</script></body></html>" in H, "tail broken"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav changed: %d" % nav
open("vaporai.html", "w").write(H)
print("_time.js replaced by _live.js | %d -> %d"
      % (n0, len(H)))
