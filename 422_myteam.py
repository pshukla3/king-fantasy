CSS = """
*{box-sizing:border-box}
body{margin:0;padding:0 2px 30px;background:transparent;
color:#e8e8ea;font:14px/1.45 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1060px;margin:0 auto}
.top{display:flex;align-items:center;gap:14px;
padding:10px 0 4px;flex-wrap:wrap}
.top h2{margin:0;font-size:21px;letter-spacing:-.4px}
.top .rec{color:#8a8a92;font-size:13px}
.tot{margin-left:auto;text-align:right}
.tot b{display:block;font-size:28px;font-weight:800;
letter-spacing:-1px}
.tot span{font-size:10px;color:#8a8a92;
text-transform:uppercase;letter-spacing:.7px}
.wk{background:#1c1c20;color:#e8e8ea;border:1px solid #2a2a30;
border-radius:8px;padding:6px 10px;font-size:12px}
h4{margin:22px 0 6px;font-size:12px;text-transform:uppercase;
letter-spacing:.8px;color:#8a8a92;font-weight:700}
h4 i{float:right;font-style:normal;color:#6a6a72;
text-transform:none;letter-spacing:0;font-size:11px}
.pr{display:grid;grid-template-columns:46px 38px 1fr auto;
gap:10px;align-items:center;padding:8px 10px;
border-bottom:1px solid #1c1c20;border-radius:8px;
cursor:pointer}
.pr:hover{background:#121216}
.pr.sel{background:#1a1610;outline:1px solid #c9a227}
.pr.ok{background:#0f1a12}
.slot{font-size:10px;font-weight:800;letter-spacing:.5px;
color:#9a9aa2;background:#1c1c20;border-radius:6px;
padding:5px 0;text-align:center}
.pr img{width:38px;height:38px;border-radius:50%;
background:#1c1c20;object-fit:cover}
.nm b{display:block;font-size:14px}
.nm b:hover{color:#c9a227}
.nm span{font-size:11px;color:#8a8a92}
.pv{font-size:16px;font-weight:700;text-align:right;
min-width:52px;font-variant-numeric:tabular-nums}
.pill{display:inline-block;font-size:9px;padding:1px 6px;
border-radius:99px;background:#2a2a30;color:#b4b4bc;
margin-left:6px;vertical-align:middle}
.pill.out{background:#3a1f1f;color:#f87171}
.pill.bye{background:#2a2438;color:#c4b5fd}
.card{background:#101013;border:1px solid #232327;
border-radius:14px;padding:14px 16px;margin:14px 0}
.card h5{margin:0 0 8px;font-size:13px}
.btn{padding:7px 14px;border-radius:8px;border:1px solid #3a3a42;
background:#1c1c20;color:#e8e8ea;cursor:pointer;font-size:12px;
font-weight:600;margin-right:6px}
.btn.go{background:#c9a227;color:#111;border-color:#c9a227}
.gain{color:#4ade80;font-weight:700}
.mut{color:#8a8a92;font-size:12px}
table.t{width:100%;border-collapse:collapse;font-size:13px}
table.t td,table.t th{padding:6px 8px;text-align:left;
border-bottom:1px solid #1c1c20}
table.t th{color:#8a8a92;font-size:11px;font-weight:600;
text-transform:uppercase;letter-spacing:.4px}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.bar{height:6px;border-radius:99px;background:#22222a;
overflow:hidden;margin-top:3px}
.bar i{display:block;height:100%;background:#c9a227}
.hint{font-size:11px;color:#6a6a72;margin:4px 0 0}
"""

