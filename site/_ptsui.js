(function(){
var P=null,POS="ALL",Q="";
function esc(x){return String(x==null?"":x)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;");}
function face(r){
 return r.img?('<img class="bfx" src="'+esc(r.img)
  +'" alt="" loading="lazy" '
  +'onerror="this.style.visibility=\'hidden\'">')
  :'<span class="bfx bfx0">'+esc((r.n||"?")[0])+'</span>';}
function posb(r){
 var ok=["QB","RB","WR","TE","K","DST"];
 var c=ok.indexOf(r.pos)>=0?r.pos:"K";
 return '<span class="posb '+c+'">'+esc(r.pos)
  +(r.posrk||"")+'</span>';}
function thr(z){
 var T={};
 ["QB","RB","WR","TE","K","DST"].forEach(function(p){
  var v=z.filter(function(r){return r.pos===p;})
   .map(function(r){return r.pts;})
   .sort(function(a,b){return a-b;});
  if(v.length>3)T[p]=[v[Math.floor(v.length*0.35)],
                      v[Math.floor(v.length*0.72)]];});
 return T;}
function draw(){
 var h=document.getElementById("kfpts");
 if(!h){var sec=document.getElementById("rpts");
  if(!sec)return;
  h=document.createElement("div");h.id="kfpts";
  sec.appendChild(h);}
 if(!P){h.innerHTML='<p class="sub">Loading...</p>';
  return;}
 var PS=["ALL","QB","RB","WR","TE","K","DST"];
 var z=(P.rows||[]).filter(function(r){
  if(POS!=="ALL"&&r.pos!==POS)return false;
  if(Q&&String(r.n).toLowerCase().indexOf(Q)<0)
   return false;
  return true;});
 var T=thr(z);
 var s='<h2>Points Leaders</h2><p class="sub">Actual '
  +'fantasy points scored through week '+P.week
  +', in your league scoring. This is what has '
  +'happened, not what is projected.</p>'
  +'<div class="bfl">'
  +PS.map(function(p){return '<button data-p="'+p
   +'" class="'+(p===POS?"on":"")+'">'+p+'</button>';})
  .join("")+'<input id="pq" placeholder="search player" '
  +'value="'+esc(Q)+'"></div>'
  +'<div class="bn">'+z.length+' players</div>'
  +'<table class="btb"><thead><tr><th>RK</th>'
  +'<th>Player</th><th>POS</th><th class="n">TM</th>'
  +'<th class="n">G</th><th class="n">POINTS</th>'
  +'<th class="n">PPG</th></tr></thead><tbody>';
 z.forEach(function(r,i){
  var t=T[r.pos];
  var c=t?(r.pts>=t[1]?"g":(r.pts<=t[0]?"r":"a")):"";
  s+='<tr class="brw"><td class="bk">'+(i+1)+'</td>'
   +'<td class="bnm">'+face(r)+'<span><b>'+esc(r.n)
   +'</b><i>'+esc(r.tm)+'</i></span></td>'
   +'<td>'+posb(r)+'</td>'
   +'<td class="n">'+esc(r.tm)+'</td>'
   +'<td class="n">'+r.g+'</td>'
   +'<td class="n"><span class="cel '+c+'">'
   +r.pts.toFixed(1)+'</span></td>'
   +'<td class="n">'+r.ppg.toFixed(1)+'</td></tr>';});
 h.innerHTML=s+'</tbody></table>';
 Array.prototype.forEach.call(
  h.querySelectorAll(".bfl button"),function(b){
  b.onclick=function(){POS=b.getAttribute("data-p");
   draw();};});
 var q=document.getElementById("pq");
 if(q)q.oninput=function(){Q=q.value.toLowerCase();
  draw();var e=document.getElementById("pq");
  if(e){e.focus();
   e.setSelectionRange(e.value.length,e.value.length);}};}
fetch("_points.json").then(function(r){return r.json();})
 .then(function(d){P=d;draw();})
 .catch(function(e){console.log("pts: "+e.message);});
})();