(function(){
var API="https://site.api.espn.com/apis/site/v2/"
 +"sports/football/nfl/";
var ANCH=Date.UTC(2026,8,8);
function wk(){var d=Math.floor((Date.now()-ANCH)/864e5);
 return d<0?1:Math.min(18,Math.floor(d/7)+1);}
var PT={passingYards:.04,passingTouchdowns:4,
 interceptions:-2,rushingYards:.1,rushingTouchdowns:6,
 receptions:1,receivingYards:.1,
 receivingTouchdowns:6,fumblesLost:-2};
var CT={passing:1,rushing:1,receiving:1,fumbles:1};
var E2N={"LAR":"LA","WSH":"WAS","JAC":"JAX","AZ":"ARI"};
function nz(a){a=(a||"").toUpperCase();
 return E2N[a]||a;}
var T=null,CACHE={},EVS=[],SC={},TM={},OPEN={};
function J(u){return fetch(u).then(function(r){
 if(!r.ok)throw new Error(r.status);return r.json();});}
function esc(x){return String(x==null?"":x)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;");}
function nm2(s){return String(s||"").toLowerCase()
 .replace(/\s+(jr|sr|ii|iii|iv)\.?$/,"")
 .replace(/[.'`\u2019\-]/g,"").replace(/\s+/g," ").trim();}
function elapsed(e){
 var st=e.st||{},p=st.period||0;
 if(st.state==="pre")return 0;
 if(st.state==="post")return 1;
 var c=String(st.clock||"15:00").split(":");
 var left=(parseInt(c[0],10)||0)*60+(parseInt(c[1],10)||0);
 var done=(Math.min(p,4)-1)*900+(900-left);
 return Math.max(0,Math.min(1,done/3600));}
function score(sm,out){
 (((sm||{}).boxscore||{}).players||[]).forEach(
 function(x){
  (x.statistics||[]).forEach(function(c){
   var cn=String(c.name||"").toLowerCase(),ks=c.keys||[];
   if(!CT[cn]&&cn!=="kicking")return;
   (c.athletes||[]).forEach(function(a){
    var at=a.athlete||{},n=at.displayName;
    if(!n)return;
    var k=nm2(n),r=out[k]||(out[k]={p:0});
    var ss=a.stats||[],i;
    for(i=0;i<ks.length;i++){
     var kk=ks[i],v=parseFloat(ss[i]);
     if(isNaN(v))continue;
     if(cn==="kicking"){
      if(kk==="totalKickingPoints")r.p+=v;}
     else if(PT[kk]!==undefined)r.p+=v*PT[kk];}});});});}
function patier(pa){
 if(pa===0)return 10;if(pa<=6)return 7;
 if(pa<=13)return 4;if(pa<=20)return 1;
 if(pa<=27)return 0;if(pa<=34)return -1;return -4;}
function spl(v,i){
 var p=String(v==null?"0":v).split(/[-\/]/);
 var n=parseFloat(p[i]);return isNaN(n)?0:n;}
function dstAdd(sm,out){
 var bt=((sm||{}).boxscore||{}).teams||[];
 if(bt.length<2)return;
 var ab=[],stat=[],i;
 for(i=0;i<2;i++){
  ab.push(((bt[i].team||{}).abbreviation)||"");
  var d={};
  (bt[i].statistics||[]).forEach(function(x){
   if(d[x.name]===undefined)d[x.name]=x.displayValue;});
  stat.push(d);}
 var sc={},nmOf={};
 (((sm.header||{}).competitions||[])[0]||{})
  .competitors=(((sm.header||{}).competitions||[])[0]
  ||{}).competitors||[];
 ((((sm.header||{}).competitions||[])[0]||{})
  .competitors||[]).forEach(function(x){
  var t=x.team||{};
  sc[t.abbreviation]=parseInt(x.score,10)||0;
  nmOf[t.abbreviation]=t.displayName||t.abbreviation;});
 for(i=0;i<2;i++){
  var me=ab[i],op=ab[1-i],o=stat[1-i];
  var pts=spl(o.sacksYardsLost,0)*1
   +spl(o.interceptions,0)*2
   +spl(o.fumblesLost,0)*2
   +spl(stat[i].defensiveTouchdowns,0)*6
   +patier(sc[op]||0);
  var k=nm2(nmOf[me]||me);
  out[k]=out[k]||{p:0};
  out[k].p+=pts;}}
function refresh(){
 return J(API+"scoreboard?week="+wk()
  +"&seasontype=2&dates=2026").then(function(sb){
  EVS=[];TM={};
  (sb.events||[]).forEach(function(e){
   var c=(e.competitions||[])[0]||{};
   var st=(e.status||{});
   var o={id:e.id,st:{state:((st.type||{}).state),
    period:st.period,clock:st.displayClock}};
   EVS.push(o);
   (c.competitors||[]).forEach(function(x){
    TM[nz((x.team||{}).abbreviation)]=o;});});
  var need=EVS.filter(function(e){
   return e.st.state!=="pre"
    &&(!CACHE[e.id]||e.st.state==="in");});
  return Promise.all(need.map(function(e){
   return J(API+"summary?event="+e.id)
    .then(function(s){CACHE[e.id]=s;})
    .catch(function(){});}));}).then(function(){
  var out={};
  EVS.forEach(function(e){
   if(CACHE[e.id]){score(CACHE[e.id],out);
    dstAdd(CACHE[e.id],out);}});
  SC=out;});}
function calc(t){
 var st=(t.starters&&t.starters.length)
  ?t.starters:optimal(t).map(function(x){
   return x.p?{name:x.p.n,slot:x.s}:null;})
  .filter(Boolean);
 var cur=0,proj=0,rows=[];
 st.forEach(function(s){
  var k=nm2(s.name);
  var p=null,i;
  for(i=0;i<t.players.length;i++){
   if(t.players[i].k===k){p=t.players[i];break;}}
  var base=p?p.ppg:(s.ppg||0);
  var g=p?TM[nz(p.nfl)]:null;
  var stt=g?g.st.state:"pre";
  var act=SC[k]?SC[k].p:null;
  var c=(act==null)?0:act;
  var pr;
  if(stt==="post"){pr=c;}
  else if(stt==="in"){
   pr=c+base*(1-elapsed(g));}
  else{pr=base;}
  cur+=c;proj+=pr;
  rows.push({slot:s.slot||"",n:s.name,
   nfl:p?p.nfl:"",st:stt,cur:c,pr:pr,
   inj:p?(p.inj||""):""});});
 return {cur:cur,proj:proj,rows:rows};}
function optimal(t){
 var SL=T.slots,FX={FLEX:["RB","WR","TE"],
  SUPER_FLEX:["QB","RB","WR","TE"],
  WRRB_FLEX:["RB","WR"],REC_FLEX:["WR","TE"]};
 var pool=t.players.slice().sort(function(a,b){
  return b.ppg-a.ppg;});
 var used={},line=[];
 SL.forEach(function(s){
  if(FX[s])return;
  var ok=(s==="DEF"||s==="DST")?["DEF","DST"]:[s];
  var pick=null,i;
  for(i=0;i<pool.length;i++){
   if(ok.indexOf(pool[i].pos)>=0&&!used[pool[i].n]){
    pick=pool[i];used[pick.n]=1;break;}}
  line.push({s:s,p:pick});});
 SL.forEach(function(s){
  if(!FX[s])return;
  var ok=FX[s],pick=null,i;
  for(i=0;i<pool.length;i++){
   if(ok.indexOf(pool[i].pos)>=0&&!used[pool[i].n]){
    pick=pool[i];used[pick.n]=1;break;}}
  line.push({s:s,p:pick});});
 return line;}
function card(t){
 var r=calc(t),me=(t.id===T.my);
 var o='<div class="mxc'+(me?" me":"")+'">'
  +'<div class="mxh"><b>'+esc(t.name)+'</b>'
  +'<span>'+esc(t.owner||"")+'</span></div>'
  +'<div class="mxn"><i>NOW</i><b>'
  +r.cur.toFixed(1)+'</b></div>'
  +'<div class="mxp"><i>PROJECTED FINAL</i><b>'
  +r.proj.toFixed(1)+'</b></div>'
  +'<button class="mxo" data-id="'+t.id+'">'
  +(OPEN[t.id]?"Hide":"Optimize")+'</button>';
 if(OPEN[t.id]){
  var L=optimal(t),tot=0,ln="";
  L.forEach(function(x){
   if(!x.p){ln+='<div class="mxr"><i>'+esc(x.s)
     +'</i><b>none eligible</b></div>';return;}
   tot+=x.p.ppg;
   var lk=x.p.inj?' <u class="mxi">'+esc(x.p.inj)+'</u>':'';
   ln+='<div class="mxr"><i>'+esc(x.s)+'</i><b>'
    +esc(x.p.n)+lk+'</b><span>'+x.p.ppg.toFixed(2)
    +'</span></div>';});
  var d=tot-r.proj;
  o+='<div class="mxl">'+ln
   +'<div class="mxr tot"><i>BEST</i><b></b><span>'
   +tot.toFixed(2)+'</span></div>'
   +'<div class="mxd'+(d>0.05?" gain":"")+'">'
   +(d>0.05?("+"+d.toFixed(2)+" left on your bench")
    :"Your lineup is already optimal")
   +'</div></div>';}
 return o+'</div>';}
function draw(){
 var h=document.getElementById("kfmx");
 if(!h){h=document.createElement("div");h.id="kfmx";
  document.body.insertBefore(h,document.body.firstChild);}
 if(!T){h.innerHTML="";return;}
 var lv=EVS.filter(function(e){
  return e.st.state==="in";}).length;
 h.innerHTML='<h3 class="mxt">Week '+wk()
  +' matchups'+(lv?' &middot; '+lv+' live':'')+'</h3>'
  +'<div class="mxw">'
  +T.teams.map(card).join("")+'</div>';
 Array.prototype.forEach.call(
  h.querySelectorAll(".mxo"),function(b){
  b.addEventListener("click",function(){
   var id=b.getAttribute("data-id");
   OPEN[id]=!OPEN[id];draw();});});}
function tick(){
 if(document.hidden){setTimeout(tick,30000);return;}
 refresh().then(function(){draw();
  setTimeout(tick,30000);})
 .catch(function(e){
  console.log("matchup: "+e.message);
  setTimeout(tick,60000);});}
function boot(){
 J("_teams.json").then(function(d){T=d;draw();
  return refresh();}).then(function(){draw();tick();})
 .catch(function(e){console.log("matchup boot: "+e.message);});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",
  function(){setTimeout(boot,500);});}
else{setTimeout(boot,500);}})();