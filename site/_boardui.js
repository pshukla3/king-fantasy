(function(){
var B=null,PT=null,R=null,DEC=null;
var VIEW="proj",MODE="pre",POS="ALL",Q="",SORT=null,DIR=-1;
var SOLO=1;
var TL=["S","A","B","C","D","E","F","G","H"];
var TC=["#ef4444","#f59e0b","#69be28","#38bdf8",
        "#a5acaf","#7c8289","#646a70","#565c62","#4a4f55"];
function esc(x){return String(x==null?"":x)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;");}
function J(u){return fetch(u).then(function(r){
 return r.json();});}
function key(n){return String(n||"").toLowerCase()
 .replace(/\s+(jr|sr|ii|iii|iv)\.?$/,"")
 .replace(/[.'`\u2019\-]/g,"").replace(/\s+/g," ").trim();}
function face(r){
 return r.img?('<img class="bfx" src="'+esc(r.img)
  +'" alt="" loading="lazy" '
  +'onerror="this.style.visibility=\'hidden\'">')
  :'<span class="bfx bfx0">'+esc((r.n||"?")[0])+'</span>';}
function posb(r){
 var p=r.pos,ok=["QB","RB","WR","TE","K","DST"];
 var c=ok.indexOf(p)>=0?p:"K";
 return '<span class="posb '+c+'">'+esc(p)
  +(r.posrk||"")+'</span>';}
function cel(v,cls,dec){
 if(v==null)return '<span class="cel">-</span>';
 return '<span class="cel '+cls+'">'
  +(dec?v.toFixed(dec):v)+'</span>';}
function band(v,t){
 if(v==null||!t)return "";
 return v>=t[1]?"g":(v<=t[0]?"r":"a");}
function sospill(v){
 if(v==null)return '<span class="pl">-</span>';
 var c=v>1.5?"pg":(v<-1.5?"pr":"");
 return '<span class="pl '+c+'">'+(v>0?"+":"")
  +v.toFixed(1)+'%</span>';}
function riskpill(v){
 if(v==null)return '<span class="pl">-</span>';
 var p=Math.round(100*v);
 return '<span class="pl '+(p>=12?"pr":(p<=5?"pg":""))
  +'">'+p+'%</span>';}
function injOf(n){var M=window.__INJ;
 return M?(M[key(n)]||null):null;}
function V(r){return MODE==="upd"?(r.uvorp||0):(r.vorp||0);}
function VAL(r){return MODE==="upd"?(r.uval||0):(r.val||0);}
function PROJ(r){return MODE==="upd"?r.s_upd:r.s_ds;}
function adj(r){
 var j=injOf(r.n);
 if(!j||j.m==null||j.m>=1)return r;
 var o={},k;for(k in r)o[k]=r[k];
 o.vorp=+(( r.vorp||0)*j.m).toFixed(2);
 o.uvorp=+((r.uvorp||0)*j.m).toFixed(2);
 o.val=Math.round((r.val||0)*j.m);
 o.uval=Math.round((r.uval||0)*j.m);
 o.s_ds=(r.s_ds==null?null:Math.round(r.s_ds*j.m));
 o.s_upd=(r.s_upd==null?null:Math.round(r.s_upd*j.m));
 o.inj=j.st;o.injm=j.m;
 return o;}
function thr(rows,fn){
 var T={};
 ["QB","RB","WR","TE","K","DST"].forEach(function(p){
  var v=[];
  rows.forEach(function(r){
   if(r.pos===p){var x=fn(r);if(x!=null)v.push(x);}});
  v.sort(function(a,b){return a-b;});
  if(v.length>4)T[p]=[v[Math.floor(v.length*0.35)],
                      v[Math.floor(v.length*0.72)]];});
 return T;}
function row2(a,b){
 return '<tr><td>'+esc(a)+'</td><td>'+esc(b)+'</td></tr>';}
function open_(r){
 if(window.openCard&&r.pid){
  try{window.openCard(r.pid);return;}catch(e){}}
 var d=R&&R[key(r.n)],dc=DEC&&DEC[key(r.n)];
 var h='<div class="bpv"><button class="bpx">close'
  +'</button><div class="bph">'+face(r)
  +'<div><b>'+esc(r.n)+'</b><span>'+esc(r.pos)
  +(r.posrk?(" "+r.posrk):"")+' &middot; '+esc(r.tm)
  +' &middot; bye '+(r.bye||"-")+'</span></div></div>'
  +'<table class="bpt">'
  +row2("Preseason rank","#"+r.rk)
  +row2("Updated rank","#"+(r.urk||r.rk))
  +row2("Preseason projection",r.base.toFixed(2)+" ppg")
  +row2("Updated projection",r.live.toFixed(2)+" ppg");
 if(dc){h+=row2("  from points",
   (dc.d_pts>0?"+":"")+dc.d_pts.toFixed(2))
  +row2("  from touches",(dc.d_touch>0?"+":"")
   +dc.d_touch.toFixed(2))
  +row2("  from snap share",(dc.d_snap>0?"+":"")
   +dc.d_snap.toFixed(2));}
 h+=row2("Schedule",(r.sos>0?"+":"")+r.sos.toFixed(2))
  +row2("Season floor / ceiling",
   (r.s_floor==null?"-":r.s_floor)+" to "
   +(r.s_ceil==null?"-":r.s_ceil))
  +row2("Injury risk",(r.risk==null?"-":
   (Math.round(100*r.risk)+"%"))
   +(r.gm?(" - "+r.gm+" games"):""))
  +row2("Value over replacement",V(r).toFixed(2))
  +row2("Tier",TL[Math.min(r.tier-1,8)])+'</table>';
 if(d&&d.line)h+='<p class="bpl">'+esc(d.line)+'</p>';
 if(d&&d.why&&d.why.length){h+='<ul class="bpw">';
  d.why.forEach(function(w){h+='<li>'+esc(w)+'</li>';});
  h+='</ul>';}
 var o=document.getElementById("bpov");
 if(!o){o=document.createElement("div");o.id="bpov";
  document.body.appendChild(o);}
 o.innerHTML=h+'</div>';o.style.display="block";
 o.onclick=function(e){
  if(e.target===o||e.target.className==="bpx")
   o.style.display="none";};}
function flt(r){
 if(POS!=="ALL"&&r.pos!==POS)return false;
 if(Q&&String(r.n).toLowerCase().indexOf(Q)<0)return false;
 return true;}
function draw(){
 var h=document.getElementById("kfbd");
 if(!h){var sec=document.getElementById("rank");
  if(!sec)return;
  h=document.createElement("div");h.id="kfbd";
  sec.insertBefore(h,sec.firstChild);}
 if(!B){h.innerHTML='<p class="sub">Loading...</p>';return;}
 var PS=["ALL","QB","RB","WR","TE","K","DST"];
 var s='<h2>Rankings</h2><p class="sub">Expert '
  +'consensus (FantasyPros + Flock, which agree at '
  +'rho 0.92) as the base, adjusted by our usage model '
  +'at 35% weight, moved by week 1 within a cap, and '
  +'penalised for expected games missed.</p>'
  +'<div class="bfl">'
  +PS.map(function(p){return '<button data-p="'+p+'" class="'
   +(p===POS?"on":"")+'">'+p+'</button>';}).join("")
  +'<input id="bq" placeholder="Search for a player" '
  +'value="'+esc(Q)+'"></div>';
 var z,hd,T;
 if(VIEW==="pts"){
  z=(PT?PT.rows:[]).filter(flt);
  T=thr(z,function(r){return r.pts;});
  hd='<tr><th>RK</th><th>Player</th><th>POS</th>'
   +'<th class="n">TM</th><th class="n">G</th>'
   +'<th class="n">FPTS</th><th class="n">PPG</th></tr>';
 }else{
  z=(B?B.rows:[]).filter(flt).map(adj);
  z=z.sort(function(a,b){return (a.rk||0)-(b.rk||0);});
  if(SORT)z=z.slice().sort(function(a,b){
   var x=a[SORT],y=b[SORT];
   if(x==null)return 1;if(y==null)return -1;
   return DIR*(x-y);});
  T=thr(z,PROJ);
  hd='<tr><th>RK</th><th>Player</th><th>POS</th>'
   +'<th class="n">Games</th><th class="n">ADP</th>'
   +'<th class="n">Bye</th><th class="n">SOS</th>'
   +'<th class="n">Injury Risk</th>'
   +'<th class="n" data-s="s_floor">Floor</th>'
   +'<th class="n" data-s="s_cons">Cons</th>'
   +'<th class="n">Proj</th>'
   +'<th class="n" data-s="s_ceil">Ceiling</th>'
   +'<th class="n">Value</th></tr>';}
 s+='<div class="bn">'+z.length+' players &middot; '
  +"consensus + usage model"+'</div>'
  +'<table class="btb"><thead>'+hd+'</thead><tbody>';
 var lt=null;
 z.forEach(function(r,i){
  s+='<tr class="brw" data-i="'+i+'">'
   +'<td class="bk">'+(VIEW==="pts"?r.rk:(i+1))+'</td>'
   +'<td class="bnm">'+face(r)+'<span><b>'+esc(r.n)
   +(r.inj?(' <u class="injb'+(r.injm===0?" out":"")
     +'">'+esc(r.inj)+'</u>'):'')
   +'</b><i>'+esc(r.tm)+'</i></span></td>'
   +'<td>'+posb(r)+'</td>';
  if(VIEW==="pts"){
   s+='<td class="n">'+esc(r.tm)+'</td>'
    +'<td class="n">'+r.g+'</td>'
    +'<td class="n">'+cel(r.pts,band(r.pts,T[r.pos]),1)
    +'</td><td class="n">'+r.ppg.toFixed(1)+'</td>';
  }else{
   s+='<td class="n">'+(r.gm||17)+'</td>'
    +'<td class="n">'+(r.adp_rp||"-")+'</td>'
    +'<td class="n">'+(r.bye||"-")+'</td>'
    +'<td class="n">'+sospill(r.sos_pct)+'</td>'
    +'<td class="n">'+riskpill(r.risk)+'</td>'
    +'<td class="n">'+(r.s_floor==null?"-":r.s_floor)
    +'</td><td class="n">'+(r.s_cons==null?"-":r.s_cons)
    +'</td><td class="n">'
    +cel(PROJ(r),band(PROJ(r),T[r.pos]),0)+'</td>'
    +'<td class="n">'+(r.s_ceil==null?"-":r.s_ceil)
    +'</td><td class="n bv">'+VAL(r)+'</td>';}
  s+='</tr>';});
 h.innerHTML=s+'</tbody></table>';
 window.__kfRedraw=draw;
 var cur=z;
 Array.prototype.forEach.call(
  h.querySelectorAll(".brw"),function(t){
  t.onclick=function(){
   open_(cur[parseInt(t.getAttribute("data-i"),10)]);};});
 Array.prototype.forEach.call(
  h.querySelectorAll(".bvt button"),function(b){
  b.onclick=function(){
   var m=b.getAttribute("data-m");
   if(m){MODE=m;}else{VIEW=b.getAttribute("data-v");}
   SORT=null;draw();};});
 Array.prototype.forEach.call(
  h.querySelectorAll(".bfl button"),function(b){
  b.onclick=function(){POS=b.getAttribute("data-p");
   draw();};});
 Array.prototype.forEach.call(
  h.querySelectorAll("th[data-s]"),function(t){
  t.style.cursor="pointer";
  t.onclick=function(){
   var k=t.getAttribute("data-s");
   if(SORT===k)DIR=-DIR;else{SORT=k;DIR=-1;}draw();};});
 var q=document.getElementById("bq");
 if(q)q.oninput=function(){Q=q.value.toLowerCase();draw();
  var e=document.getElementById("bq");
  if(e){e.focus();
   e.setSelectionRange(e.value.length,e.value.length);}};}
Promise.all([J("_board.json"),J("_points.json"),
 J("_reasons.json").catch(function(){return {};}),
 J("_decomp.json").catch(function(){return {};})])
.then(function(a){B=a[0];PT=a[1];R=a[2];DEC=a[3];draw();})
.catch(function(e){console.log("board: "+e.message);});
})();