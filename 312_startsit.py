import re

JS = r'''(function(){
var QR=null,TC=null,PJ=null,API="https://api.sleeper.app/v1/";
var ELIG={QB:["QB"],RB:["RB"],WR:["WR"],TE:["TE"],K:["K"],
 DEF:["DEF","DST"],DST:["DEF","DST"],
 FLEX:["RB","WR","TE"],WRRB_FLEX:["RB","WR"],
 REC_FLEX:["WR","TE"],SUPER_FLEX:["QB","RB","WR","TE"]};
function q(i){return document.getElementById(i);}
function esc(s){return String(s==null?"":s).replace(
 /[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",
 ">":"&gt;",'"':"&quot;"}[c];});}
function J(u){return fetch(u).then(function(r){
 if(!r.ok)throw new Error("HTTP "+r.status);
 return r.json();});}
function qarr(p){return (QR&&(QR[p]||QR.WR))||null;}
function pct(g,p,i){var a=qarr(p);
 return a?g*a[i]:g;}
function pwin(ga,pa,gb,pb,n){
 var A=qarr(pa),B=qarr(pb);
 if(!A||!B)return 0.5;
 var w=0,i,x,y;
 for(i=0;i<n;i++){
  x=ga*A[(Math.random()*A.length)|0];
  y=gb*B[(Math.random()*B.length)|0];
  if(x>y)w++;else if(x===y)w+=0.5;}
 return w/n;}

function optimize(players,slots){
 var used={},out=[],order=slots.slice();
 order.sort(function(a,b){
  return (ELIG[a]||[a]).length-(ELIG[b]||[b]).length;});
 order.forEach(function(s){
  var ok=ELIG[s]||[s],best=null,bi=-1;
  players.forEach(function(p,i){
   if(used[i])return;
   if(ok.indexOf(p.ps)<0)return;
   if(!best||p.ppg>best.ppg){best=p;bi=i;}});
  if(best){used[bi]=1;out.push({slot:s,p:best});}
  else{out.push({slot:s,p:null});}});
 var bench=players.filter(function(p,i){return !used[i];});
 bench.sort(function(a,b){return b.ppg-a.ppg;});
 return {start:out,bench:bench};}

var OPTL=null,OPTR=null;
function optRender(rid){
 var host=q("optBody");
 if(!host||!OPTL)return;
 var me=null,i;
 for(i=0;i<OPTR.length;i++)
  if(OPTR[i].roster_id===rid)me=OPTR[i];
 if(!me){host.innerHTML=
  '<div class="gvmut">roster not found</div>';return;}
 var slots=(OPTL.roster_positions||[]).filter(function(s){
  return s!=="BN"&&s!=="IR"&&s!=="TAXI";});
 var pl=[],miss=0;
 (me.players||[]).forEach(function(id){
  var v=PJ&&PJ[id];
  if(v){pl.push({id:id,nm:v.nm,
   ps:(v.ps==="DST"?"DEF":v.ps),tm:v.tm,ppg:v.ppg||0});}
  else{miss++;}});
 if(!pl.length){host.innerHTML=
  '<div class="gvmut">no projections matched this roster'
  +'</div>';return;}
 var r=optimize(pl,slots),tot=0;
 r.start.forEach(function(x){if(x.p)tot+=x.p.ppg;});
 var h='<div class="ssrow ssh"><span>Slot</span>'
  +'<b>Player</b><u>Proj</u></div>';
 r.start.forEach(function(x){
  h+='<div class="ssrow"><span>'+esc(x.slot)+'</span><b>'
   +(x.p?esc(x.p.nm)+' <em>'+esc(x.p.ps+" "+x.p.tm)
   +'</em>':'<em>empty</em>')+'</b><u>'
   +(x.p?x.p.ppg.toFixed(1):"-")+'</u></div>';});
 h+='<div class="sstot">Projected total<b>'
  +tot.toFixed(1)+'</b></div>';
 if(r.bench.length){
  h+='<h4>Bench</h4>';
  r.bench.slice(0,8).forEach(function(p){
   h+='<div class="ssrow dim"><span>BN</span><b>'
    +esc(p.nm)+' <em>'+esc(p.ps+" "+p.tm)
    +'</em></b><u>'+p.ppg.toFixed(1)+'</u></div>';});
  h+='<p class="note">Best bench player projects '
   +r.bench[0].ppg.toFixed(1)+' per week.'
   +(miss?' '+miss+' rostered players had no projection '
   +'and were skipped.':'')+'</p>';}
 host.innerHTML=h;}

function optLoad(){
 var id=q("optLid").value.trim();
 if(!id)return q("optOut").innerHTML=
  '<div class="gvmut">enter a league ID, or load one on '
  +'the League tab first</div>';
 q("optOut").innerHTML='<div class="gvmut">loading...</div>';
 Promise.all([J(API+"league/"+id),
  J(API+"league/"+id+"/rosters"),
  J(API+"league/"+id+"/users")])
 .then(function(x){
  OPTL=x[0];OPTR=x[1];
  var U=x[2],un={},i;
  for(i=0;i<U.length;i++)un[U[i].user_id]=
   (U[i].metadata&&U[i].metadata.team_name)
   ||U[i].display_name;
  var h='<div class="ssteam"><span>Your team</span>'
   +'<select id="optTeam">';
  OPTR.forEach(function(r){
   h+='<option value="'+r.roster_id+'">'
    +esc(un[r.owner_id]||("roster "+r.roster_id))
    +'</option>';});
  h+='</select><span class="dim2">'+esc(OPTL.name||"")
   +'</span></div><div id="optBody"></div>';
  q("optOut").innerHTML=h;
  var sel=q("optTeam");
  sel.addEventListener("change",function(){
   optRender(parseInt(sel.value,10));});
  optRender(parseInt(sel.value,10));})
 .catch(function(e){q("optOut").innerHTML=
  '<div class="gvmut">could not load: '+esc(e.message)
  +'</div>';});}

function ssFind(s){
 if(!TC)return [];
 s=s.trim().toLowerCase();
 if(s.length<2)return [];
 return TC.filter(function(x){
  return x.n.toLowerCase().indexOf(s)>=0;}).slice(0,7);}
function ssSug(side){
 var box=q("ssS"+side),inp=q("ssI"+side);
 box.innerHTML=ssFind(inp.value).map(function(x){
  return '<div class="tcsug" data-n="'+esc(x.n)
  +'" data-side="'+side+'"><b>'+esc(x.n)+'</b><span>'
  +esc(x.p+" "+x.t)+'</span><u>'+x.g.toFixed(1)
  +'</u></div>';}).join("");}
var SSA=null,SSB=null;
function ssDraw(){
 var o=q("ssOut");
 if(!SSA||!SSB)return o.innerHTML=
  '<div class="gvmut">pick two players to compare</div>';
 var p=pwin(SSA.g,SSA.p,SSB.g,SSB.p,4000);
 var win=p>=0.5?SSA:SSB,pc=p>=0.5?p:1-p;
 var conf=pc>=0.65?"clear":(pc>=0.56?"lean":"coin flip");
 function card(x){
  return '<div class="sscard"><h5>'+esc(x.n)+'</h5>'
   +'<span>'+esc(x.p+" "+x.t)+'</span>'
   +'<div class="ssnum">'+x.g.toFixed(1)+'</div>'
   +'<div class="ssfc">floor '+pct(x.g,x.p,9).toFixed(1)
   +' &middot; ceiling '+pct(x.g,x.p,89).toFixed(1)
   +'</div></div>';}
 o.innerHTML='<div class="ssvs">'+card(SSA)
  +'<i>vs</i>'+card(SSB)+'</div>'
  +'<div class="ssverdict '+(conf==="coin flip"?"even":"go")
  +'">Start <b>'+esc(win.n)+'</b> &mdash; '
  +(100*pc).toFixed(0)+'% of weeks</div>'
  +'<p class="note">This is a <b>'+conf+'</b>. The number '
  +'comes from simulating both players 4,000 times against '
  +'the real week-to-week distribution for their position, '
  +'not from comparing averages. Even a player projected '
  +'twice as high only wins about 3 weeks in 4 &mdash; '
  +'weekly variance is enormous, and anything above 65% is '
  +'a strong call in fantasy.</p>';}

function boot(){
 if(!q("optOut")&&!q("ssOut"))return;
 J("_qr.json").then(function(d){QR=d;}).catch(function(){});
 J("_tc.json").then(function(d){TC=d;}).catch(function(){});
 J("_proj.json").then(function(d){PJ=d;}).catch(function(){});
 var lid=q("optLid");
 if(lid){
  try{lid.value=localStorage.getItem("shukie_lg")||"";}
  catch(e){}
  q("optGo").addEventListener("click",optLoad);
  if(lid.value)setTimeout(optLoad,500);}
 ["A","B"].forEach(function(s){
  var i=q("ssI"+s);
  if(!i)return;
  i.addEventListener("input",function(){ssSug(s);});
  i.addEventListener("blur",function(){
   setTimeout(function(){q("ssS"+s).innerHTML="";},170);});});
 var w=q("sswrap");
 if(w)w.addEventListener("mousedown",function(e){
  var t=e.target.closest?e.target.closest(".tcsug"):null;
  if(!t)return;
  var n=t.getAttribute("data-n"),s=t.getAttribute("data-side");
  var pl=TC.filter(function(x){return x.n===n;})[0];
  if(!pl)return;
  if(s==="A")SSA=pl;else SSB=pl;
  q("ssI"+s).value=pl.n;q("ssS"+s).innerHTML="";
  ssDraw();});
 console.log("start/sit + optimizer ready");}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",boot);}
else{setTimeout(boot,300);}})();'''
open("site/_ss.js", "w").write(JS)
print("wrote site/_ss.js (%d bytes)" % len(JS))