JS = r"""
var T=null,BD=null,LGJ=null,SLOTS=[],WK=2,MYID=1;
var LINEUP=null,SEL=null,ME=null;
var EL={QB:["QB"],RB:["RB"],WR:["WR"],TE:["TE"],K:["K"],
DEF:["DEF","DST"],DST:["DEF","DST"],FLEX:["RB","WR","TE"],
WRRB_FLEX:["RB","WR"],REC_FLEX:["WR","TE"],
SUPER_FLEX:["QB","RB","WR","TE"]};

function $(i){return document.getElementById(i);}
function norm(s){return String(s||"").toLowerCase()
 .replace(/[^a-z ]/g,"").replace(/\s+/g," ").trim().replace(/ (jr|sr|iii|ii|iv|v)$/,"");}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function n1(v){return (Math.round(v*10)/10).toFixed(1);}

var BM={},BDST={};
function bd(p){
 if(p.pos==="DEF"||p.pos==="DST")
  return BDST[p.tm]||BDST[p.pid]||null;
 return BM[p.k||norm(p.n)]||null;
}

var PW=null;
function wkProj(p,wk){
 if(!PW)return null;
 var k=norm(p.n||p.name||"");
 var v=PW[k];
 if(!v||!v.wk)return null;
 for(var i=0;i<v.wk.length;i++){
  if(Number(v.wk[i].w)===Number(wk))return v.wk[i].m;
 }
 return null;
}

function proj(p,wk){
 var A=KFwk.actual(p,wk);
 if(A!=null)return A;
 var W=wkProj(p,wk);
 if(W!=null)return W;
 var b=bd(p);
 var v=(b&&b.live!=null)?b.live:(p.ppg||0);
 if(b&&b.bye&&Number(b.bye)===Number(wk))return 0;
 var inj=String(p.inj||(b?b.inj:"")||"");
 if(/^(Out|IR|Sus|NA|PUP|DNR)/i.test(inj))return 0;
 if(/Doubtful/i.test(inj))v*=0.35;
 if(/Question/i.test(inj))v*=0.88;
 return v;
}
function img(p){var b=bd(p);return (b&&b.img)?b.img:"";}
function elig(p,s){var a=EL[s];return a?a.indexOf(p.pos)>=0:false;}
function ss(){return SLOTS.filter(function(s){
 return s!=="BN"&&s!=="IR"&&s!=="TAXI";});}

function optimal(t,wk){
 var S=ss(),pool=(t.players||[]).slice();
 pool.sort(function(a,b){return proj(b,wk)-proj(a,wk);});
 var used={},out=[],fx=[];
 S.forEach(function(s,i){
  if(s.indexOf("FLEX")>=0){fx.push(i);out[i]=null;return;}
  var pk=null;
  for(var j=0;j<pool.length;j++){
   if(used[pool[j].pid])continue;
   if(elig(pool[j],s)){pk=pool[j];break;}}
  out[i]=pk;if(pk)used[pk.pid]=1;});
 fx.forEach(function(i){
  var s=S[i],pk=null;
  for(var j=0;j<pool.length;j++){
   if(used[pool[j].pid])continue;
   if(elig(pool[j],s)){pk=pool[j];break;}}
  out[i]=pk;if(pk)used[pk.pid]=1;});
 return out;
}
function lineupOf(t){
 var S=ss(),st=t.starters||[],by={},out=[];
 (t.players||[]).forEach(function(p){by[p.pid]=p;});
 S.forEach(function(s,i){out[i]=by[st[i]]||null;});
 return out;
}
function total(lu,wk){var s=0;
 lu.forEach(function(p){if(p)s+=proj(p,wk);});return s;}

function prow(p,slot,idx,cls){
 if(!p)return '<div class="pr"><div class="slot">'
  +esc(slot)+'</div><div></div>'
  +'<div class="nm mut">empty</div>'
  +'<div class="pv">0.0</div></div>';
 var b=bd(p),tags="";
 var inj=String(p.inj||(b?b.inj:"")||"");
 if(b&&b.bye&&Number(b.bye)===Number(WK))
  tags+='<span class="pill bye">BYE</span>';
 else if(inj&&!/Active/i.test(inj))
  tags+='<span class="pill'+(/^(Out|IR)/i.test(inj)?
   ' out':'')+'">'+esc(inj.slice(0,4).toUpperCase())
   +'</span>';
 var at=(idx!=null)?(' data-slot="'+idx+'"'):
  (' data-pid="'+esc(p.pid)+'"');
 return '<div class="pr '+(cls||"")+'"'+at+'>'
  +'<div class="slot">'+esc(slot)+'</div>'
  +(img(p)?'<img src="'+esc(img(p))+'">':'<div></div>')
  +'<div class="nm"><b data-kfp="'+esc(p.n)+'">'
  +esc(p.n)+tags+'</b>'
  +'<span>'+esc(p.pos)+' &middot; '+esc(p.tm||"FA")
  +(b&&b.rk?(' &middot; #'+b.rk+' overall'):'')
  +'</span></div>'
  +'<div class="pv">'+n1(proj(p,WK))+'</div></div>';
}

function draw(){
 ME=null;
 (T.teams||[]).forEach(function(t){
  if(Number(t.id)===Number(MYID))ME=t;});
 if(!ME){$("v").innerHTML='<p class="mut">Team '+MYID
  +' not found.</p>';return;}
 var S=ss();
 if(!LINEUP)LINEUP=lineupOf(ME);
 var my=total(LINEUP,WK);

 var h='<div class="wrap"><div class="top">'
  +'<h2>'+esc(ME.owner||("Team "+ME.id))+'</h2>'
  +'<span class="rec">'+ME.w+'-'+ME.l+' &middot; '
  +n1(ME.pf)+' PF &middot; '+n1(ME.pa)+' PA</span>'
  +'<select class="wk" id="wksel">';
 for(var w=1;w<=18;w++)h+='<option value="'+w+'"'
  +(w===WK?' selected':'')+'>Week '+w+'</option>';
 h+='</select><div class="tot"><b>'+n1(my)
  +'</b><span>projected</span></div></div>';

 h+='<h4>Starters<i>click a row to swap &middot; click a '
  +'name for full analysis</i></h4>';
 S.forEach(function(s,i){
  var a=LINEUP[i],c="";
  if(SEL&&SEL.slot===i)c="sel";
  else if(SEL&&SEL.bench&&elig(SEL.bench,s))c="ok";
  h+=prow(a,s,i,c);
 });

 var inLU={};
 LINEUP.forEach(function(p){if(p)inLU[p.pid]=1;});
 var bench=(ME.players||[]).filter(function(p){
  return !inLU[p.pid];});
 bench.sort(function(a,b){return proj(b,WK)-proj(a,WK);});
 h+='<h4>Bench<i>'+bench.length+' players</i></h4>';
 bench.forEach(function(p){
  var c="";
  if(SEL&&SEL.bench&&SEL.bench.pid===p.pid)c="sel";
  else if(SEL&&SEL.slot!=null&&elig(p,S[SEL.slot]))c="ok";
  h+=prow(p,"BN",null,c);
 });

 // optimizer
 var op=optimal(ME,WK),ot=total(op,WK),gain=ot-my;
 h+='<div class="card"><h5>Optimizer</h5>';
 if(gain<0.05){
  h+='<p class="mut">Your lineup is already optimal for '
   +'week '+WK+'.</p>';
 }else{
  h+='<p class="mut">Optimal projects <b>'+n1(ot)
   +'</b> &mdash; <span class="gain">+'+n1(gain)
   +'</span> over your current '+n1(my)+'.</p>';
  S.forEach(function(s,i){
   var a=LINEUP[i],b=op[i];
   if(!b||(a&&a.pid===b.pid))return;
   var d=proj(b,WK)-(a?proj(a,WK):0);
   if(d<=0.05)return;
   h+='<div class="mut" style="padding:3px 0">'
    +esc(s)+': '+esc(a?a.n:"empty")+' &rarr; <b>'
    +esc(b.n)+'</b> <span class="gain">+'+n1(d)
    +'</span></div>';});
  h+='<div style="margin-top:10px">'
   +'<button class="btn go" id="applyopt">Apply optimal'
   +'</button><button class="btn" id="resetlu">Reset'
   +'</button></div>';
 }
 h+='<p class="hint">What-if only \u2014 Sleeper\u2019s '
  +'public API is read-only, so set the real lineup there '
  +'too.</p></div>';

 // positional strength
 h+='<div class="card"><h5>Roster strength by position</h5>';
 var G={};
 (ME.players||[]).forEach(function(p){
  (G[p.pos]=G[p.pos]||[]).push(proj(p,WK));});
 var order=["QB","RB","WR","TE","K","DEF"];
 var best=0;
 order.forEach(function(ps){
  if(G[ps]){var s=G[ps].slice().sort(function(a,b){
   return b-a;}).slice(0,3).reduce(function(a,b){
   return a+b;},0);if(s>best)best=s;}});
 h+='<table class="t">';
 order.forEach(function(ps){
  var a=G[ps];if(!a)return;
  a=a.slice().sort(function(x,y){return y-x;});
  var top=a.slice(0,3).reduce(function(x,y){
   return x+y;},0);
  h+='<tr><td>'+ps+'</td>'
   +'<td class="num">'+a.length+'</td>'
   +'<td style="width:50%"><div class="bar"><i style="width:'
   +(best?Math.round(100*top/best):0)+'%"></i></div></td>'
   +'<td class="num">'+n1(top)+'</td></tr>';});
 h+='</table><p class="hint">Sum of your top three at each '
  +'position, this week.</p></div>';

 // bye + injury watch
 var byes={},hurt=[];
 (ME.players||[]).forEach(function(p){
  var b=bd(p);
  if(b&&b.bye)(byes[b.bye]=byes[b.bye]||[]).push(p.n);
  var inj=String(p.inj||(b?b.inj:"")||"");
  if(inj&&!/Active/i.test(inj))
   hurt.push({n:p.n,s:inj,pos:p.pos});});
 h+='<div class="card"><h5>Bye weeks &amp; injuries</h5>';
 var bk=Object.keys(byes).sort(function(a,b){
  return a-b;});
 if(bk.length){
  h+='<table class="t"><tr><th>Week</th><th>Players on bye'
   +'</th></tr>';
  bk.forEach(function(w){
   var n=byes[w].length;
   h+='<tr><td>'+w+(n>=3?' <span class="pill out">'
    +n+'</span>':'')+'</td><td class="mut">'
    +esc(byes[w].join(", "))+'</td></tr>';});
  h+='</table>';
 }else h+='<p class="mut">No bye data.</p>';
 if(hurt.length){
  h+='<table class="t" style="margin-top:10px">'
   +'<tr><th>Player</th><th>Status</th></tr>';
  hurt.forEach(function(x){
   h+='<tr><td data-kfp="'+esc(x.n)+'" '
    +'style="cursor:pointer">'+esc(x.n)+' <span '
    +'class="mut">'+esc(x.pos)+'</span></td>'
    +'<td><span class="pill out">'+esc(x.s)
    +'</span></td></tr>';});
  h+='</table>';
 }
 h+='</div></div>';

 $("v").innerHTML=h;
 wire(S,bench);
 try{parent.postMessage(
  {kfh:document.body.scrollHeight+24},"*");}catch(e){}
}

function wire(S,bench){
 var w=$("wksel");
 if(w)w.onchange=function(){
  WK=Number(w.value);SEL=null;KFwk.load(WK).then(function(){draw();});};
 var a=$("applyopt");
 if(a)a.onclick=function(){
  LINEUP=optimal(ME,WK);SEL=null;draw();};
 var r=$("resetlu");
 if(r)r.onclick=function(){
  LINEUP=lineupOf(ME);SEL=null;draw();};

 function isName(e){
  var t=e.target;
  while(t&&t!==document.body){
   if(t.getAttribute&&t.getAttribute("data-kfp"))return 1;
   t=t.parentNode;}
  return 0;
 }
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-slot]"),function(e){
  e.onclick=function(ev){
   if(isName(ev))return;
   var i=Number(e.getAttribute("data-slot"));
   if(SEL&&SEL.bench){
    if(elig(SEL.bench,S[i]))LINEUP[i]=SEL.bench;
    SEL=null;draw();return;}
   SEL=(SEL&&SEL.slot===i)?null:{slot:i};
   draw();};});
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-pid]"),function(e){
  e.onclick=function(ev){
   if(isName(ev))return;
   var pid=e.getAttribute("data-pid"),p=null;
   bench.forEach(function(x){if(x.pid===pid)p=x;});
   if(!p)return;
   if(SEL&&SEL.slot!=null){
    if(elig(p,S[SEL.slot]))LINEUP[SEL.slot]=p;
    SEL=null;draw();return;}
   SEL=(SEL&&SEL.bench&&SEL.bench.pid===pid)?null:{bench:p};
   draw();};});
}

function boot(){
 try{var m=localStorage.getItem("kf_myteam");
  if(m)MYID=Number(m);}catch(e){}
 Promise.all([
  fetch("_slteams.json").then(function(r){return r.json();}),
  fetch("_board.json").then(function(r){return r.json();}),
  fetch("_projweek.json").then(function(r){return r.json();})
   .catch(function(){return null;}),
  fetch("_league.json").then(function(r){return r.json();})
   .catch(function(){return null;})
 ]).then(function(a){
  T=a[0];BD=a[1];PW=a[2];LGJ=a[3];
  SLOTS=T.slots||["QB","RB","RB","WR","WR","TE","FLEX",
   "FLEX","K","DEF"];
  (BD.rows||[]).forEach(function(r){
   var p=String(r.pos||"");
   if(p==="DEF"||p==="DST")BDST[String(r.tm||"")]=r;
   else BM[norm(r.n)]=r;});
  if(LGJ&&LGJ.week)WK=Math.min(18,Number(LGJ.week)+1);
  KFwk.load(WK).then(function(){draw();});
 }).catch(function(e){
  $("v").innerHTML='<p class="mut">Could not load team: '
   +esc(e.message)+'</p>';});
}
boot();
"""

