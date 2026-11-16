(function(){
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
var CACHE={},MAP={},EVS=[];
function J(u){return fetch(u).then(function(r){
 if(!r.ok)throw new Error(r.status);return r.json();});}
function norm(s){return String(s||"").toLowerCase()
 .replace(/\s+(jr|sr|ii|iii|iv)\.?$/,"")
 .replace(/[.'`\u2019\-]/g,"")
 .replace(/\s+/g," ").trim();}
function sc(sm,state,out){
 (((sm||{}).boxscore||{}).players||[]).forEach(
 function(x){
  (x.statistics||[]).forEach(function(c){
   var cn=String(c.name||"").toLowerCase();
   var ks=c.keys||[];
   if(!C[cn]&&cn!=="kicking")return;
   (c.athletes||[]).forEach(function(a){
    var at=a.athlete||{},nm=at.displayName;
    if(!nm)return;
    var k=norm(nm);
    var r=out[k]||(out[k]={p:0,st:state,nm:nm});
    r.st=state;
    var ss=a.stats||[],i;
    for(i=0;i<ks.length;i++){
     var kk=ks[i],v=parseFloat(ss[i]);
     if(isNaN(v))continue;
     if(cn==="kicking"){
      if(kk==="totalKickingPoints")r.p+=v;}
     else if(P[kk]!==undefined)r.p+=v*P[kk];}});});});}
function load(){
 return J(API+"scoreboard?week="+wk()
  +"&seasontype=2&dates=2026").then(function(sb){
  EVS=(sb.events||[]).map(function(e){
   return {id:e.id,
    state:((e.status||{}).type||{}).state};});
  var need=EVS.filter(function(e){
   return e.state!=="pre"
    &&(!CACHE[e.id]||e.state==="in");});
  return Promise.all(need.map(function(e){
   return J(API+"summary?event="+e.id)
    .then(function(s){CACHE[e.id]=s;})
    .catch(function(){});}));});}
function build(){var out={};
 EVS.forEach(function(e){
  if(CACHE[e.id])sc(CACHE[e.id],e.state,out);});
 MAP=out;}
function clr(){
 var b=document.querySelectorAll(".lpts"),i;
 for(i=0;i<b.length;i++)b[i].parentNode.removeChild(b[i]);
 var d=document.querySelectorAll("[data-lp]");
 for(i=0;i<d.length;i++)d[i].removeAttribute("data-lp");}
function ann(){
 var els=document.querySelectorAll(
  "b,strong,span,td,li,a,div"),i,n=0;
 for(i=0;i<els.length;i++){
  var e=els[i];
  if(e.children.length)continue;
  if(e.getAttribute("data-lp"))continue;
  var k=norm(e.textContent);
  if(!k||k.length<6||k.indexOf(" ")<0)continue;
  var r=MAP[k];
  if(!r)continue;
  e.setAttribute("data-lp","1");
  var s=document.createElement("span");
  s.className="lpts"+(r.st==="post"?" fin":" liv");
  s.textContent=r.p.toFixed(1)
   +(r.st==="post"?" FINAL":"");
  e.appendChild(s);n++;}
 return n;}
function tick(){
 if(document.hidden){setTimeout(tick,30000);return;}
 load().then(function(){
  build();clr();
  var n=ann();
  var lv=EVS.filter(function(e){
   return e.state==="in";}).length;
  console.log("lpts: "+n+" tagged, "+lv+" live");
  setTimeout(tick,30000);})
 .catch(function(e){
  console.log("lpts failed: "+e.message);
  setTimeout(tick,60000);});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",
  function(){setTimeout(tick,800);});}
else{setTimeout(tick,800);}})();