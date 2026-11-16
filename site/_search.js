(function(){
var P=[],KW=[
 ["trade calculator","tcalc"],["trade center","tcalc"],
 ["calculator","tcalc"],["trade finder","tfind"],
 ["find trades","tfind"],["trades","tfind"],
 ["mock draft","mock"],["draft","mock"],
 ["rankings","rank"],["tiers","rtiers"],
 ["boom","rboom"],["bust","rboom"],
 ["floor","rboom"],["ceiling","rboom"],
 ["accuracy","acc"],["model","acc"],
 ["playoff odds","lgodds"],["odds","lgodds"],
 ["power rankings","lgpower"],["standings","lgpower"],
 ["rosters","rosters"],["depth chart","rosters"],
 ["my team","calc"],["league","league"],
 ["news","home"],["scores","home"],["home","home"]];
function hit(t){var b=document.querySelector(
 'nav button[data-t="'+t+'"]');if(b)b.click();}
function esc(s){return String(s).replace(/[&<>"]/g,
 function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",
 '"':"&quot;"}[c];});}
function boot(){
 var bar=document.getElementById("subbar");
 if(!bar||document.getElementById("skq"))return;
 var w=document.createElement("div");w.id="skwrap";
 w.innerHTML='<input id="skq" placeholder="Search players '
  +'or pages\u2026" autocomplete="off">'
  +'<div id="skr"></div>';
 bar.appendChild(w);
 fetch("_tc.json").then(function(r){return r.json();})
  .then(function(d){P=d;}).catch(function(){});
 var q=document.getElementById("skq"),
     r=document.getElementById("skr");
 function draw(){
  var s=q.value.trim().toLowerCase();
  if(s.length<2){r.innerHTML="";r.className="";return;}
  var pg=KW.filter(function(k){
   return k[0].indexOf(s)>=0;}).slice(0,4);
  var pl=P.filter(function(x){
   return x.n.toLowerCase().indexOf(s)>=0;}).slice(0,7);
  var h="";
  pg.forEach(function(k){
   h+='<div class="skrow pg" data-go="'+k[1]+'">'
    +'<b>'+esc(k[0])+'</b><span>page</span></div>';});
  pl.forEach(function(x){
   h+='<div class="skrow" data-pid="'+esc(x.i||"")+'">'
    +'<b>'+esc(x.n)+'</b><span>'+esc(x.p)
    +(x.t?" "+esc(x.t):"")+'</span><u>'+x.g+'</u></div>';});
  r.innerHTML=h||'<div class="skrow"><b>no matches</b></div>';
  r.className=h?"on":"on";}
 q.addEventListener("input",draw);
 q.addEventListener("blur",function(){
  setTimeout(function(){r.className="";},170);});
 q.addEventListener("focus",draw);
 r.addEventListener("mousedown",function(e){
  var t=e.target.closest?e.target.closest(".skrow"):null;
  if(!t)return;
  var go=t.getAttribute("data-go");
  if(go){hit(go);q.value="";r.className="";return;}
  var id=t.getAttribute("data-pid");
  if(id&&window.openCard){window.openCard(id);
   q.value="";r.className="";}});
 document.addEventListener("keydown",function(e){
  if((e.metaKey||e.ctrlKey)&&e.key==="k"){
   e.preventDefault();q.focus();q.select();}
  if(e.key==="Escape"){q.blur();r.className="";}});
 console.log("search ready");}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",boot);}
else{setTimeout(boot,120);}})();