OPT = ('<section id="topt"><div class="pg">'
       '<h2>Lineup Optimizer</h2>'
       '<p class="sub">Reads your connected league\'s '
       'actual roster slots &mdash; superflex, TE premium, '
       'two-flex, whatever you play &mdash; and fills the '
       'best legal lineup from your roster.</p>'
       '<div class="ssbar"><input id="optLid" '
       'placeholder="Sleeper league ID"><button id="optGo" '
       'class="btn-blue">Optimize</button></div>'
       '<div id="optOut"></div></div></section>')
SST = ('<section id="tstart"><div class="pg" id="sswrap">'
       '<h2>Start / Sit</h2>'
       '<p class="sub">How often does one player actually '
       'outscore the other? Simulated against the real '
       'week-to-week distribution for each position, so '
       'the answer accounts for how wildly fantasy scoring '
       'swings.</p>'
       '<div class="tcgrid">'
       '<div class="tcside"><h3>Player A</h3>'
       '<div class="tcin"><input id="ssIA" '
       'placeholder="Search" autocomplete="off">'
       '<div class="tcsugbox" id="ssSA"></div></div></div>'
       '<div class="tcside"><h3>Player B</h3>'
       '<div class="tcin"><input id="ssIB" '
       'placeholder="Search" autocomplete="off">'
       '<div class="tcsugbox" id="ssSB"></div></div></div>'
       '</div><div id="ssOut"></div></div></section>')

H = open("vaporai.html").read()
n0 = len(H)
rx = re.compile(r"</?section\b", re.I)
for sid, body in [("topt", OPT), ("tstart", SST)]:
    m = re.search(r'<section id="%s"[^>]*>' % sid, H)
    assert m, "no section " + sid
    d, k = 0, m.start()
    while True:
        mm = rx.search(H, k)
        if H[mm.start():mm.start() + 2] == "</":
            d -= 1
            if d == 0:
                en = H.index(">", mm.start()) + 1
                break
        else:
            d += 1
        k = mm.end()
    H = H[:m.start()] + body + H[en:]
    print("  wrote %s" % sid)
TAG = '<script src="_ss.js"></script>'
H = H.replace(TAG, "")
mb = re.search(r"<body[^>]*>", H)
H = H[:mb.end()] + TAG + H[mb.end():]
assert "</script></body></html>" in H, "tail broken"
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
