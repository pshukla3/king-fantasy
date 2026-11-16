var API="https://api.sleeper.app/v1/";
var CDN="https://sleepercdn.com/";
var ESPN="https://site.api.espn.com/apis/site/v2/"+
 "sports/football/nfl/scoreboard?dates=";
var P=null,SK=null,SC=null,PM=null;
var ST=null,WK=1,TAB="mu",OPEN=null;
var SLOTS=[],FLEX={RB:1,WR:1,TE:1};
function $(i){return document.getElementById(i);}
function E(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;");}
function g(u){return fetch(u).then(function(r){
 if(!r.ok)throw new Error(r.status);
 return r.json();});}
function say(m){$("msg").innerHTML=m;}
function q(x){return x.ps==="DST"?"DEF":x.ps;}
function chip(z){return '<span class="pos '+z+'">'
 +z+'</span>';}
function face(id){
 return '<img class=hs src="'+CDN
  +'content/nfl/players/thumb/'+id+'.jpg" '
  +'onerror="this.style.visibility=\'hidden\'">';}
function av(a){
 return a?'<img class=av src="'+CDN+'avatars/thumbs/'
  +a+'">':'<span class=av></span>';}
function sch(tm,w){
 var d=(SC.sched[tm]||{})[w];
 return d?(d.at+" "+d.o+" &middot; "+d.t):"BYE";
}
function samp(z){var a=SK[z]||SK.QB;
 return a[(Math.random()*a.length)|0];}
function best(pool,wk){
 var used={},f=[],i,j;
 for(i=0;i<SLOTS.length;i++){
  var s=SLOTS[i],b=-1,bv=-1;
  for(j=0;j<pool.length;j++){
   if(used[j])continue;
   var d=pool[j];
   if(!d||d.by===wk)continue;
   var z=q(d);
   var m=(s==="FLEX")?!!FLEX[z]:(z===s);
   if(m&&d.ppg>bv){bv=d.ppg;b=j;}}
  if(b>=0){used[b]=1;f.push(pool[b]);}}
 return f;}
function sum(f){var t=0,i;
 for(i=0;i<f.length;i++)t+=f[i].ppg;
 return t;}
function wp(fa,fb,n){
 var w=0,i,j,a,b;
 for(i=0;i<n;i++){a=0;b=0;
  for(j=0;j<fa.length;j++)a+=fa[j].ppg*samp(q(fa[j]));
  for(j=0;j<fb.length;j++)b+=fb[j].ppg*samp(q(fb[j]));
  if(a>b)w++;}
 return w/n;}
function tab(t){
 TAB=t;OPEN=null;
 var b=document.querySelectorAll(".stab");
 for(var i=0;i<b.length;i++)
  b[i].className="stab"+
   (b[i].getAttribute("data-s")===t?" on":"");
 draw();}
function lgList(){
 try{return JSON.parse(
  localStorage.getItem("shukie_lgs")||"[]");}
 catch(e){return [];}}
function lgSave(o){
 var L=lgList(),i;
 for(i=0;i<L.length;i++){
  if(L[i].id===o.id){L[i]=o;
   try{localStorage.setItem("shukie_lgs",
    JSON.stringify(L));}catch(e){}
   return;}}
 L.push(o);
 try{localStorage.setItem("shukie_lgs",
  JSON.stringify(L));}catch(e){}}
function lgSwitch(){
 var L=lgList();
 var inp=document.getElementById("lid");
 if(!inp)return;
 var old=document.getElementById("lgsw");
 if(old)old.parentNode.removeChild(old);
 if(L.length<2)return;
 var cur="";
 try{cur=localStorage.getItem("shukie_lg")||"";}catch(e){}
 var d=document.createElement("div");
 d.id="lgsw";
 d.style.cssText="margin:10px 0;display:flex;gap:8px;"
  +"align-items:center;flex-wrap:wrap";
 var h='<span style="font-size:10px;letter-spacing:.08em;'
  +'text-transform:uppercase;color:#8b8d94">your leagues'
  +'</span>';
 L.forEach(function(x){
  var on=(String(x.id)===String(cur));
  h+='<button class="lgb" data-id="'+x.id+'" style="'
   +'background:'+(on?"#fff":"transparent")+';color:'
   +(on?"#0a0a0c":"#8b8d94")+';border:1px solid '
   +(on?"#fff":"rgba(255,255,255,.16)")+';border-radius:8px;'
   +'padding:6px 12px;font-size:12px;cursor:pointer;'
   +'font-weight:600">'+lgesc(x.name)+'</button>';});
 d.innerHTML=h;
 inp.parentNode.parentNode.insertBefore(
  d,inp.parentNode.nextSibling);
 d.addEventListener("click",function(e){
  var t=e.target;
  while(t&&t!==d&&!t.getAttribute("data-id"))t=t.parentNode;
  if(!t||t===d)return;
  inp.value=t.getAttribute("data-id");
  load();});}
function load(){
 var v=$("lid").value.trim();
 if(!v)return say("enter a league ID or username");
 try{localStorage.setItem("shukie_lg",v);}catch(e){}
 say("loading league...");
 Promise.resolve()
 .then(function(){
  if(/^\d{5,}$/.test(v))return v;
  return g(API+"user/"+encodeURIComponent(v))
   .then(function(u){return g(API+"user/"+u.user_id
    +"/leagues/nfl/2026");})
   .then(function(l){
    if(!l||!l.length)throw new Error("no 2026 leagues");
    return l[0].league_id;});})
 .then(function(id){
  var a=[g(API+"league/"+id),
   g(API+"league/"+id+"/rosters"),
   g(API+"league/"+id+"/users")],w;
  for(w=1;w<=14;w++)
   a.push(g(API+"league/"+id+"/matchups/"+w)
    .catch(function(){return [];}));
  return Promise.all(a);})
 .then(function(x){
  build(x[0],x[1],x[2],x.slice(3));})
 .catch(function(e){say("could not load: "+e.message);});}
function build(L,R,U,MM){
 SLOTS=(L.roster_positions||[]).filter(function(s){
  return s!=="BN"&&s!=="IR"&&s!=="TAXI";});
 lgSave({id:String(L.league_id),
  name:L.name||("league "+L.league_id),
  teams:L.total_rosters||0,
  ppr:((L.scoring_settings||{}).rec)});
 try{lgSwitch();}catch(e){}
 var un={},tn={},ava={},i,j,w;
 for(i=0;i<U.length;i++){
  un[U[i].user_id]=U[i].display_name;
  ava[U[i].user_id]=U[i].avatar;
  tn[U[i].user_id]=(U[i].metadata
   &&U[i].metadata.team_name)||U[i].display_name;}
 var T={},taken={};
 for(i=0;i<R.length;i++){
  var ids=R[i].players||[],pool=[];
  for(j=0;j<ids.length;j++){
   taken[ids[j]]=1;
   var d=P[ids[j]];
   if(d){d=JSON.parse(JSON.stringify(d));
    d.sid=ids[j];pool.push(d);}}
  T[R[i].roster_id]={rid:R[i].roster_id,
   nm:tn[R[i].owner_id]||("Roster "+R[i].roster_id),
   ow:un[R[i].owner_id]||"",
   av:ava[R[i].owner_id],pool:pool,
   start:R[i].starters||[],
   n:ids.length,hit:pool.length,ew:0,pf:0};}
 var WKS=[];
 for(w=0;w<MM.length;w++){
  var by={},rows=MM[w],gs=[];
  for(i=0;i<rows.length;i++){
   var k=rows[i].matchup_id;
   if(k===null||k===undefined)continue;
   (by[k]=by[k]||[]).push(rows[i].roster_id);}
  for(var k2 in by){
   if(by[k2].length!==2)continue;
   var a=by[k2][0],b=by[k2][1];
   var fa=best(T[a].pool,w+1),fb=best(T[b].pool,w+1);
   var p=wp(fa,fb,1000);
   T[a].ew+=p;T[b].ew+=1-p;
   T[a].pf+=sum(fa);T[b].pf+=sum(fb);
   gs.push({a:a,b:b,fa:fa,fb:fb,
    pa:sum(fa),pb:sum(fb),p:p});}
  WKS.push(gs);}
 var me=null;
 for(i=0;i<R.length;i++)
  if(R[i].owner_id&&un[R[i].owner_id]&&
     $("lid").value.trim().toLowerCase()===
     String(un[R[i].owner_id]).toLowerCase())
   me=R[i].roster_id;
 ST={L:L,T:T,WK:WKS,taken:taken,me:me||R[0].roster_id};
 var s=$("wk");s.innerHTML="";
 for(w=1;w<=WKS.length;w++)
  s.innerHTML+="<option value="+w+">Week "+w+"</option>";
 s.value=WK;
 s.onchange=function(){WK=parseInt(s.value,10);
  OPEN=null;draw();};
 var t=0,h=0;
 for(var r in T){t+=T[r].n;h+=T[r].hit;}
 say("<b>"+E(L.name)+"</b> &middot; "+L.total_rosters
  +" teams &middot; "+h+"/"+t+" players matched");
 $("app").style.display="block";
 draw();}
function prow(d,slot){
 var s=d?sch(d.tm,WK):"";
 var bye=d&&d.by===WK;
 return '<tr><td class=sl>'+(slot||"")+'</td>'
  +'<td class=fc>'+(d?face(d.sid):"")+'</td>'
  +'<td><b>'+(d?E(d.nm):"empty")+'</b> '
  +(d?chip(q(d)):"")+' <span class=dim>'
  +(d?E(d.tm):"")+'</span><div class=dim>'
  +(bye?"BYE week "+WK:s)+'</div></td>'
  +'<td class=r>'+(d?d.ppg.toFixed(2):"--")
  +'</td></tr>';}
function drawTeam(){
 var t=ST.T[ST.me],i,h="";
 var st=t.start||[],inb={};
 h='<div class=hd>'+av(t.av)+'<div><div class=tm>'
  +E(t.nm)+'</div><div class=dim>@'+E(t.ow)
  +'</div></div></div>';
 h+='<h3>Starters</h3><table>';
 for(i=0;i<st.length;i++){
  inb[st[i]]=1;
  var d=null,j;
  for(j=0;j<t.pool.length;j++)
   if(t.pool[j].sid===st[i])d=t.pool[j];
  h+=prow(d,SLOTS[i]||"FLEX");}
 h+='</table><h3>Bench</h3><table>';
 for(i=0;i<t.pool.length;i++)
  if(!inb[t.pool[i].sid])h+=prow(t.pool[i],"BN");
 h+='</table>';
 var f=best(t.pool,WK);
 h+='<div class=tot>optimal lineup <b>'
  +sum(f).toFixed(2)+'</b> projected points</div>';
 $("body").innerHTML=h;}
function drawPlayers(){
 var fl=$("pf").value,s=$("ps").value.toLowerCase();
 var rows=[],k;
 for(k in P){
  if(ST.taken[k])continue;
  var d=P[k];
  if(!d||!d.ppg)continue;
  if(fl&&q(d)!==fl)continue;
  if(s&&(d.nm+" "+d.tm).toLowerCase()
     .indexOf(s)<0)continue;
  d.sid=k;rows.push(d);}
 rows.sort(function(a,b){return b.ppg-a.ppg;});
 var h='<table><tr><th></th><th>Player</th>'
  +'<th class=r>Bye</th><th class=r>Proj</th>'
  +'<th class=r>VORP</th></tr>',i;
 for(i=0;i<rows.length&&i<200;i++){
  var d=rows[i];
  h+='<tr><td class=fc>'+face(d.sid)+'</td><td><b>'
   +E(d.nm)+'</b> '+chip(q(d))+' <span class=dim>'
   +E(d.tm)+'</span><div class=dim>'+sch(d.tm,WK)
   +'</div></td><td class=r>'+(d.by||"--")
   +'</td><td class=r>'+d.ppg.toFixed(2)
   +'</td><td class=r>'
   +(d.vorp==null?"--":d.vorp.toFixed(2))
   +'</td></tr>';}
 $("body").innerHTML=h+'</table><div class=dim>'
  +'free agents in your league, by our projection'
  +'</div>';}
function bar(p){
 return '<div class=bw><div class=bf style="width:'
  +Math.round(p*100)+'%"></div></div>';}
function card(m,i){
 var A=ST.T[m.a],B=ST.T[m.b];
 return '<div class=mc onclick="expand('+i+')">'
  +'<div class=side>'+av(A.av)+'<div class=tm>'
  +E(A.nm)+'</div><div class=dim>@'+E(A.ow)
  +'</div><div class=pj>'+m.pa.toFixed(2)+'</div>'
  +'</div><div class=mid>'+bar(m.p)+'<div class=pc>'
  +'<span>'+Math.round(m.p*100)+'%</span><span>vs</span>'
  +'<span>'+Math.round((1-m.p)*100)+'%</span></div>'
  +'</div><div class="side r">'+av(B.av)
  +'<div class=tm>'+E(B.nm)+'</div><div class=dim>@'
  +E(B.ow)+'</div><div class=pj>'+m.pb.toFixed(2)
  +'</div></div></div>';}
function expand(i){OPEN=(OPEN===i?null:i);draw();}
function detail(m){
 var n=Math.max(m.fa.length,m.fb.length),i,h="";
 h='<table class=cmp>';
 for(i=0;i<n;i++){
  var a=m.fa[i],b=m.fb[i];
  h+='<tr><td class=r>'+(a?a.ppg.toFixed(2):"--")
   +'</td><td class=lft>'+(a?E(a.nm):"")+'</td>'
   +'<td class=mid2>'+(a?chip(q(a)):(b?chip(q(b)):""))
   +'</td><td>'+(b?E(b.nm):"")+'</td>'
   +'<td class=r>'+(b?b.ppg.toFixed(2):"--")
   +'</td></tr>';}
 return h+'</table>';}
function drawAround(){
 var gs=ST.WK[WK-1]||[],i,h="";
 for(i=0;i<gs.length;i++){
  h+=card(gs[i],i);
  if(OPEN===i)h+='<div class=det>'+detail(gs[i])
   +'</div>';}
 $("body").innerHTML=h||'<p class=dim>no matchups</p>';}
function drawGame(){
 var gs=ST.WK[WK-1]||[],i,m=null;
 for(i=0;i<gs.length;i++)
  if(gs[i].a===ST.me||gs[i].b===ST.me)m=gs[i];
 if(!m)return $("body").innerHTML=
  '<p class=dim>no matchup this week</p>';
 $("body").innerHTML=card(m,0)+'<div class=det>'
  +detail(m)+'</div>';}
function drawScores(){
 var dts=(SC.dates[String(WK)]||[]),i;
 $("body").innerHTML='<p class=dim>loading games...</p>';
 Promise.all(dts.map(function(d){
  return g(ESPN+d).catch(function(){return {};});}))
 .then(function(res){
  var ev=[],h="";
  res.forEach(function(r){
   (r.events||[]).forEach(function(e){ev.push(e);});});
  h='<div class=two><div><h3>Game Center</h3>';
  if(!ev.length)h+='<p class=dim>no games listed</p>';
  ev.forEach(function(e){
   var c=(e.competitions||[{}])[0];
   var s=(c.status||{}).type||{};
   var cs=c.competitors||[];
   h+='<div class=gm><div class=dim>'
    +E(s.shortDetail||s.description||"")+'</div>';
   cs.forEach(function(x){
    h+='<div class=gr><span>'
     +E((x.team||{}).abbreviation)+'</span><b>'
     +E(x.score==null?"-":x.score)+'</b></div>';});
   h+='</div>';});
  h+='</div><div><h3>Fantasy scorers, week '+WK
   +'</h3><div id=lead><p class=dim>loading...'
   +'</p></div></div></div>';
  $("body").innerHTML=h;
  return g(API+"stats/nfl/regular/2026/"+WK);})
 .then(function(s){
  var G={QB:[],RB:[],WR:[],TE:[],K:[],DEF:[]},k;
  for(k in (s||{})){
   var v=s[k],p=PM[k]||P[k];
   var pt=v&&(v.pts_ppr!=null?v.pts_ppr:v.pts_std);
   if(!p||pt==null||pt<=0)continue;
   var z=p.p||p.ps;z=(z==="DST")?"DEF":z;
   if(G[z])G[z].push({n:p.n||p.nm,t:p.t||p.tm,
    v:pt,id:k});}
  var h="",z;
  for(z in G){
   G[z].sort(function(a,b){return b.v-a.v;});
   if(!G[z].length)continue;
   h+='<h4>'+z+'</h4><table>';
   G[z].forEach(function(x){
    h+='<tr><td class=fc>'+face(x.id)+'</td><td><b>'
     +E(x.n)+'</b> <span class=dim>'+E(x.t)
     +'</span></td><td class=r>'+Number(x.v).toFixed(2)
     +'</td></tr>';});
   h+='</table>';}
  $("lead").innerHTML=h||'<p class=dim>Players have '
   +'yet to play &mdash; week 1 kicks off Sep 9.</p>';})
 .catch(function(e){
  var l=$("lead");
  if(l)l.innerHTML='<p class=dim>stats unavailable: '
   +E(e.message)+'</p>';});}
function draw(){
 if(!ST)return;
 if(TAB==="tm")return drawTeam();
 if(TAB==="pl")return drawPlayers();
 if(TAB==="ar")return drawAround();
 if(TAB==="sc")return drawScores();
 return drawGame();}
Promise.all([g("_proj.json"),g("_shock.json"),
 g("_sched.json"),g("_pmap.json"),
 g(API+"state/nfl").catch(function(){return {week:1};})])
.then(function(x){
 P=x[0];SK=x[1];SC=x[2];PM=x[3];
 WK=Math.max(1,Math.min(14,x[4].week||1));
 var v="";try{v=localStorage.getItem("shukie_lg")||"";}
 catch(e){}
 if(v){$("lid").value=v;load();}
 else say("enter a Sleeper league ID or username");})
.catch(function(e){say("data load failed: "+e);});
$("go").addEventListener("click",load);
$("lid").addEventListener("keydown",function(e){
 if(e.key==="Enter")load();});
$("pf").addEventListener("change",draw);
$("ps").addEventListener("input",draw);
