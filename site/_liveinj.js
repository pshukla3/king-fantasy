(function(){
var E="https://site.api.espn.com/apis/site/v2/sports/"
 +"football/nfl/injuries";
var ZERO={"out":1,"doubtful":1,"injured reserve":1,
 "suspension":1,"suspended":1,
 "physically unable to perform":1,
 "non football injury":1};
var MULT=null;
function key(n){return String(n||"").toLowerCase()
 .replace(/\s+(jr|sr|ii|iii|iv)\.?$/,"")
 .replace(/[.'`\u2019\-]/g,"").replace(/\s+/g," ").trim();}
function J(u){return fetch(u).then(function(r){
 if(!r.ok)throw new Error(r.status);return r.json();});}
function build(d){
 var M={},n=0,z=0;
 (d.injuries||[]).forEach(function(t){
  (t.injuries||[]).forEach(function(i){
   var a=i.athlete||{},nm=a.displayName;
   if(!nm)return;
   var s=String(i.status||"").trim();
   var lo=s.toLowerCase();
   if(!s||lo==="active")return;
   var de=i.details||{},ty=String(de.type||"");
   var m=1;
   if(ZERO[lo]){m=0;z++;}
   else if(lo==="questionable"){
    m=MULT?MULT.q:0.515;
    if(MULT&&MULT.byType){
     for(var t2 in MULT.byType){
      if(t2&&ty.toLowerCase()
        .indexOf(t2.toLowerCase())>=0){
       m=MULT.byType[t2];break;}}}}
   else return;
   M[key(nm)]={st:s,ty:ty,m:m};n++;});});
 return {M:M,n:n,z:z};}
function tick(){
 if(document.hidden){setTimeout(tick,60000);return;}
 J(E).then(function(d){
  var r=build(d);
  window.__INJ=r.M;
  var el=document.getElementById("injst");
  if(el)el.textContent="injuries live: "+r.n
   +" flagged, "+r.z+" ruled out - updated "
   +new Date().toLocaleTimeString(undefined,
     {hour:"numeric",minute:"2-digit"});
  if(window.__kfRedraw){try{window.__kfRedraw();}
   catch(e){}}
  setTimeout(tick,60000);})
 .catch(function(e){
  console.log("liveinj: "+e.message);
  setTimeout(tick,120000);});}
function boot(){
 J("_injmult.json").then(function(m){MULT=m;})
  .catch(function(){MULT=null;})
  .then(function(){tick();});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",
  function(){setTimeout(boot,900);});}
else{setTimeout(boot,900);}})();