(function(){
var M={"ing": {"feat": ["sd_t", "expt", "score_differential", "t", "half", "down", "ydstogo", "yardline_100", "to_diff", "is4", "spread_pos", "sp_t"], "mean": [-0.39306525447349394, 0.26487177213273533, -1.370542412723817, 1734.259877963389, 833.8997699309793, 1.989362433730119, 8.564594378313494, 51.42274244773432, -0.017086375912773833, 0.10166800040012004, 0.08187299939981994, 0.056299225705211564], "scale": [3.483149719567831, 0.273059944695964, 10.595631221459676, 1046.441531257699, 545.8664877215145, 1.0013445003462647, 4.118285219598734, 24.440129097128807, 0.8489033127463678, 0.3022112143762392, 6.351644555407928, 3.5822271303771407], "coef": [2.1762552027641977, 0.21129131698459308, 0.36451865307476067, 0.06248645577190701, -0.019099621040862623, -0.09035445530727261, -0.04307529919635926, -0.21167323040322505, 0.004810190521272994, -0.03275215699302853, 0.4661309404214379, 0.2725547566118369], "i": 0.028601212862961103}, "pre": {"i": -0.04232943277127542, "c": 0.14672491383177266}, "ot": 0.602};
var E2N={"LAR":"LA","WSH":"WAS","JAC":"JAX","AZ":"ARI"};
function nz(a){a=(a||"").toUpperCase();return E2N[a]||a;}
var SCH=null,QT=null,PM=null,PJ=null,BUSY=false;
function J(u){return fetch(u).then(function(r){
 if(!r.ok)throw new Error("HTTP "+r.status);
 return r.json();});}
function lg(z){return 1/(1+Math.exp(-z));}
function ev(m,f){if(!m||!m.feat)return 0.5;var z=m.i,i;for(i=0;i<m.feat.length;i++){z+=m.coef[i]*(((f[m.feat[i]]||0)-m.mean[i])/m.scale[i]);}return lg(z);}
function evpre(sp){return lg(M.pre.i+M.pre.c*(sp||0));}
function ft(sd,t,y,dn,ds,sp){t=Math.max(1,t);
 return {sd_t:sd/Math.sqrt(t/60+1),
  expt:Math.exp(-4*t/3600),score_differential:sd,
  t:t,half:t<=1800?t:t-1800,down:dn||1,
  ydstogo:ds||10,yardline_100:(y==null?50:y),
  to_diff:0,is4:(dn===4?1:0),spread_pos:sp||0,
  sp_t:(sp||0)*(t/3600)};}
function esc(x){return String(x==null?"":x).replace(
 /[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",
 ">":"&gt;","\"":"&quot;"}[c];});}
function pad(n){return (n<10?"0":"")+n;}
function secs(clock,per){
 var p=String(clock||"0:00").split(":");
 var s=(parseInt(p[0],10)||0)*60+(parseInt(p[1],10)||0);
 var q=Math.min(4,per||1);
 return s+(4-q)*900;}

function hx(c){c=String(c||"").replace("#","");
 if(c.length===3)c=c[0]+c[0]+c[1]+c[1]+c[2]+c[2];
 if(c.length!==6)return [128,128,128];
 var n=parseInt(c,16);
 return [(n>>16)&255,(n>>8)&255,n&255];}
function cdist(a,b){var x=hx(a),y=hx(b);
 return Math.sqrt(2*Math.pow(x[0]-y[0],2)
  +4*Math.pow(x[1]-y[1],2)+3*Math.pow(x[2]-y[2],2));}
function lift(c){var x=hx(c);
 function f(v){return Math.max(0,Math.min(255,
  Math.round(v*0.4+140)));}
 return "#"+[f(x[0]),f(x[1]),f(x[2])].map(function(v){
  return ("0"+v.toString(16)).slice(-2);}).join("");}
function tlogo(ab){return ab?
 "https://a.espncdn.com/i/teamlogos/nfl/500/"+ab+".png":"";}
function field(y,dir,ha,aa,hc,ac,dn,dist){
 var i,g="",x;
 for(i=1;i<20;i++){x=10+i*5;
  g+='<line x1="'+x+'" y1="0" x2="'+x+'" y2="53.3" '
   +'stroke="#fff" stroke-width="'+(i%2===0?".3":".16")
   +'" opacity="'+(i%2===0?".5":".26")+'"/>';}
 var nm=[10,20,30,40,50,40,30,20,10];
 for(i=0;i<nm.length;i++){x=20+i*10;
  g+='<text x="'+x+'" y="15.5" fill="#fff" opacity=".55" '
   +'font-size="5.6" font-weight="700" text-anchor="middle" '
   +'font-family="Arial,sans-serif">'+nm[i]+'</text>'
   +'<text x="'+x+'" y="41.5" fill="#fff" opacity=".55" '
   +'font-size="5.6" font-weight="700" text-anchor="middle" '
   +'font-family="Arial,sans-serif" transform="rotate(180 '
   +x+' 39.6)">'+nm[i]+'</text>';}
 for(i=1;i<100;i++){x=10+i;
  if(i%5===0)continue;
  g+='<line x1="'+x+'" y1="20.6" x2="'+x+'" y2="22.1" '
   +'stroke="#fff" stroke-width=".13" opacity=".38"/>'
   +'<line x1="'+x+'" y1="31.2" x2="'+x+'" y2="32.7" '
   +'stroke="#fff" stroke-width=".13" opacity=".38"/>';}
 var bx=10+(dir>0?(100-y):y);
 var fy=Math.max(0,y-(dist||10));
 var fx=10+(dir>0?(100-fy):fy);
 var los='<line x1="'+bx+'" y1="0" x2="'+bx+'" y2="53.3" '
  +'stroke="#2f6bff" stroke-width=".7"/>';
 var fd=(dist&&fy>0&&fy<100)
  ?'<line x1="'+fx+'" y1="0" x2="'+fx+'" y2="53.3" '
   +'stroke="#ffd400" stroke-width=".7"/>':'';
 return '<svg viewBox="0 0 120 53.3" class="gvfld">'
 +'<defs><linearGradient id="turf" x1="0" y1="0" x2="0" '
 +'y2="1"><stop offset="0" stop-color="#1d6b32"/>'
 +'<stop offset="1" stop-color="#155126"/></linearGradient>'
 +'</defs>'
 +'<rect x="0" y="0" width="120" height="53.3" '
 +'fill="url(#turf)"/>'
 +'<rect x="10" y="0" width="10" height="53.3" '
 +'fill="#fff" opacity=".035"/>'
 +'<rect x="30" y="0" width="10" height="53.3" '
 +'fill="#fff" opacity=".035"/>'
 +'<rect x="50" y="0" width="10" height="53.3" '
 +'fill="#fff" opacity=".035"/>'
 +'<rect x="70" y="0" width="10" height="53.3" '
 +'fill="#fff" opacity=".035"/>'
 +'<rect x="90" y="0" width="10" height="53.3" '
 +'fill="#fff" opacity=".035"/>'
 +'<rect x="0" y="0" width="10" height="53.3" fill="'
 +(ac||"#16241a")+'"/>'
 +'<rect x="110" y="0" width="10" height="53.3" fill="'
 +(hc||"#16241a")+'"/>'
 +g
 +'<line x1="10" y1="0" x2="10" y2="53.3" stroke="#fff" '
 +'stroke-width=".5"/>'
 +'<line x1="110" y1="0" x2="110" y2="53.3" stroke="#fff" '
 +'stroke-width=".5"/>'
 +'<rect x="0" y="0" width="120" height="53.3" fill="none" '
 +'stroke="#fff" stroke-width=".5" opacity=".8"/>'
 +fd+los
 +'<circle cx="'+bx+'" cy="26.6" r="1.9" fill="#fff" '
 +'stroke="#0a0a0c" stroke-width=".4"/>'
 +'<text x="5" y="29.5" fill="#fff" opacity=".9" '
 +'font-size="5" font-weight="800" text-anchor="middle" '
 +'font-family="Arial,sans-serif" transform="rotate(-90 5 '
 +'26.6)">'+esc(aa)+'</text>'
 +'<text x="115" y="29.5" fill="#fff" opacity=".9" '
 +'font-size="5" font-weight="800" text-anchor="middle" '
 +'font-family="Arial,sans-serif" transform="rotate(90 115 '
 +'26.6)">'+esc(ha)+'</text></svg>';}
function curve(pts,col){
 if(!pts.length)return '<div class="gvmut">'
  +'win probability chart appears once the game starts</div>';
 var w=560,h=110,d="",i;
 for(i=0;i<pts.length;i++){
  var x=w*i/Math.max(1,pts.length-1);
  var y=h*(1-pts[i]);
  d+=(i?"L":"M")+x.toFixed(1)+" "+y.toFixed(1);}
 return '<svg viewBox="0 0 '+w+' '+h+'" class="gvcrv">'
 +'<line x1="0" y1="'+(h/2)+'" x2="'+w+'" y2="'+(h/2)+'" '
 +'stroke="#2a2c30" stroke-width="1"/>'
 +'<path d="'+d+'" fill="none" stroke="'+(col||"#8ab4f8")+'" '
 +'stroke-width="2"/></svg>';}

function qtab(sd,q){
 if(!QT)return "";
 var rows="",k,tb=QT.table||QT;
 for(k in tb){
  var v=tb[k];
  if(typeof v==="number"){
   rows+='<tr><td>'+esc(k)+'</td><td>'
   +(100*v).toFixed(1)+'%</td></tr>';}}
 if(!rows)return "";
 return '<h4>Empirical, 3,018 games</h4>'
 +'<table class="gvqt">'+rows+'</table>';}


function histBlock(sm,a,h){
 var lf=sm&&sm.lastFiveGames;
 if(!lf||!lf.teams)return "";
 var out="",i,k;
 for(i=0;i<lf.teams.length;i++){
  var t=lf.teams[i],ab=nz(((t.team||{}).abbreviation)||"");
  var ev2=(t.events||[]).slice(0,5),rows="";
  for(k=0;k<ev2.length;k++){
   var g=ev2[k];
   rows+='<div class="gvrp"><b>'+esc(g.opponent&&
    g.opponent.abbreviation?((g.atVs||"")+" "+
    g.opponent.abbreviation):"-")+'</b><span>'
    +esc((g.gameResult||"")+" "+(g.score||""))
    +'</span></div>';}
  if(rows)out+='<h4>'+esc(ab)+' last 5</h4>'+rows;}
 return out;}
function shell(){
 if(document.getElementById("gvx"))return;
 var d=document.createElement("div");
 d.id="gvx";d.className="gvov";
 d.innerHTML='<div class="gvbx"><button class="gvcl" '
 +'id="gvclose">close</button><div id="gvbody"></div></div>';
 document.body.appendChild(d);
 d.addEventListener("click",function(e){
  if(e.target===d)hide();});
 document.getElementById("gvclose")
  .addEventListener("click",hide);
 document.addEventListener("keydown",function(e){
  if(e.key==="Escape")hide();});}
function hide(){var d=document.getElementById("gvx");
 if(d)d.classList.remove("on");}
function show(h){shell();
 document.getElementById("gvbody").innerHTML=h;
 document.getElementById("gvx").classList.add("on");}

function findDate(a,h){
 if(!SCH||!SCH.sched)return null;
 var t=SCH.sched[h],w;
 if(t){for(w in t){if(t[w].o===a&&t[w].at==="vs")
  return t[w].d;}}
 t=SCH.sched[a];
 if(t){for(w in t){if(t[w].o===h&&t[w].at==="@")
  return t[w].d;}}
 return null;}

function open2(a,h,meta){
 if(BUSY)return;BUSY=true;
 show('<div class="gvhd"><b>'+esc(a)+' @ '+esc(h)
  +'</b><span>'+esc(meta)+'</span></div>'
  +'<div class="gvmut">loading...</div>');
 var d=findDate(a,h);
 if(!d){render(a,h,meta,null,null);BUSY=false;return;}
 var ds=d.replace(/-/g,"");
 J("https://site.api.espn.com/apis/site/v2/sports/"
  +"football/nfl/scoreboard?dates="+ds)
 .then(function(sb){
  var ev=(sb.events||[]),i,found=null;
  for(i=0;i<ev.length;i++){
   var c=(ev[i].competitions||[])[0];if(!c)continue;
   var t=(c.competitors||[]).map(function(x){
    return nz((x.team||{}).abbreviation);});
   if(t.indexOf(a)>=0&&t.indexOf(h)>=0){found=ev[i];break;}}
  if(!found){render(a,h,meta,null,null);BUSY=false;return;}
  return J("https://site.api.espn.com/apis/site/v2/sports/"
   +"football/nfl/summary?event="+found.id)
   .then(function(sm){render(a,h,meta,found,sm);BUSY=false;});})
 .catch(function(e){
  render(a,h,meta,null,null);BUSY=false;});}

function fsc(sm){
 var P={passingYards:0.04,passingTouchdowns:4,
  interceptions:-2,rushingYards:0.1,
  rushingTouchdowns:6,receptions:1,receivingYards:0.1,
  receivingTouchdowns:6,fumblesLost:-2};
 var C={passing:1,rushing:1,receiving:1,fumbles:1};
 var out={},tms=((sm||{}).boxscore||{}).players||[];
 tms.forEach(function(t){
  var ab=((t.team||{}).abbreviation||"");
  (t.statistics||[]).forEach(function(c){
   var cn=String(c.name||"").toLowerCase();
   var ks=c.keys||[];
   if(!C[cn]&&cn!=="kicking")return;
   (c.athletes||[]).forEach(function(a){
    var at=a.athlete||{},nm=at.displayName;
    if(!nm)return;
    var ps=((at.position||{}).abbreviation)||"";
    var r=out[nm]||(out[nm]={tm:ab,ps:ps,p:0});
    if(ps&&!r.ps)r.ps=ps;
    var stt=a.stats||[],i;
    for(i=0;i<ks.length;i++){
     var k=ks[i],v=parseFloat(stt[i]);
     if(isNaN(v))continue;
     if(cn==="kicking"){
      if(k==="totalKickingPoints")r.p+=v;}
     else if(P[k]!==undefined)r.p+=v*P[k];}});});});
 return out;}
function fbox(sm,a,h,al,hl,ac,hc){
 var S=fsc(sm),ks=Object.keys(S),g={};
 if(!ks.length)return"";
 ks.forEach(function(n){var r=S[n];
  if(Math.abs(r.p)<0.05)return;
  var t=nz(r.tm);(g[t]=g[t]||[]).push(
   {n:n,ps:r.ps,p:r.p});});
 var blk=function(ab,lg,col){
  var z=(g[nz(ab)]||[]).slice().sort(
   function(x,y){return y.p-x.p;}).slice(0,8);
  if(!z.length)return"";
  var o='<div class="gvfp"><h5 style="color:'+col+'">'
   +(lg?'<img src="'+tlogo(lg)+'" alt="">':'')
   +esc(ab)+'</h5>';
  z.forEach(function(x){
   o+='<div class="gvrp"><b>'+esc(x.n)+'</b><span>'
    +esc(x.ps)+' &middot; '+x.p.toFixed(1)
    +'</span></div>';});
  return o+'</div>';};
 var body=blk(a,al,ac)+blk(h,hl,hc);
 if(!body)return"";
 return '<h4>Live fantasy points</h4>'
  +'<div class="gvfw">'+body+'</div>';}
function render(a,h,meta,evt,sm){
 var sp=0,hasSp=false,st="",series=[],ply=[];
 var ac="#7a7d82",hc="#8ab4f8",hist="",hlogo="",alogo="";
 var sd=0,tl=3600,y=75,dn=1,ds=10,posHome=true,live=false,fin=false;
 if(evt){var c=(evt.competitions||[])[0]||{};
  st=((evt.status||{}).type||{}).shortDetail||"";
  var od=(c.odds||[])[0];
  if(od&&typeof od.spread==="number"){sp=od.spread;hasSp=true;}
  live=(((evt.status||{}).type||{}).state==="in");fin=(((evt.status||{}).type||{}).state==="post");
  var cp=(c.competitors||[]),hA=null,aA=null;
  for(var ci=0;ci<cp.length;ci++){
   var tm=(cp[ci].team||{});
   var cl=tm.color?("#"+tm.color):null;
   var al=tm.alternateColor?("#"+tm.alternateColor):null;
   var ab=String(tm.abbreviation||"").toLowerCase();
   if(cp[ci].homeAway==="home"){
    if(cl)hc=cl;hA=al;hlogo=ab;}
   else{if(cl)ac=cl;aA=al;alogo=ab;}}
  if(cdist(hc,ac)<110){
   if(aA&&cdist(hc,aA)>=110){ac=aA;}
   else if(hA&&cdist(hA,ac)>=110){hc=hA;}
   else{ac=lift(ac);}}}
 var hAdv=hasSp?(-sp):0;
 if(sm&&sm.drives){
  var prev=(sm.drives.previous||[]).slice(),i,k;
  if(sm.drives.current)prev.push(sm.drives.current);
  for(i=0;i<prev.length;i++){
   var pl=(prev[i].plays||[]);
   for(k=0;k<pl.length;k++){
    var p=pl[k],s=p.start||{};
    if(!s.down)continue;
    var per=((p.period||{}).number)||1;
    var tt=secs(((p.clock||{}).displayValue),per);
    var ph=String(((s.team||{}).id))===String(
     ((((sm.header||{}).competitions||[])[0]||{})
      .competitors||[]).filter(function(x){
      return x.homeAway==="home";}).map(function(x){
      return x.id;})[0]);
    var pd=(p.homeScore||0)-(p.awayScore||0);
    var msd=ph?pd:-pd;
    var msp=ph?hAdv:-hAdv;
    var f=ft(msd,tt,(s.yardsToEndzone==null?50:
     s.yardsToEndzone),s.down,s.distance,msp);
    var w=ev(M.ing,f);
    series.push(ph?w:1-w);
    ply.push({t:p.text||"",q:per,
     c:((p.clock||{}).displayValue)||"",
     w:(ph?w:1-w),dn:s.down,ds:s.distance});
    sd=msd;tl=tt;y=(s.yardsToEndzone==null?50:
     s.yardsToEndzone);dn=s.down;ds=s.distance;posHome=ph;}}}
 var hw;
 if(series.length){hw=series[series.length-1];}
 else{hw=evpre(hAdv);}
 var aw=1-hw;
 var spTxt=hasSp?((sp<0?h:a)+" by "+Math.abs(sp).toFixed(1))
  :"line unavailable";
 var mdl=series.length?"in-game (mkt2)":"pregame (line)";
 function ord(n){return n===1?"1st":n===2?"2nd":
  n===3?"3rd":"4th";}
 var recent=ply.slice(-16);
 var pl2=recent.map(function(p,i){
  var prev=i>0?recent[i-1].w:p.w;
  var dw=(p.w-prev)*100;
  var cls=Math.abs(dw)>=4?(dw>0?"up":"dn"):"";
  var big=/touchdown|interception|fumble|safety/i
   .test(p.t)?" big":"";
  return '<div class="gvpl'+big+'">'
   +'<span>Q'+p.q+' '+esc(p.c)+'</span>'
   +(p.dn?'<i>'+ord(p.dn)+' &amp; '+(p.ds||10)+'</i>':'')
   +'<u>'+esc(p.t)+'</u>'
   +'<b class="'+cls+'">'+(dw>=0?"+":"")
   +dw.toFixed(1)+'%</b></div>';})
  .reverse().join("")
  ||'<div class="gvmut">Play-by-play appears once the '
  +'game kicks off. Each play will show what it did to '
  +'the win probability.</div>';
 hist=histBlock(sm,a,h);

 var roster="";
 if(PJ){var A2=[],H2=[],id,q;
  for(id in PJ){q=PJ[id];
   if(!q||!q.tm)continue;
   var tm=nz(q.tm);
   if(tm===a){A2.push(q);}
   else if(tm===h){H2.push(q);}}
  var srt=function(z){
   z.sort(function(x,y){
    return (y.ppg||0)-(x.ppg||0);});
   return z.slice(0,9);};
  var blk=function(z,ab,lg,col){
   if(!z.length)return "";
   var o='<div class="gvteam"><h5 style="border-color:'
    +col+'">'
    +(lg?'<img src="'+tlogo(lg)+'" alt="">':'')
    +esc(ab)+'</h5>';
   z.forEach(function(x){
    o+='<div class="gvrp"><b>'+esc(x.nm)+'</b><span>'
     +esc(x.ps)+' &middot; '+(x.ppg||0).toFixed(1)
     +'</span></div>';});
   return o+'</div>';};
  roster=blk(srt(A2),a,alogo,ac)+blk(srt(H2),h,hlogo,hc);}
 if(fin&&evt){var _c=(evt.competitions||[])[0]||{};
  var _cp=_c.competitors||[],_hs=0,_as=0,_i;
  for(_i=0;_i<_cp.length;_i++){
   var _s=parseInt(_cp[_i].score,10)||0;
   if(_cp[_i].homeAway==="home")_hs=_s;else _as=_s;}
  hw=(_hs>_as)?1:((_hs<_as)?0.5:0.5);
  if(_hs<_as)hw=0;
  aw=1-hw;spTxt="final";mdl="final score";}
 show('<div class="gvhd"><b>'
  +(alogo?'<img class="gvlg" src="'+tlogo(alogo)+'" alt="">':'')
  +esc(a)+'<em>@</em>'
  +(hlogo?'<img class="gvlg" src="'+tlogo(hlogo)+'" alt="">':'')
  +esc(h)+'</b>'
  +'<span>'+esc(st||meta)+'</span></div>'
  +'<div class="gvwp"><div class="gvt"><i>'+esc(a)+'</i>'
  +'<b>'+(100*aw).toFixed(1)+'%</b></div>'
  +'<div class="gvbar"><i style="width:'+(100*aw).toFixed(1)+'%;background:'+ac+'"></i>'+'<i style="width:'+(100*hw).toFixed(1)+'%;background:'+hc+'"></i></div>'
  +'<div class="gvt"><i>'+esc(h)+'</i><b>'
  +(100*hw).toFixed(1)+'%</b></div></div>'
  +'<div class="gvsub">'+esc(spTxt)+' &middot; model: '
  +esc(mdl)+'</div>'
  +field(y,posHome?1:-1,h,a,hc,ac,dn,ds)
  +'<div class="gvgrid"><div><h4>Win probability</h4>'
  +curve(series,hc)+'<h4>Play by play</h4>'+'<div class="gvpbx">'+pl2+'</div>'+fbox(sm,a,h,alogo,hlogo,ac,hc)+'</div>'
  +'<div>'+qtab(sd,tl)
  +(roster?'<h4>Projected ppg</h4>'+roster:"")+hist
  +'</div></div>');}

function boot(){
 var cards=document.querySelectorAll(".sbc");
 if(!cards.length)return;
 Promise.all([
  J("_sched.json").then(function(d){SCH=d;})
   .catch(function(){}),
  J("_qtr.json").then(function(d){QT=d;})
   .catch(function(){}),
  J("_pmap.json").then(function(d){PM=d;})
   .catch(function(){}),
  J("_proj.json").then(function(d){PJ=d;})
   .catch(function(){})
 ]).then(function(){
  Array.prototype.forEach.call(cards,function(c){
   var im=c.querySelectorAll(".sbrow img");
   if(im.length<2)return;
   var a=nz(im[0].getAttribute("alt"));
   var h=nz(im[1].getAttribute("alt"));
   var mt=(c.querySelector(".sbmeta")||{}).textContent||"";
   c.style.cursor="pointer";
   c.setAttribute("title","win probability");
   c.addEventListener("click",function(){
    open2(a,h,mt);});});
  console.log("game view wired to "+cards.length+" games");});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",boot);}
else{boot();}
window.KFgameBoot=boot;
})();