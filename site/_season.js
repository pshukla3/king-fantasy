(function(){
function esc(x){return String(x==null?"":x)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;");}
var POSN=["ALL","QB","RB","WR","TE","K"];
var D=null,SEL="ALL";
function tbl(){
 var z=(D.rows||[]).filter(function(x){
  return SEL==="ALL"||x.ps===SEL;}).slice(0,15);
 if(!z.length)return'<div class="lbcol">'
  +'<h5>No data yet</h5></div>';
 var o='<table class="sltab"><thead><tr><th></th>'
  +'<th>Player</th><th>Pos</th><th>G</th>'
  +'<th>Avg</th><th>Total</th></tr></thead><tbody>';
 z.forEach(function(x,i){
  o+='<tr><td class="sli">'+(i+1)+'</td>'
   +'<td class="sln">'+esc(x.n)+'</td>'
   +'<td class="slp">'+esc(x.ps||"-")+' '+esc(x.t)+'</td>'
   +'<td>'+x.g+'</td><td>'+x.avg.toFixed(1)+'</td>'
   +'<td class="slt">'+x.p.toFixed(1)+'</td></tr>';});
 return o+'</tbody></table>';}
function draw(){
 var h=document.getElementById("kfsl");
 if(!h){var hm=document.getElementById("home");
  if(!hm)return;
  h=document.createElement("div");h.id="kfsl";
  hm.appendChild(h);}
 if(!D||!D.rows||!D.rows.length){h.innerHTML="";return;}
 var b=POSN.map(function(p){
  return '<button class="slb'+(p===SEL?" on":"")
   +'" data-p="'+p+'">'+p+'</button>';}).join("");
 h.innerHTML='<h3 class="hsec">Season leaders '
  +'<em>through week '+D.through+'</em></h3>'
  +'<div class="slbar">'+b+'</div>'
  +'<div class="slwrap">'+tbl()+'</div>';
 Array.prototype.forEach.call(
  h.querySelectorAll(".slb"),function(x){
  x.addEventListener("click",function(){
   SEL=x.getAttribute("data-p");draw();});});}
function boot(){
 fetch("_season.json").then(function(r){
  return r.json();}).then(function(d){
  D=d;draw();}).catch(function(e){
  console.log("season leaders: "+e.message);});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",
  function(){setTimeout(boot,700);});}
else{setTimeout(boot,700);}})();