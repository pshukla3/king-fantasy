(function(){
var P=[],A=[],Bs=[],S={t:10,ppr:1,tep:0,sf:0};
function q(i){return document.getElementById(i);}
function esc(s){return String(s).replace(/[&<>"]/g,
 function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",
 '"':"&quot;"}[c];});}
function pts(x){
 return x.g-(1-S.ppr)*x.rec+(x.p==="TE"?S.tep*x.rec:0);}
function build(){
 var need={QB:S.sf?Math.round(1.7*S.t):S.t,
  RB:Math.round(2.5*S.t),WR:Math.round(3*S.t),
  TE:S.t,K:S.t,DST:S.t};
 var by={},r={},k;
 P.forEach(function(x){(by[x.p]=by[x.p]||[]).push(pts(x));});
 for(k in by){by[k].sort(function(a,b){return b-a;});
  var i=Math.max(0,Math.min(by[k].length-1,(need[k]||S.t)-1));
  r[k]=by[k][i]||0;}
 var mx=0;
 P.forEach(function(x){
  x.sv=Math.max(0,pts(x)-(r[x.p]||0));
  if(x.sv>mx)mx=x.sv;});
 P.forEach(function(x){
  x.v=Math.max(1,Math.round(10000*x.sv/(mx||1)));});
 P.sort(function(a,b){return b.v-a.v;});}
function tot(L){var s=0;L.forEach(function(x){s+=x.v;});
 return s;}
function chips(L,side){
 return L.map(function(x,i){
  return '<div class="tcchip" data-s="'+side+'" data-i="'+i+
  '"><b>'+esc(x.n)+'</b><span>'+esc(x.p)+
  (x.t?" "+esc(x.t):"")+' &middot; '+pts(x).toFixed(1)+
  ' ppg</span><u>'+x.v.toLocaleString()+
  '</u><em>&times;</em></div>';}).join("")
  ||'<div class="tcempty">no players yet</div>';}
function equal(){
 var d=tot(A)-tot(Bs),ab=Math.abs(d);
 if(ab<200||!P.length)return "";
 var side=d>0?"their side":"your side";
 var c=P.filter(function(x){
  return Math.abs(x.v-ab)<ab*0.28;})
  .sort(function(a,b){
   return Math.abs(a.v-ab)-Math.abs(b.v-ab);}).slice(0,6);
 if(!c.length)return "";
 return '<div class="tceq"><h4>Add to '+side
 +' to even it out</h4>'+c.map(function(x){
  return '<div class="tcrow"><b>'+esc(x.n)+'</b><span>'
  +esc(x.p)+'</span><u>'+x.v.toLocaleString()
  +'</u></div>';}).join("")+'</div>';}
function draw(){
 var ta=tot(A),tb=tot(Bs),d=ta-tb;
 q("tcA").innerHTML=chips(A,"A");
 q("tcB").innerHTML=chips(Bs,"B");
 q("tcVA").textContent=ta.toLocaleString();
 q("tcVB").textContent=tb.toLocaleString();
 var v=q("tcV");
 if(!A.length||!Bs.length){v.className="tcv";
  v.textContent="Add players to both sides";}
 else if(Math.abs(d)<Math.max(300,0.04*Math.max(ta,tb))){
  v.className="tcv even";
  v.textContent="Even trade \u2014 within noise";}
 else{v.className="tcv "+(d>0?"b":"a");
  v.textContent=(d>0?"You lose by ":"You win by ")
   +Math.abs(d).toLocaleString()+" ("
   +(100*Math.abs(d)/Math.max(ta,tb)).toFixed(0)+"%)";}
 q("tcEq").innerHTML=equal();}
function reprice(){build();
 A.forEach(function(x,i){A[i]=byName(x.n)||x;});
 Bs.forEach(function(x,i){Bs[i]=byName(x.n)||x;});
 draw();}
function byName(n){
 for(var i=0;i<P.length;i++)if(P[i].n===n)return P[i];
 return null;}
function sug(inp,box,side){
 var s=inp.value.trim().toLowerCase();
 if(s.length<2){box.innerHTML="";return;}
 box.innerHTML=P.filter(function(x){
  return x.n.toLowerCase().indexOf(s)>=0;}).slice(0,8)
  .map(function(x){
   return '<div class="tcsug" data-n="'+esc(x.n)
   +'" data-side="'+side+'"><b>'+esc(x.n)+'</b><span>'
   +esc(x.p)+(x.t?" "+esc(x.t):"")+'</span><u>'
   +x.v.toLocaleString()+'</u></div>';}).join("");}
function boot(){
 var host=q("tcwrap");
 if(!host)return;
 fetch("_tc.json").then(function(r){return r.json();})
 .then(function(d){P=d;build();draw();});
 ["A","B"].forEach(function(s){
  var i=q("tcI"+s),b=q("tcS"+s);
  i.addEventListener("input",function(){sug(i,b,s);});
  i.addEventListener("blur",function(){
   setTimeout(function(){b.innerHTML="";},180);});});
 ["tcT","tcP","tcE"].forEach(function(id){
  var e=q(id);if(!e)return;
  e.addEventListener("change",function(){
   S.t=parseInt(q("tcT").value,10);
   S.ppr=parseFloat(q("tcP").value);
   S.tep=parseFloat(q("tcE").value);
   reprice();});});
 var sf=q("tcF");
 if(sf)sf.addEventListener("change",function(){
  S.sf=sf.checked?1:0;reprice();});
 host.addEventListener("mousedown",function(e){
  var t=e.target.closest?e.target.closest(".tcsug"):null;
  if(t){var pl=byName(t.getAttribute("data-n")),
   s=t.getAttribute("data-side");
   if(pl){(s==="A"?A:Bs).push(pl);
    q("tcI"+s).value="";q("tcS"+s).innerHTML="";draw();}
   return;}
  var c=e.target.closest?e.target.closest(".tcchip"):null;
  if(c){var si=c.getAttribute("data-s"),
   ix=parseInt(c.getAttribute("data-i"),10);
   (si==="A"?A:Bs).splice(ix,1);draw();}});
 q("tcClr").addEventListener("click",function(){
  A=[];Bs=[];draw();});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",boot);}
else{boot();}})();