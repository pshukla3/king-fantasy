import json, re
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()]
PCOL = "position" if "position" in B.columns else None
TCOL = ("recent_team" if "recent_team" in B.columns
        else ("team" if "team" in B.columns else None))
print("position col: %s | team col: %s" % (PCOL, TCOL))

POS = {}
for _, r in B.iterrows():
    k = norm(r["player_display_name"])
    if not k:
        continue
    POS[k] = {
        "n": str(r["player_display_name"]).strip(),
        "p": (str(r[PCOL]).strip() if PCOL
              and pd.notna(r[PCOL]) else ""),
        "t": (str(r[TCOL]).strip() if TCOL
              and pd.notna(r[TCOL]) else ""),
    }
json.dump(POS, open("site/_pos.json", "w"))
print("wrote site/_pos.json (%d players)" % len(POS))
from collections import Counter
print(Counter(v["p"] for v in POS.values()).most_common(8))

JS = r'''(function(){
var API="https://site.api.espn.com/apis/site/v2/"
 +"sports/football/nfl/";
var ANCH=Date.UTC(2026,8,8);
function wk(){var d=Math.floor((Date.now()-ANCH)/864e5);
 return d<0?1:Math.min(18,Math.floor(d/7)+1);}
var P={passingYards:0.04,passingTouchdowns:4,
 interceptions:-2,rushingYards:0.1,rushingTouchdowns:6,
 receptions:1,receivingYards:0.1,
 receivingTouchdowns:6,fumblesLost:-2};
var C={passing:1,rushing:1,receiving:1,fumbles:1};
var CACHE={},EVS=[],POS=null;
function J(u){return fetch(u).then(function(r){
 if(!r.ok)throw new Error(r.status);return r.json();});}
function nm2(s){return String(s||"").toLowerCase()
 .replace(/\s+(jr|sr|ii|iii|iv)\.?$/,"")
 .replace(/[.'`\u2019\-]/g,"")
 .replace(/\s+/g," ").trim();}
function esc(x){return String(x==null?"":x)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;");}
function sc(sm,st,out){
 (((sm||{}).boxscore||{}).players||[]).forEach(
 function(x){
  var ab=((x.team||{}).abbreviation||"");
  (x.statistics||[]).forEach(function(c){
   var cn=String(c.name||"").toLowerCase();
   var ks=c.keys||[];
   if(!C[cn]&&cn!=="kicking")return;
   (c.athletes||[]).forEach(function(a){
    var at=a.athlete||{},n=at.displayName;
    if(!n)return;
    var k=nm2(n);
    var r=out[k]||(out[k]={p:0,st:st,nm:n,tm:ab});
    r.st=st;
    var ss=a.stats||[],i;
    for(i=0;i<ks.length;i++){
     var kk=ks[i],v=parseFloat(ss[i]);
     if(isNaN(v))continue;
     if(cn==="kicking"){
      if(kk==="totalKickingPoints")r.p+=v;}
     else if(P[kk]!==undefined)r.p+=v*P[kk];}});});});}
function rows(){
 var out={};
 EVS.forEach(function(e){
  if(CACHE[e.id])sc(CACHE[e.id],e.state,out);});
 var z=[],k;
 for(k in out){
  var r=out[k];
  if(Math.abs(r.p)<0.05)continue;
  var m=POS&&POS[k];
  var ps=(m&&m.p)||"";
  if(ps==="FB")ps="RB";
  if(ps==="PK")ps="K";
  z.push({n:r.nm,t:r.tm,p:r.p,s:r.st,ps:ps});}
 z.sort(function(a,b){return b.p-a.p;});
 return z;}
function tbl(z,ttl){
 if(!z.length)return"";
 var o='<div class="lbcol"><h5>'+esc(ttl)+'</h5>';
 z.forEach(function(x,i){
  o+='<div class="lbrow"><i>'+(i+1)+'</i>'
   +'<b>'+esc(x.n)+'</b>'
   +'<u>'+esc(x.ps||"")+' '+esc(x.t)+'</u>'
   +'<span class="'+(x.s==="post"?"fin":"liv")+'">'
   +x.p.toFixed(1)+'</span></div>';});
 return o+'</div>';}
function draw(){
 var host=document.getElementById("kflb");
 if(!host){
  var hm=document.getElementById("home");
  if(!hm)return;
  host=document.createElement("div");
  host.id="kflb";hm.appendChild(host);}
 var z=rows();
 if(!z.length){host.innerHTML="";return;}
 var lv=EVS.filter(function(e){
  return e.state==="in";}).length;
 var by={},i;
 for(i=0;i<z.length;i++){
  if(!z[i].ps)continue;
  (by[z[i].ps]=by[z[i].ps]||[]).push(z[i]);}
 var h='<h3 class="hsec">Week '+wk()
  +' top performers'+(lv?' &middot; '+lv+' live':'')
  +'</h3><div class="lbwrap">'
  +tbl(z.slice(0,10),"Overall");
 ["QB","RB","WR","TE","K"].forEach(function(p){
  h+=tbl((by[p]||[]).slice(0,5),p);});
 host.innerHTML=h+'</div>';}
function tick(){
 if(document.hidden){setTimeout(tick,30000);return;}
 J(API+"scoreboard?week="+wk()+"&seasontype=2&dates=2026")
 .then(function(sb){
  EVS=(sb.events||[]).map(function(e){
   return {id:e.id,
    state:((e.status||{}).type||{}).state};});
  var need=EVS.filter(function(e){
   return e.state!=="pre"
    &&(!CACHE[e.id]||e.state==="in");});
  return Promise.all(need.map(function(e){
   return J(API+"summary?event="+e.id)
    .then(function(s){CACHE[e.id]=s;})
    .catch(function(){});}));})
 .then(function(){draw();setTimeout(tick,30000);})
 .catch(function(e){
  console.log("leaders failed: "+e.message);
  setTimeout(tick,60000);});}
function boot(){
 J("_pos.json").then(function(d){POS=d;})
  .catch(function(){POS={};})
  .then(function(){tick();});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",
  function(){setTimeout(boot,600);});}
else{setTimeout(boot,600);}})();'''
open("site/_leaders.js", "w").write(JS)
print("wrote site/_leaders.js (%d bytes)" % len(JS))

TAG = '<script src="_leaders.js"></script>'
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
