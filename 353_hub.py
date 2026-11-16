import json

LG = json.load(open("site/_slteams.json"))["league"]

HTML = '''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
body{margin:0;background:transparent;color:#f9fafb;
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",
Roboto,sans-serif}
.tabs{display:flex;gap:6px;margin:0 0 16px;flex-wrap:wrap;
border-bottom:1px solid #374151;padding-bottom:12px}
.stab{background:#1f2937;border:1px solid #374151;
color:#9ca3af;border-radius:8px;padding:8px 16px;
cursor:pointer;font-size:11px;font-weight:700;
letter-spacing:.08em;text-transform:uppercase}
.stab.on{background:#06b6d4;color:#111827;
border-color:#06b6d4}
.grid{display:grid;gap:10px;
grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.card{background:#1f2937;border:1px solid #374151;
border-radius:12px;padding:14px}
.card.me{border-color:#06b6d4}
h4{margin:0 0 10px;font-size:11px;letter-spacing:.08em;
text-transform:uppercase;color:#9ca3af;font-weight:700}
table{width:100%;border-collapse:collapse}
th{text-align:left;font-size:10px;color:#9ca3af;
letter-spacing:.07em;text-transform:uppercase;
padding:6px 8px;border-bottom:1px solid #374151}
td{padding:6px 8px;border-bottom:1px solid #232f3e;
font-size:13px}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.pos{font-size:10px;color:#9ca3af}
.inj{color:#f87171;font-size:10px;font-weight:700}
.est{color:#9ca3af;font-size:10px}
.live{color:#06b6d4;font-weight:700}
.fin{color:#10b981;font-weight:700}
.big{font-size:26px;font-weight:800;
font-variant-numeric:tabular-nums}
.sm{font-size:11px;color:#9ca3af;letter-spacing:.06em;
text-transform:uppercase}
.mrow{display:flex;justify-content:space-between;
align-items:center;padding:8px 0}
.mrow b{font-size:14px}
.win{color:#10b981}
button.opt{margin:10px 0;padding:9px 18px;border-radius:8px;
border:1px solid #06b6d4;background:transparent;
color:#06b6d4;font-weight:700;cursor:pointer;font-size:12px}
button.opt:hover{background:#06b6d4;color:#111827}
.gain{color:#f87171;font-weight:700;margin-top:8px}
.ok{color:#10b981;font-weight:700;margin-top:8px}
.f{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.f button{background:#1f2937;border:1px solid #374151;
color:#9ca3af;border-radius:6px;padding:5px 12px;
cursor:pointer;font-size:11px;font-weight:700}
.f button.on{background:#06b6d4;color:#111827;
border-color:#06b6d4}
.mut{color:#9ca3af;padding:14px 0}
</style></head><body>
<div class="tabs">
<div class="stab on" data-s="mu">Matchup</div>
<div class="stab" data-s="tm">My Team</div>
<div class="stab" data-s="wv">Waivers</div>
<div class="stab" data-s="gm">League Games</div>
<div class="stab" data-s="st">Standings</div>
</div>
<div id="v" class="mut">Loading league...</div>
<script>
var LG="__LG__";
var SL="https://api.sleeper.app/v1/";
var ES="https://site.api.espn.com/apis/site/v2/sports/"
 +"football/nfl/";
var ANCH=Date.UTC(2026,8,8);
function wk(){var d=Math.floor((Date.now()-ANCH)/864e5);
 return d<0?1:Math.min(18,Math.floor(d/7)+1);}
var T=null,AV=null,SCH=null,PTS={},GS={},TAB="mu",
 POSF="ALL",SHOW=0;
function J(u){return fetch(u).then(function(r){
 if(!r.ok)throw new Error(r.status);return r.json();});}
function esc(x){return String(x==null?"":x)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;");}
var E2N={"LAR":"LA","WSH":"WAS","JAC":"JAX","AZ":"ARI"};
function nz(a){a=(a||"").toUpperCase();
 return E2N[a]||a;}
function team(id){var i;
 for(i=0;i<T.teams.length;i++)
  if(T.teams[i].id===id)return T.teams[i];
 return null;}
function me(){var i;
 for(i=0;i<T.teams.length;i++)
  if(T.teams[i].mine)return T.teams[i];
 return T.teams[0];}
function elapsed(g){
 if(!g||g.state==="pre")return 0;
 if(g.state==="post")return 1;
 var c=String(g.clock||"15:00").split(":");
 var left=(parseInt(c[0],10)||0)*60
  +(parseInt(c[1],10)||0);
 var done=(Math.min(g.period||1,4)-1)*900+(900-left);
 return Math.max(0,Math.min(1,done/3600));}
function pstate(p){
 var g=GS[nz(p.tm)];
 return g?g.state:"pre";}
function calc(t){
 var cur=0,proj=0,rows=[],i;
 var by={};
 for(i=0;i<t.players.length;i++)
  by[t.players[i].pid]=t.players[i];
 for(i=0;i<t.starters.length;i++){
  var pid=t.starters[i],p=by[pid];
  var slot=(T.slots.filter(function(x){
   return x!=="BN";})[i])||"";
  if(!p){rows.push({slot:slot,n:"(empty)",pts:0,
   proj:0,st:"pre"});continue;}
  var live=PTS[pid];
  var st=pstate(p);
  var c=(live==null)?0:live;
  var pr;
  if(st==="post")pr=c;
  else if(st==="in")pr=c+p.ppg*(1-elapsed(GS[nz(p.tm)]));
  else pr=p.ppg;
  cur+=c;proj+=pr;
  rows.push({slot:slot,n:p.n,pos:p.pos,tm:p.tm,
   pts:c,proj:pr,st:st,inj:p.inj,est:p.est,
   ppg:p.ppg});}
 return {cur:cur,proj:proj,rows:rows};}
function optimize(t){
 var FX={FLEX:["RB","WR","TE"],
  SUPER_FLEX:["QB","RB","WR","TE"],
  WRRB_FLEX:["RB","WR"],REC_FLEX:["WR","TE"]};
 var SL2=T.slots.filter(function(x){return x!=="BN";});
 var pool=t.players.slice().sort(function(a,b){
  return b.ppg-a.ppg;});
 var used={},line=[],i,j;
 for(i=0;i<SL2.length;i++){
  var s=SL2[i];if(FX[s])continue;
  var ok=(s==="DEF"||s==="DST")?["DEF","DST"]:[s];
  var pk=null;
  for(j=0;j<pool.length;j++)
   if(ok.indexOf(pool[j].pos)>=0&&!used[pool[j].pid]){
    pk=pool[j];used[pk.pid]=1;break;}
  line.push({s:s,p:pk});}
 for(i=0;i<SL2.length;i++){
  var s2=SL2[i];if(!FX[s2])continue;
  var ok2=FX[s2],pk2=null;
  for(j=0;j<pool.length;j++)
   if(ok2.indexOf(pool[j].pos)>=0&&!used[pool[j].pid]){
    pk2=pool[j];used[pk2.pid]=1;break;}
  line.push({s:s2,p:pk2});}
 return line;}
function ptag(r){
 if(r.st==="post")return '<span class="fin">'
  +r.pts.toFixed(2)+'</span>';
 if(r.st==="in")return '<span class="live">'
  +r.pts.toFixed(2)+'</span>';
 return '<span class="est">-</span>';}
function vMatch(){
 var W=String(wk()),pr=(SCH&&SCH[W])||[];
 if(!pr.length)return '<div class="mut">'
  +'No matchups published for week '+W+'.</div>';
 return '<div class="grid">'+pr.map(function(g){
  var a=team(g[0].id),b=team(g[1].id);
  if(!a||!b)return "";
  var ca=calc(a),cb=calc(b);
  var mine=(a.mine||b.mine);
  var row=function(t,c,o){
   return '<div class="mrow"><div><b>'+esc(t.owner)
    +'</b><div class="sm">proj '+c.proj.toFixed(1)
    +'</div></div><div class="big'
    +(c.proj>o.proj?" win":"")+'">'
    +c.cur.toFixed(1)+'</div></div>';};
  return '<div class="card'+(mine?" me":"")+'">'
   +'<h4>Week '+W+'</h4>'+row(a,ca,cb)
   +'<div style="border-top:1px solid #374151"></div>'
   +row(b,cb,ca)+'</div>';}).join("")+'</div>';}
function vTeam(){
 var t=me(),c=calc(t);
 var h='<div class="card me"><h4>'+esc(t.owner)
  +' &middot; week '+wk()+'</h4>'
  +'<div class="mrow"><div><div class="sm">Now</div>'
  +'<div class="big">'+c.cur.toFixed(1)+'</div></div>'
  +'<div style="text-align:right"><div class="sm">'
  +'Projected final</div><div class="big">'
  +c.proj.toFixed(1)+'</div></div></div>'
  +'<button class="opt" id="ob">'
  +(SHOW?"Hide optimal":"Optimize lineup")+'</button>';
 h+='<table><tr><th></th><th>Player</th><th>Pos</th>'
  +'<th class="n">Proj</th><th class="n">Now</th></tr>';
 c.rows.forEach(function(r){
  h+='<tr><td class="pos">'+esc(r.slot)+'</td>'
   +'<td>'+esc(r.n)
   +(r.inj?' <span class="inj">'+esc(r.inj)+'</span>':'')
   +(r.est?' <span class="est">est</span>':'')
   +'</td><td class="pos">'+esc(r.pos||"")+' '
   +esc(r.tm||"")+'</td>'
   +'<td class="n">'+(r.ppg==null?"-":r.ppg.toFixed(2))
   +'</td><td class="n">'+ptag(r)+'</td></tr>';});
 h+='</table>';
 if(SHOW){
  var L=optimize(t),tot=0;
  h+='<h4 style="margin-top:16px">Optimal lineup</h4>'
   +'<table><tr><th></th><th>Player</th>'
   +'<th class="n">Proj</th></tr>';
  L.forEach(function(x){
   if(!x.p){h+='<tr><td class="pos">'+esc(x.s)
    +'</td><td class="mut">none eligible</td>'
    +'<td class="n">-</td></tr>';return;}
   tot+=x.p.ppg;
   h+='<tr><td class="pos">'+esc(x.s)+'</td><td>'
    +esc(x.p.n)
    +(x.p.inj?' <span class="inj">'+esc(x.p.inj)
      +'</span>':'')
    +'</td><td class="n">'+x.p.ppg.toFixed(2)
    +'</td></tr>';});
  h+='</table>';
  var d=tot-c.proj;
  h+=(d>0.05
   ?'<div class="gain">+'+d.toFixed(2)
    +' available on your bench</div>'
   :'<div class="ok">Your lineup is already optimal</div>');}
 return h+'</div>';}
function vWaiv(){
 if(!AV)return '<div class="mut">Loading...</div>';
 var P=["ALL","QB","RB","WR","TE","K","DST"];
 var h='<div class="f">'+P.map(function(p){
  return '<button data-p="'+p+'" class="'
   +(p===POSF?"on":"")+'">'+p+'</button>';}).join("")
  +'</div><div class="card"><h4>Best available</h4>'
  +'<table><tr><th>Player</th><th>Pos</th>'
  +'<th class="n">Proj</th></tr>';
 var z=AV.filter(function(x){
  return POSF==="ALL"||x.pos===POSF;}).slice(0,40);
 z.forEach(function(x){
  h+='<tr><td>'+esc(x.n)
   +(x.inj?' <span class="inj">'+esc(x.inj)+'</span>':'')
   +'</td><td class="pos">'+esc(x.pos)+' '+esc(x.tm)
   +'</td><td class="n">'+x.ppg.toFixed(2)
   +'</td></tr>';});
 return h+'</table></div>';}
function vGames(){
 if(!SCH)return '<div class="mut">Loading...</div>';
 var ws=Object.keys(SCH).sort(function(a,b){
  return b-a;});
 return '<div class="grid">'+ws.map(function(w){
  var h='<div class="card"><h4>Week '+w+'</h4>';
  SCH[w].forEach(function(g){
   var a=team(g[0].id),b=team(g[1].id);
   if(!a||!b)return;
   var pa=g[0].pts,pb=g[1].pts;
   var done=(pa>0||pb>0);
   h+='<div class="mrow"><div><b>'+esc(a.owner)
    +'</b> vs <b>'+esc(b.owner)+'</b></div>'
    +'<div class="'+(done?"":"est")+'">'
    +(done?(pa.toFixed(1)+" - "+pb.toFixed(1)):"-")
    +'</div></div>';});
  return h+'</div>';}).join("")+'</div>';}
function vStand(){
 var z=T.teams.slice().sort(function(a,b){
  if(b.w!==a.w)return b.w-a.w;return b.pf-a.pf;});
 var h='<div class="card"><h4>Standings</h4><table>'
  +'<tr><th>#</th><th>Team</th><th class="n">W-L</th>'
  +'<th class="n">PF</th><th class="n">PA</th></tr>';
 z.forEach(function(t,i){
  h+='<tr><td class="pos">'+(i+1)+'</td><td>'
   +esc(t.owner)+(t.mine?' <span class="live">you</span>':'')
   +'</td><td class="n">'+t.w+"-"+t.l
   +'</td><td class="n">'+t.pf.toFixed(1)
   +'</td><td class="n">'+t.pa.toFixed(1)+'</td></tr>';});
 return h+'</table></div>';}
function draw(){
 var v=document.getElementById("v");
 if(!T){v.innerHTML='<div class="mut">Loading...</div>';
  return;}
 v.className="";
 v.innerHTML=(TAB==="mu"?vMatch():TAB==="tm"?vTeam()
  :TAB==="wv"?vWaiv():TAB==="gm"?vGames():vStand());
 var ob=document.getElementById("ob");
 if(ob)ob.onclick=function(){SHOW=!SHOW;draw();};
 Array.prototype.forEach.call(
  v.querySelectorAll(".f button"),function(b){
  b.onclick=function(){
   POSF=b.getAttribute("data-p");draw();};});}
function tabs(){
 Array.prototype.forEach.call(
  document.querySelectorAll(".stab"),function(b){
  b.onclick=function(){
   TAB=b.getAttribute("data-s");
   Array.prototype.forEach.call(
    document.querySelectorAll(".stab"),function(x){
    x.className="stab"+(x===b?" on":"");});
   draw();};});}
function live(){
 return J(SL+"league/"+LG+"/matchups/"+wk())
  .then(function(M){
   PTS={};
   M.forEach(function(m){
    var pp=m.get?null:(m.players_points||{});
    for(var k in pp)PTS[k]=pp[k];});
   return J(ES+"scoreboard?week="+wk()
    +"&seasontype=2&dates=2026");})
  .then(function(sb){
   GS={};
   (sb.events||[]).forEach(function(e){
    var st=e.status||{};
    var o={state:((st.type||{}).state),
     period:st.period,clock:st.displayClock};
    (((e.competitions||[])[0]||{}).competitors||[])
     .forEach(function(x){
     GS[nz((x.team||{}).abbreviation)]=o;});});});}
function tick(){
 if(document.hidden){setTimeout(tick,30000);return;}
 live().then(function(){draw();setTimeout(tick,30000);})
 .catch(function(e){
  console.log("hub: "+e.message);
  setTimeout(tick,60000);});}
Promise.all([J("_slteams.json"),J("_avail.json"),
 J("_lgsched.json")]).then(function(r){
 T=r[0];AV=r[1];SCH=r[2];
 var mine=null,i;
 for(i=0;i<T.teams.length;i++)
  if(String(T.teams[i].owner||"").indexOf("Shukie")===0)
   mine=T.teams[i];
 if(!mine)mine=T.teams[0];
 mine.mine=true;
 tabs();draw();return live();})
.then(function(){draw();tick();})
.catch(function(e){
 document.getElementById("v").innerHTML=
  '<div class="mut">Could not load league: '
  +esc(e.message)+'</div>';});
</script></body></html>'''.replace("__LG__", LG)

open("site/league.html", "w").write(HTML)
print("wrote site/league.html (%d KB) - 5 tabs"
      % (len(HTML) // 1024))