HTML = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,'
        'initial-scale=1"><style>__CSS__</style></head>'
        '<body><div id="v" class="mut">Loading team\u2026</div>'
        '<script src="_card.js"></script>'
        '<script src="_score.js"></script><script src="_wkpts.js"></script><script>__JS__</script></body></html>')
HTML = HTML.replace("__CSS__", CSS).replace("__JS__", JS)
open("site/myteam.html", "w").write(HTML)
print("wrote site/myteam.html (%d KB)" % (len(HTML) // 1024))

H = open("vaporai.html").read()
OLD = ('<section id="lgh_tm"><iframe '
       'data-src="league.html?tab=tm"')
NEW = '<section id="lgh_tm"><iframe data-src="myteam.html"'
if OLD in H:
    H = H.replace(OLD, NEW, 1)
    open("vaporai.html", "w").write(H)
    print("lgh_tm -> myteam.html")
else:
    assert NEW in H, "lgh_tm iframe not found"
    print("lgh_tm already points at myteam.html")

# matchup.html should open cards too
M = open("site/matchup.html").read()
CT = '<script src="_card.js"></script>'
if CT not in M:
    M = M.replace("<script>", CT + "<script>", 1)
    open("site/matchup.html", "w").write(M)
    print("matchup.html: _card.js added")
else:
    print("matchup.html: _card.js already present")
