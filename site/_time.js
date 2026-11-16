(function(){
var API="https://site.api.espn.com/apis/site/v2/sports/"
 +"football/nfl/scoreboard?dates=";
var E2N={"LAR":"LA","WSH":"WAS","JAC":"JAX","AZ":"ARI"};
function nz(a){a=(a||"").toUpperCase();return E2N[a]||a;}
function ymd(d){
 return d.getFullYear()
  +("0"+(d.getMonth()+1)).slice(-2)
  +("0"+d.getDate()).slice(-2);}
function fmt(iso){
 var d=new Date(iso);
 if(isNaN(d))return null;
 var day=d.toLocaleDateString(undefined,
  {weekday:"short",month:"short",day:"numeric"});
 var tm=d.toLocaleTimeString(undefined,
  {hour:"numeric",minute:"2-digit"});
 return {day:day,time:tm};}
function boot(){
 var cards=document.querySelectorAll(".sbc");
 if(!cards.length){setTimeout(boot,300);return;}
 var a=new Date(),b=new Date();
 b.setDate(b.getDate()+16);
 fetch(API+ymd(a)+"-"+ymd(b))
 .then(function(r){return r.json();})
 .then(function(sb){
  var M={};
  (sb.events||[]).forEach(function(e){
   var c=(e.competitions||[])[0];
   if(!c||!e.date)return;
   var t=(c.competitors||[]).map(function(x){
    return nz((x.team||{}).abbreviation);});
   if(t.length===2){M[t.sort().join("@")]=e.date;}});
  var hit=0;
  Array.prototype.forEach.call(cards,function(cd){
   var im=cd.querySelectorAll(".sbrow img");
   if(im.length<2)return;
   var k=[nz(im[0].getAttribute("alt")),
          nz(im[1].getAttribute("alt"))].sort().join("@");
   var iso=M[k];
   if(!iso)return;
   var f=fmt(iso);
   if(!f)return;
   var me=cd.querySelector(".sbmeta");
   if(!me)return;
   var wk=(me.textContent.match(/Week\s*\d+/i)||[""])[0];
   me.textContent=(wk?wk+" \u00b7 ":"")
    +f.day+" \u00b7 "+f.time;
   hit++;});
  console.log("localized "+hit+" kickoff times");})
 .catch(function(e){
  console.log("kickoff localize skipped: "+e.message);});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",boot);}
else{setTimeout(boot,250);}})();