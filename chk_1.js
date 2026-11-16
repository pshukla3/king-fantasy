

function $(i){return document.getElementById(i);}
function E(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;");}
function n1(v){return v==null?"--":Number(v).toFixed(1);}

function go(t){
 var s=document.querySelectorAll("section"),i;
 for(i=0;i<s.length;i++){s[i].className="";}
 var b=document.querySelectorAll("nav button");
 for(i=0;i<b.length;i++){b[i].className="";}
 var el=$(t); if(el){el.className="on";}
 var bt=document.querySelector("nav button[data-t="+t+"]");
 if(bt){bt.className="on";}
}
var nb=document.querySelectorAll("nav button");
for(var i=0;i<nb.length;i++){
 (function(b){b.addEventListener("click",function(){
   go(b.getAttribute("data-t"));});})(nb[i]);
}

function safe(fn,name){
 try{fn();}catch(e){
  console.log("ERR "+name+": "+e.message);
  var el=$(name);
  if(el&&!el.innerHTML){
   el.innerHTML='<p class="err">'+E(name)+
    ' failed: '+E(e.message)+'</p>';}
 }
}

function drawHome(){
 var m=D.meta||{};
 var h='<h2>Engine status</h2><div class="cards">';
 var k=[["Players ranked",m.board],
        ["Teams",m.teams],
        ["Depth-chart players",m.players],
        ["Injuries tracked",m.injured],
        ["Coaches on file",(m.coaches||0)+" / 32"],
        ["News articles",(D.news&&D.news.articles?
          D.news.articles.length:0)]];
 for(var i=0;i<k.length;i++){
  h+='<div class="card"><div class="kpi">'+k[i][1]+
     '</div><div class="kpi-l">'+k[i][0]+'</div></div>';}
 h+='</div><p class="note">Every number here is measured '+
  'from nflverse data under your league\u2019s real Sleeper '+
  'scoring keys. Year-over-year reliability: WR 0.765, '+
  'TE 0.733, RB 0.709, QB 0.560, DST 0.265.</p>';
 $("home").innerHTML=h;
}

function drawRosters(){
 var T=D.teams,ks=Object.keys(T).sort(),h='';
 h+='<h2>Team depth charts</h2><div class="cards">';
 for(var i=0;i<ks.length;i++){
  var t=T[ks[i]],c=t.coach||{};
  h+='<div class="card"><div class="tm"><b>'+E(ks[i])+
     '</b></div><div class="kpi-l">Head coach</div><div>'+
     (c.head_coach?E(c.head_coach):'<span class="err">'+
      'not on file</span>')+'</div>';
  var inj=t.injuries||[];
  h+='<div class="kpi-l" style="margin-top:9px">Injuries '+
     inj.length+'</div>';
  for(var j=0;j<inj.length&&j<4;j++){
   h+='<div class="hurt">'+E(inj[j].name)+' '+
      E(inj[j].status)+'</div>';}
  h+='</div>';
 }
 h+='</div>';
 $("rosters").innerHTML=h;
}

function drawBoard(){
 var q=($("fq")?$("fq").value:"").toLowerCase().trim();
 var p=$("fpos")?$("fpos").value:"ALL";
 var r=D.board,out=[],i;
 for(i=0;i<r.length;i++){
  if(p!=="ALL"&&r[i].ps!==p){continue;}
  if(q&&r[i].nm.toLowerCase().indexOf(q)<0){continue;}
  out.push(r[i]); if(out.length>=300){break;}
 }
 var h='<table><tr><th>Rk</th><th>Player</th><th>Pos</th>'+
  '<th>Tm</th><th>Bye</th><th>PPG</th><th>Gms</th>'+
  '<th>VORP</th><th>ADP</th></tr>';
 for(i=0;i<out.length;i++){
  var x=out[i];
  h+='<tr><td>'+x.rk+'</td><td'+
     (x.st?' class="hurt"':'')+'>'+E(x.nm)+
     (x.st?'<span class="tag">'+E(x.st)+'</span>':'')+
     '</td><td>'+E(x.ps)+x.pr+'</td><td>'+E(x.tm)+
     '</td><td>'+(x.by||'--')+'</td><td>'+n1(x.pp)+
     '</td><td>'+n1(x.eg)+'</td><td>'+n1(x.vp)+
     '</td><td>'+n1(x.ad)+'</td></tr>';
 }
 h+='</table>';
 $("btbl").innerHTML=h;
}

function drawNews(){
 var a=(D.news&&D.news.articles)?D.news.articles:[];
 var h='<h2>Latest news</h2>';
 if(!a.length){h+='<div class="card">No articles.</div>';}
 for(var i=0;i<a.length&&i<40;i++){
  h+='<div class="card" style="margin-bottom:10px">'+
   '<div class="kpi-l">'+E(a[i].ts).slice(0,10)+
   (a[i].ins?' <span class="tag">BREAKING</span>':'')+
   '</div><div style="font-weight:600;margin:4px 0">'+
   (a[i].url?'<a href="'+E(a[i].url)+'" target="_blank">'+
    E(a[i].hd)+'</a>':E(a[i].hd))+'</div></div>';
 }
 $("news").innerHTML=h;
}

function drawTrades(){
 var t=(D.news&&D.news.trades)?D.news.trades:[];
 var m=(D.news&&D.news.moves)?D.news.moves:[];
 var h='<h2>Trades and movement</h2>',i;
 h+='<h3 class="sec">2026 trades</h3><table>'+
  '<tr><th>Date</th><th>Player</th><th>From</th>'+
  '<th>To</th></tr>';
 for(i=0;i<t.length;i++){
  if(!t[i].pfr_name){continue;}
  h+='<tr><td>'+E(t[i].trade_date)+'</td><td>'+
   E(t[i].pfr_name)+'</td><td>'+E(t[i].gave)+
   '</td><td>'+E(t[i].received)+'</td></tr>';
 }
 h+='</table><h3 class="sec">Offseason movement</h3>'+
  '<table><tr><th>Rk</th><th>Player</th><th>Pos</th>'+
  '<th>From</th><th>To</th><th>PPG</th></tr>';
 for(i=0;i<m.length;i++){
  h+='<tr><td>'+(m[i].rank?Math.round(m[i].rank):'--')+
   '</td><td>'+E(m[i].player_display_name)+'</td><td>'+
   E(m[i].position)+'</td><td>'+E(m[i].from_tm)+
   '</td><td>'+E(m[i].to_tm)+'</td><td>'+
   (m[i].points?Number(m[i].points).toFixed(1):'--')+
   '</td></tr>';
 }
 h+='</table>';
 $("trades").innerHTML=h;
}

function drawMine(){
 var r=D.mine||[];
 var h='<h2>My team</h2>';
 if(!r.length){
  h+='<div class="card">my_roster.csv not loaded.</div>';
  $("calc").innerHTML=h; return;}
 var tot=0,st=0;
 h+='<table><tr><th>Slot</th><th>Player</th><th>Pos</th>'+
  '<th>Tm</th><th>Bye</th><th>PPG</th><th>Gms</th>'+
  '<th>Board</th></tr>';
 for(var i=0;i<r.length;i++){
  var x=r[i];
  if(x.sl!=="BENCH"&&x.pp){tot+=x.pp*(x.eg||0);st++;}
  h+='<tr><td>'+E(x.sl)+'</td><td'+
   (x.st?' class="hurt"':'')+'>'+E(x.nm)+
   (x.st?'<span class="tag">'+E(x.st)+'</span>':'')+
   '</td><td>'+E(x.ps)+'</td><td>'+E(x.tm)+
   '</td><td>'+(x.by||'--')+'</td><td>'+n1(x.pp)+
   '</td><td>'+n1(x.eg)+'</td><td>'+
   (x.rk||'--')+'</td></tr>';
 }
 h+='</table><div class="cards" style="margin-top:16px">'+
  '<div class="card"><div class="kpi">'+
  Math.round(tot)+'</div><div class="kpi-l">'+
  'Projected season points, '+st+' starters</div></div>'+
  '</div>';
 $("calc").innerHTML=h;
}

$("board").innerHTML='<div class="bar2">'+
 '<input id="fq" placeholder="Search player">'+
 '<select id="fpos"><option>ALL</option><option>QB</option>'+
 '<option>RB</option><option>WR</option><option>TE</option>'+
 '<option>K</option><option>DST</option></select></div>'+
 '<div id="btbl"></div>';
$("fq").addEventListener("input",drawBoard);
$("fpos").addEventListener("change",drawBoard);

safe(drawHome,"home");
safe(drawRosters,"rosters");
safe(drawBoard,"board");
safe(drawNews,"news");
safe(drawTrades,"trades");
safe(drawMine,"calc");


console.log("king fantasy ready");

function drawHome(){}


var RSEL=null;
var RNICK={"BUF":"Bills","MIA":"Dolphins","NE":"Patriots","NYJ":"Jets","BAL":"Ravens","CIN":"Bengals","CLE":"Browns","PIT":"Steelers","HOU":"Texans","IND":"Colts","JAX":"Jaguars","TEN":"Titans","DEN":"Broncos","KC":"Chiefs","LV":"Raiders","LAC":"Chargers","DAL":"Cowboys","NYG":"Giants","PHI":"Eagles","WAS":"Commanders","CHI":"Bears","DET":"Lions","GB":"Packers","MIN":"Vikings","ATL":"Falcons","CAR":"Panthers","NO":"Saints","TB":"Buccaneers","ARI":"Cardinals","LA":"Rams","SF":"49ers","SEA":"Seahawks"};
var RDIV=[["AFC East",["BUF","MIA","NE","NYJ"]],["AFC North",["BAL","CIN","CLE","PIT"]],["AFC South",["HOU","IND","JAX","TEN"]],["AFC West",["DEN","KC","LV","LAC"]],["NFC East",["DAL","NYG","PHI","WAS"]],["NFC North",["CHI","DET","GB","MIN"]],["NFC South",["ATL","CAR","NO","TB"]],["NFC West",["ARI","LA","SF","SEA"]]];
var RLOGO={"ARI":"https://a.espncdn.com/i/teamlogos/nfl/500/ari.png","ATL":"https://a.espncdn.com/i/teamlogos/nfl/500/atl.png","BAL":"https://a.espncdn.com/i/teamlogos/nfl/500/bal.png","BUF":"https://a.espncdn.com/i/teamlogos/nfl/500/buf.png","CAR":"https://a.espncdn.com/i/teamlogos/nfl/500/car.png","CHI":"https://a.espncdn.com/i/teamlogos/nfl/500/chi.png","CIN":"https://a.espncdn.com/i/teamlogos/nfl/500/cin.png","CLE":"https://a.espncdn.com/i/teamlogos/nfl/500/cle.png","DAL":"https://a.espncdn.com/i/teamlogos/nfl/500/dal.png","DEN":"https://a.espncdn.com/i/teamlogos/nfl/500/den.png","DET":"https://a.espncdn.com/i/teamlogos/nfl/500/det.png","GB":"https://a.espncdn.com/i/teamlogos/nfl/500/gb.png","HOU":"https://a.espncdn.com/i/teamlogos/nfl/500/hou.png","IND":"https://a.espncdn.com/i/teamlogos/nfl/500/ind.png","JAX":"https://a.espncdn.com/i/teamlogos/nfl/500/jax.png","KC":"https://a.espncdn.com/i/teamlogos/nfl/500/kc.png","LV":"https://a.espncdn.com/i/teamlogos/nfl/500/lv.png","LAC":"https://a.espncdn.com/i/teamlogos/nfl/500/lac.png","LA":"https://a.espncdn.com/i/teamlogos/nfl/500/lar.png","MIA":"https://a.espncdn.com/i/teamlogos/nfl/500/mia.png","MIN":"https://a.espncdn.com/i/teamlogos/nfl/500/min.png","NE":"https://a.espncdn.com/i/teamlogos/nfl/500/ne.png","NO":"https://a.espncdn.com/i/teamlogos/nfl/500/no.png","NYG":"https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png","NYJ":"https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png","PHI":"https://a.espncdn.com/i/teamlogos/nfl/500/phi.png","PIT":"https://a.espncdn.com/i/teamlogos/nfl/500/pit.png","SF":"https://a.espncdn.com/i/teamlogos/nfl/500/sf.png","SEA":"https://a.espncdn.com/i/teamlogos/nfl/500/sea.png","TB":"https://a.espncdn.com/i/teamlogos/nfl/500/tb.png","TEN":"https://a.espncdn.com/i/teamlogos/nfl/500/ten.png","WAS":"https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png"};
function RE(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function RQ(i){return document.getElementById(i);}
function RTeam(t){
 var T=D.teams[t];
 if(!T&&t==="ARI"){T=D.teams["AZ"];}
 if(!T&&t==="LA"){T=D.teams["LAR"];}
 if(!T&&t==="WAS"){T=D.teams["WSH"];}
 return T;
}
function pickTeam(t){
 RSEL=(RSEL===t)?null:t;
 drawRosters();
 var e=RQ("dcard");
 if(e){e.scrollIntoView({behavior:"smooth",block:"center"});}
}
function depthCard(t){
 var T=RTeam(t);
 if(!T){return '<div class="dcard">No depth chart on file '+
  'for '+RE(t)+'.</div>';}
 var c=T.coach||{};
 var inj=T.injuries||[];
 var h='<div class="dcard" id="dcard"><div class="dhead">'+
  '<img src="'+RLOGO[t]+'" alt=""><div><h3>'+
  RE(RNICK[t])+'</h3><span>'+
  RE(c.head_coach||"head coach not on file")+
  ' &middot; '+inj.length+' on the injury report</span>'+
  '</div></div>';
 var off=(T.depth&&T.depth.offense)||{};
 var ORD=["QB","RB","WR","TE","LT","LG","C","RG","RT","FB"];
 var hurt={};
 inj.forEach(function(x){if(x.id){hurt[x.id]=x.inj||"inj";}});
 h+='<div class="dgrid">';
 ORD.forEach(function(p){
  var L=off[p];
  if(!L||!L.length){return;}
  h+='<div class="dpos"><h5>'+RE(p)+'</h5>';
  L.slice(0,4).forEach(function(m){
   var im=m.img?'<img src="'+RE(m.img)+'" alt="">':
    '<img alt="">';
   var fl=hurt[m.id]?' <em>&#9873; '+RE(hurt[m.id])+'</em>':'';
   h+='<div class="dp"><i>'+(m.rank||"")+'</i>'+im+
    '<span>'+RE(m.name)+fl+'</span></div>';
  });
  h+='</div>';
 });
 h+='</div><p class="dnote">Depth order is the latest '+
  'published chart, not a projection. Injury flags come from '+
  'the tracked list; a flagged starter is the single biggest '+
  'reason a projection moves.</p></div>';
 return h;
}
function drawRosters(){
 var h='';
 if(RSEL){h+=depthCard(RSEL);}
 h+='<div class="divwrap">';
 RDIV.forEach(function(d){
  h+='<div class="divcol"><h4>'+RE(d[0])+'</h4>';
  d[1].forEach(function(t){
   var sel=(RSEL===t)?' sel':'';
   h+='<div class="tmrow'+sel+'" onclick="pickTeam(\''+t+
    '\')"><img src="'+RLOGO[t]+'" alt="'+RE(t)+'">'+
    '<b>'+RE(RNICK[t])+'</b></div>';
  });
  h+='</div>';
 });
 h+='</div>';
 RQ("rosters").innerHTML=h;
}

safe(drawRosters,'rosters');
