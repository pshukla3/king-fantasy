import io, os
H = io.StringIO()
W = H.write

W('''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mock Draft</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#080808;color:#eee;
 font:14px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",
 Roboto,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1500px;margin:0 auto;padding:16px}
h1{font-size:26px;font-weight:800;letter-spacing:-.5px}
.sub{color:#888;font-size:13px;margin-top:4px}
.card{background:#101010;border:1px solid #232323;
 border-radius:14px;padding:18px;margin-bottom:14px}
.lbl{font-size:11px;font-weight:700;letter-spacing:1.2px;
 color:#7a7a7a;text-transform:uppercase;margin-bottom:8px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:22px}
.opt{background:#1a1a1a;border:1px solid #2c2c2c;color:#ccc;
 padding:9px 17px;border-radius:9px;cursor:pointer;
 font-size:13px;font-weight:600;transition:.12s}
.opt:hover{background:#242424;color:#fff}
.opt.on{background:#f2ece1;border-color:#f2ece1;color:#111}
.hint{color:#666;font-size:12px;margin-top:7px}
.dash{border-top:1px dashed #262626;margin:18px 0}
.slots{display:grid;grid-template-columns:repeat(3,1fr);
 gap:11px;margin-top:10px}
.slot{border-radius:11px;padding:13px 15px;display:flex;
 align-items:center;justify-content:space-between;
 border:1px solid}
.slot b{font-size:13px;font-weight:800;letter-spacing:.6px}
.stp{display:flex;align-items:center;gap:11px}
.stp button{width:26px;height:26px;border-radius:50%;
 background:transparent;border:1px solid #444;color:#bbb;
 cursor:pointer;font-size:15px;line-height:1}
.stp button:hover{border-color:#888;color:#fff}
.stp span{min-width:16px;text-align:center;font-weight:800;
 font-size:16px}
.s-QB{background:#0b1d14;border-color:#1d3d2b}
.s-QB b{color:#3ddc84}
.s-RB{background:#0b1522;border-color:#1c3350}
.s-RB b{color:#4da3ff}
.s-WR{background:#1d0d14;border-color:#45202f}
.s-WR b{color:#ff5d8f}
.s-TE{background:#170d1f;border-color:#35204a}
.s-TE b{color:#b07cff}
.s-FLEX{background:#1f1608;border-color:#4a3413}
.s-FLEX b{color:#ffa63d}
.s-K{background:#141414;border-color:#2b2b2b}
.s-K b{color:#999}
.s-DST{background:#0b1d14;border-color:#1d3d2b}
.s-DST b{color:#3ddc84}
.go{background:#f2ece1;color:#111;border:0;padding:12px 26px;
 border-radius:10px;font-weight:800;font-size:14px;
 cursor:pointer}
.go:hover{background:#fff}
.ghost{background:transparent;border:1px solid #333;
 color:#aaa;padding:12px 24px;border-radius:10px;
 font-weight:700;cursor:pointer}
</style></head><body><div class="wrap">
''')

W('''<div id="setup">
<h1>Build Your League</h1>
<div class="sub">Set the format, roster, and draft rules —
 your board is built to match.</div>
<div class="card" style="margin-top:14px">
 <div class="grid2">
  <div>
   <div class="lbl">Teams</div>
   <div class="row" id="o-teams"></div>
   <div class="dash"></div>
   <div class="lbl">Scoring</div>
   <div class="row" id="o-score"></div>
   <div class="hint" id="h-score"></div>
   <div class="dash"></div>
   <div class="lbl">Draft Pattern</div>
   <div class="row" id="o-pat"></div>
   <div class="hint">Pick order reverses each round.</div>
  </div>
  <div>
   <div class="lbl">Your Draft Slot</div>
   <div class="row" id="o-slot"></div>
   <div class="row" style="margin-top:9px">
    <button class="opt" onclick="randSlot()">Randomize</button>
   </div>
   <div class="dash"></div>
   <div class="lbl">Draft Speed</div>
   <div class="row" id="o-speed"></div>
   <div class="dash"></div>
   <div class="lbl">Rounds</div>
   <div class="row">
    <div class="stp" style="background:#141414;
      border:1px solid #2b2b2b;border-radius:10px;
      padding:9px 15px">
     <button onclick="bump('rounds',-1)">&minus;</button>
     <span id="v-rounds">15</span>
     <button onclick="bump('rounds',1)">+</button>
    </div>
   </div>
   <div class="hint" id="h-picks"></div>
  </div>
 </div>
 <div class="dash"></div>
 <div class="row" style="justify-content:space-between">
  <div class="lbl" style="margin:0">Roster (Starters)</div>
  <div class="hint" style="margin:0" id="h-roster"></div>
 </div>
 <div class="slots" id="o-slots"></div>
 <div class="hint" id="h-bench"></div>
 <div class="dash"></div>
 <div class="row" style="justify-content:flex-end">
  <button class="ghost" onclick="location.reload()">Reset</button>
  <button class="go" onclick="startDraft()">Start Mock Draft
   &rsaquo;</button>
 </div>
</div></div>
''')

W('''<div id="draft" style="display:none">
<style>
.top{display:flex;align-items:center;gap:18px;
 background:#101010;border:1px solid #232323;
 border-radius:12px;padding:12px 16px;margin-bottom:12px}
.clock{background:#ff7a18;color:#111;border-radius:9px;
 padding:8px 16px;font-weight:800;min-width:92px;
 text-align:center}
.clock.wait{background:#1c1c1c;color:#888}
.mid{font-weight:800;font-size:16px}
.ctl{margin-left:auto;display:flex;gap:8px}
.ctl button{background:#1a1a1a;border:1px solid #2c2c2c;
 color:#bbb;padding:8px 14px;border-radius:9px;
 cursor:pointer;font-weight:700;font-size:12px}
.ctl button:hover{color:#fff;border-color:#555}
.board{display:grid;grid-template-columns:1fr 372px;gap:14px}


/*KFGRID*/

.wrap{max-width:none!important;padding:14px 18px!important}
.board{display:block!important}
.pane{width:100%!important;margin-top:16px}
.gridwrap{background:#101010;border:1px solid #232323;
 border-radius:12px;padding:10px!important;
 overflow:auto!important;max-height:none!important}
table.g{border-collapse:separate;border-spacing:4px;
 width:100%;table-layout:fixed}
table.g thead th{position:sticky;top:0;z-index:3;
 background:#141414;font-size:12px;padding:8px 4px;
 color:#9aa;white-space:nowrap;overflow:hidden}
table.g th.rh{position:sticky;left:0;z-index:4;
 background:#141414;width:26px;font-size:11px;color:#777}
table.g th.meh{color:#3b82f6}
table.g td.c{height:58px!important;padding:4px 6px;
 border-radius:7px;background:#161b26;
 border:1px solid #232c3d;overflow:hidden;
 position:relative;vertical-align:top}
table.g td.c em{position:absolute;top:3px;right:6px;
 font-size:10px;color:#6b7686;font-style:normal}
table.g td.c s{position:absolute;bottom:2px;left:6px;
 font-size:11px;color:#55606f;text-decoration:none}
table.g td.c b{display:block;font-size:12px;line-height:1.15;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
 max-width:88%;margin-top:3px;color:#0d1117}
table.g td.c i{display:block;font-size:9px;font-style:normal;
 color:#263040;margin-top:2px}
table.g td.me{box-shadow:inset 0 0 0 2px #3b82f6}
table.g td.on{box-shadow:0 0 0 3px #fbbf24}
.p-QB{background:#f2a0b4!important;border-color:#e07c96!important}
.p-RB{background:#8fe0b0!important;border-color:#5cc78d!important}
.p-WR{background:#86c7f0!important;border-color:#54a8df!important}
.p-TE{background:#f0b878!important;border-color:#dd9a4e!important}
.p-K,.p-DST{background:#c9c9d4!important;
 border-color:#a8a8b8!important}
.rch{outline:2px solid #ef4444}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.tabs button{display:flex;flex-direction:column;
 align-items:center;line-height:1.1;padding:6px 14px;
 border-radius:16px;font-size:12px}
.tabs button small{font-size:10px;opacity:.65;margin-top:2px}
table.pl{width:100%;border-collapse:collapse;font-size:12px}
table.pl tr.grp th{font-size:10px;color:#8b94a3;
 letter-spacing:.6px;padding:6px 4px;
 border-bottom:1px solid #222}
table.pl tr.hd2 th{font-size:10px;color:#6f7988;
 padding:5px 4px;border-bottom:1px solid #2a2a2a;
 text-align:right}
table.pl tr.hd2 th.pn{text-align:left}
table.pl td{padding:7px 4px;text-align:right;
 border-bottom:1px solid #1b1b1b;color:#c9d1d9}
table.pl td.pn{text-align:left;min-width:190px}
table.pl td.pn b{display:block;font-size:13px;color:#fff}
table.pl td.pn i{font-style:normal;font-size:10px;
 color:#8b94a3}
table.pl td.rk{color:#6f7988;width:38px}
table.pl td.hi{color:#fff;font-weight:600}
table.pl button{padding:4px 12px;border-radius:6px;
 font-size:11px}
/*ENDKFGRID*/
.gridwrap{background:#101010;border:1px solid #232323;
 border-radius:12px;padding:14px;overflow:auto;
 max-height:86vh}
table.g{border-collapse:separate;border-spacing:6px}
table.g th{font-size:10px;color:#777;font-weight:700;
 text-transform:uppercase;letter-spacing:.8px;
 padding-bottom:4px;white-space:nowrap}
td.c{background:#161616;border-radius:9px;padding:9px 11px;
 min-width:132px;height:66px;vertical-align:top;
 font-size:12px;color:#5c5c5c;border-left:3px solid #262626}
td.c.me{background:#241703;outline:1px solid #5a3a0d}
td.c.on{background:#ff7a18;color:#111;font-weight:800}
td.c.f{color:#ddd}
td.c b{display:block;font-size:13px;font-weight:700;
 color:#fff;white-space:nowrap;overflow:hidden;
 text-overflow:ellipsis;max-width:120px;margin-bottom:2px}
td.c i{font-style:normal;font-size:11px;color:#9a9a9a}
td.c em{font-style:normal;font-size:10px;color:#4e4e4e;
 display:block;margin-bottom:3px;font-weight:700}
/* position colors on the board */
td.c.p-QB{background:#0c1f16;border-left-color:#3ddc84}
td.c.p-QB i{color:#3ddc84}
td.c.p-RB{background:#0b1726;border-left-color:#4da3ff}
td.c.p-RB i{color:#4da3ff}
td.c.p-WR{background:#210e16;border-left-color:#ff4d6d}
td.c.p-WR i{color:#ff6b86}
td.c.p-TE{background:#190e22;border-left-color:#b07cff}
td.c.p-TE i{color:#b07cff}
td.c.p-K,td.c.p-DST{background:#161616;
 border-left-color:#666}
table.g th{font-size:11px}
td.c.rch{outline:1px solid #e0543a}
.pane{background:#101010;border:1px solid #232323;
 border-radius:12px;padding:12px;display:flex;
 flex-direction:column;max-height:74vh}
.pane input{background:#1a1a1a;border:1px solid #2c2c2c;
 color:#eee;border-radius:9px;padding:10px 13px;width:100%;
 font-size:13px;outline:none}
.tabs{display:flex;gap:6px;margin:10px 0}
.tabs button{background:#1a1a1a;border:1px solid #2c2c2c;
 color:#999;padding:6px 13px;border-radius:20px;
 cursor:pointer;font-size:12px;font-weight:700}
.tabs button.on{background:#f2ece1;color:#111;
 border-color:#f2ece1}
.plist{overflow:auto;flex:1}
.p{display:flex;align-items:center;gap:11px;padding:9px 6px;
 border-bottom:1px solid #1c1c1c}
.p img{width:38px;height:38px;border-radius:50%;
 background:#222;object-fit:cover}
.pg{background:#4da3ff;color:#06101d;font-size:10px;
 font-weight:800;padding:2px 7px;border-radius:5px}
.pg.QB{background:#3ddc84;color:#06180f}
.pg.WR{background:#ff5d8f;color:#1d0810}
.pg.TE{background:#b07cff;color:#140823}
.pg.K,.pg.DST{background:#666;color:#111}
.p .nm{font-weight:700;font-size:13px}
.p .mt{font-size:11px;color:#777;margin-top:2px}
.p .pk{margin-left:auto;text-align:right}
.p .pk button{background:#ff7a18;border:0;color:#111;
 font-weight:800;padding:6px 15px;border-radius:7px;
 cursor:pointer;font-size:12px}
.p .pk button[disabled]{background:#242424;color:#666;
 cursor:not-allowed}
.ppg{font-size:11px;color:#888;margin-bottom:3px}
.feed{max-height:150px;overflow:auto;margin-top:10px;
 border-top:1px solid #1e1e1e;padding-top:9px}
.fi{font-size:12px;color:#999;padding:4px 0}
.fi b{color:#eee}
.badge{background:#e0543a;color:#fff;font-size:9px;
 font-weight:800;padding:1px 6px;border-radius:4px;
 margin-left:6px}
.myros{margin-top:10px;border-top:1px solid #1e1e1e;
 padding-top:9px}
.rs{display:flex;justify-content:space-between;
 font-size:12px;padding:3px 0;color:#bbb}
.rs span:first-child{color:#777;font-weight:700;
 min-width:44px}
</style>
<div class="top">
 <div class="clock" id="clk">0:30</div>
 <div>
  <div class="mid" id="onclk">--</div>
  <div class="hint" id="pkinfo" style="margin:0"></div>
 </div>
 <div class="ctl">
  <button onclick="togglePause()" id="bp">Pause</button>
  <button onclick="S.sound=!S.sound;this.textContent=
   S.sound?'Sound On':'Sound Off'">Sound On</button>
  <button onclick="autoPick()">Auto Pick</button>
  <button onclick="location.reload()">Exit</button>
 </div>
</div>
<div class="board">
 <div class="gridwrap"><div id="grid"></div></div>
 <div class="pane">
  <input id="q" placeholder="Search players..."
   oninput="renderList()">
  <div class="tabs" id="tabs"></div>
  <div class="plist" id="plist"></div>
  <div class="myros"><div class="lbl">Your Roster</div>
   <div id="ros"></div></div>
  <div class="feed" id="feed"></div>
 </div>
</div></div>
''')

W('''<script>
var S={teams:12,score:"half",slot:6,speed:1000,rounds:15,
 pat:"snake",sound:true,paused:false,pool:[],picks:[],
 pick:0,filter:"ALL",timer:null,tick:null,left:30,
 slots:{QB:1,RB:2,WR:2,TE:1,FLEX:1,K:1,DST:1}};

var AC=null;
function beep(f,d,t,v){
 try{AC=AC||new (window.AudioContext||
  window.webkitAudioContext)();
  var o=AC.createOscillator(),g=AC.createGain();
  o.type=t||"sine";o.frequency.value=f;
  g.gain.setValueAtTime(v||.16,AC.currentTime);
  g.gain.exponentialRampToValueAtTime(.001,
   AC.currentTime+d);
  o.connect(g);g.connect(AC.destination);
  o.start();o.stop(AC.currentTime+d);}catch(e){}}
function sndTurn(){if(!S.sound)return;
 beep(523,.14,"sine",.12);
 setTimeout(function(){beep(784,.14,"sine",.12)},130);
 setTimeout(function(){beep(1046,.42,"sine",.13)},260);}
function sndReach(){if(!S.sound)return;
 beep(311,.13,"square",.09);
 setTimeout(function(){beep(233,.13,"square",.09)},130);
 setTimeout(function(){beep(155,.34,"square",.10)},260);}
function sndPick(){if(!S.sound)return;
 beep(587,.05,"triangle",.045);}

function mk(el,arr,key,fmt){
 var h="";for(var i=0;i<arr.length;i++){
  var v=arr[i];
  h+='<button class="opt'+(S[key]==v[0]?' on':'')+
   '" onclick="setv(\\''+key+'\\',\\''+v[0]+'\\')">'+
   v[1]+'</button>';}
 document.getElementById(el).innerHTML=h;}
function setv(k,v){S[k]=isNaN(v)?v:+v;drawCfg();}
function bump(k,d){S[k]=Math.max(8,Math.min(20,S[k]+d));
 drawCfg();}
function bumpSlot(p,d){S.slots[p]=Math.max(0,
 Math.min(4,S.slots[p]+d));drawCfg();}
function randSlot(){S.slot=1+Math.floor(
 Math.random()*S.teams);drawCfg();}

function drawCfg(){
 mk("o-teams",[[8,"8"],[10,"10"],[12,"12"],[14,"14"]],"teams");
 mk("o-score",[["std","Non-PPR"],["half","Half PPR"],
  ["full","Full PPR"]],"score");
 mk("o-pat",[["snake","Snake"],["linear","Linear"],
  ["3rr","3rd Rd Reversal"]],"pat");
 mk("o-speed",[[2000,"Slow"],[1000,"Normal"],
  [400,"Fast"]],"speed");
 var sl=[];for(var i=1;i<=S.teams;i++)sl.push([i,i]);
 if(S.slot>S.teams)S.slot=S.teams;
 mk("o-slot",sl,"slot");
 document.getElementById("h-score").textContent=
  S.score=="full"?"1.0 per reception.":
  S.score=="half"?"0.5 points per reception.":
  "No points for receptions.";
 document.getElementById("v-rounds").textContent=S.rounds;
 document.getElementById("h-picks").textContent=
  (S.teams*S.rounds)+" total picks";
 var P=["QB","RB","WR","TE","FLEX","K","DST"],h="",st=0;
 for(var i=0;i<P.length;i++){var p=P[i];st+=S.slots[p];
  h+='<div class="slot s-'+p+'"><b>'+p+'</b>'+
   '<div class="stp"><button onclick="bumpSlot(\\''+p+
   '\\',-1)">&minus;</button><span>'+S.slots[p]+
   '</span><button onclick="bumpSlot(\\''+p+
   '\\',1)">+</button></div></div>';}
 document.getElementById("o-slots").innerHTML=h;
 document.getElementById("h-roster").textContent=
  st+" starters \\u00b7 "+Math.max(0,S.rounds-st)+" bench";
 document.getElementById("h-bench").textContent=
  st+" starters, "+Math.max(0,S.rounds-st)+
  " bench \\u2014 rounds set your total roster ("+
  S.rounds+" spots).";}

function revR(r){
 if(S.pat=="linear")return false;
 if(S.pat=="3rr")return r==1||(r>=2&&r%2==0);
 return r%2==1;}
function order(){
 var o=[];
 for(var r=0;r<S.rounds;r++){
  var a=[];for(var t=1;t<=S.teams;t++)a.push(t);
  if(revR(r))a.reverse();
  o=o.concat(a);}
 return o;}
</script>''')

W('''<script>
var ORD=[],NAMES=["Sammy Bot","Nathan Bot","Corey Bot",
 "FL Toilet Bot","ESPN Bot","Waiver Wire","Autodraft Al",
 "Bye Week Bill","Handcuff Hank","Zero RB Zeke",
 "Reach Rick","Sleeper Sam","Homer Hal","Chalk Charlie"];

var SL=null;
function adpFor(p){
 var a=p.rk;
 if(a==null||a<=0||a>=9000)a=(p.adp||300);
 if(S.score=="std"&&(p.pos=="WR"||p.pos=="TE"))a*=1.10;
 return a;}

function loadPool(){
 return Promise.all([
  fetch("_board.json?v="+Date.now())
   .then(function(r){return r.json()}),
  fetch("_statline.json?v="+Date.now())
   .then(function(r){return r.json()})
   .catch(function(){return {}})
 ]).then(function(a){
  var b=a[0]; SL=a[1]||{};
  var rows=(b.rows||b).filter(function(r){
   return r.n&&r.pos&&(r.live!=null)});
  rows.forEach(function(r){r._adp=adpFor(r)});
  rows.sort(function(a,c){return a._adp-c._adp});
  S.pool=rows.map(function(r,i){
   return {n:r.n,pos:r.pos,tm:r.tm||"",bye:r.bye||"",
    img:r.img||"",ppg:r.live||0,adp:i+1,pid:r.pid||"",
    rk:r.rk||i+1,taken:0}});
  return S.pool});}

function need(t){
 var mine=S.picks.filter(function(p){return p.t==t}),
  c={};
 mine.forEach(function(p){c[p.pl.pos]=(c[p.pl.pos]||0)+1});
 return c;}

function wantScore(pl,t){
 var c=need(t),have=c[pl.pos]||0,r=Math.floor(S.pick/S.teams);
 var cap={QB:1,TE:1,K:1,DST:1,RB:5,WR:6}[pl.pos]||4;
 if(have>=cap)return -999;
 if((pl.pos=="K"||pl.pos=="DST")&&r<S.rounds-3)return -999;
 if(pl.pos=="QB"&&have>=1&&r<S.rounds-2)return -999;
 var s=0;
 if(pl.pos=="RB"&&have<2)s+=14;
 if(pl.pos=="WR"&&have<2)s+=14;
 if(pl.pos=="TE"&&have<1&&r>3)s+=9;
 if(pl.pos=="QB"&&have<1&&r>5)s+=11;
 return s;}

function cpuPick(t){
 var av=S.pool.filter(function(p){return !p.taken}),
  best=null,bs=-1e9;
 for(var i=0;i<Math.min(av.length,26);i++){
  var p=av[i];
  var sc=-i*1.6+wantScore(p,t)+Math.random()*11;
  if(sc>bs){bs=sc;best=p}}
 return best||av[0];}

function take(pl,t){
 pl.taken=1;
 var over=S.pick+1-pl.adp;
 var rch=over<-24;
 S.picks.push({t:t,pl:pl,pk:S.pick+1,reach:rch,over:-over});
 if(rch&&t!=S.slot)sndReach();else sndPick();
 S.pick++;
 drawGrid();renderList();drawFeed();drawRoster();
 if(S.pick>=ORD.length){finish();return}
 schedule();}

function schedule(){
 clearTimeout(S.timer);clearInterval(S.tick);
 var t=ORD[S.pick];
 var me=(t==S.slot);
 document.getElementById("onclk").textContent=
  me?"Your Turn!":(NAMES[(t-1)%NAMES.length]+" is picking");
 document.getElementById("pkinfo").textContent=
  "Round "+(Math.floor(S.pick/S.teams)+1)+
  " \\u00b7 Pick "+(S.pick+1)+" of "+ORD.length;
 var c=document.getElementById("clk");
 c.className="clock"+(me?"":" wait");
 if(S.paused)return;
 if(me){sndTurn();S.left=30;c.textContent="0:30";
  S.tick=setInterval(function(){
   S.left--;c.textContent="0:"+(S.left<10?"0":"")+S.left;
   if(S.left<=0){clearInterval(S.tick);autoPick()}},1000);
  return}
 c.textContent="--";
 S.timer=setTimeout(function(){
  take(cpuPick(t),t)},S.speed);}

function userPick(i){
 if(ORD[S.pick]!=S.slot)return;
 clearInterval(S.tick);
 take(S.pool[i],S.slot);}
function autoPick(){var t=ORD[S.pick];take(cpuPick(t),t);}
function togglePause(){S.paused=!S.paused;
 document.getElementById("bp").textContent=
  S.paused?"Resume":"Pause";
 if(!S.paused)schedule();else{
  clearTimeout(S.timer);clearInterval(S.tick)}}
</script>''')

W('''<script>
function drawGrid(){
 var h='<table class="g"><thead><tr><th class="rh"></th>';
 for(var t=1;t<=S.teams;t++)
  h+='<th'+(t==S.slot?' class="meh"':'')+'>'+
   (t==S.slot?"YOU":
    NAMES[(t-1)%NAMES.length].split(" ")[0])+'</th>';
 h+='</tr></thead><tbody>';
 for(var r=0;r<S.rounds;r++){
  var rv=revR(r);
  h+='<tr><th class="rh">'+(r+1)+'</th>';
  for(var c=0;c<S.teams;c++){
   var pir=rv?(S.teams-c):(c+1);
   var idx=r*S.teams+(rv?(S.teams-1-c):c);
   var t=ORD[idx],pk=S.picks[idx],cl="c";
   if(t==S.slot)cl+=" me";
   if(idx==S.pick)cl+=" on";
   if(pk){cl+=" f p-"+pk.pl.pos;if(pk.reach)cl+=" rch"}
   var lastp=rv?(c===0):(c===S.teams-1);
   var ar=lastp?"\u2193":(rv?"\u2190":"\u2192");
   h+='<td class="'+cl+'"><em>'+(r+1)+'.'+pir+'</em>';
   if(pk)h+='<b>'+pk.pl.n+'</b><i>'+pk.pl.pos+
    ' \u00b7 '+pk.pl.tm+'</i>';
   h+='<s class="ar">'+ar+'</s></td>';}
  h+='</tr>';}
 document.getElementById("grid").innerHTML=h+'</tbody></table>';}

function renderList(){
 var q=(document.getElementById("q").value||"").toLowerCase();
 var me=(ORD[S.pick]==S.slot);
 function v(x){return (x==null||isNaN(x))?0:x;}
 var h='<table class="pl"><thead>'+
  '<tr class="grp"><th colspan="4"></th>'+
  '<th colspan="2">PROJ</th><th colspan="3">RUSHING</th>'+
  '<th colspan="3">RECEIVING</th>'+
  '<th colspan="3">PASSING</th><th></th></tr>'+
  '<tr class="hd2"><th>RK</th><th class="pn">PLAYER</th>'+
  '<th>ADP</th><th>BYE</th><th>PTS</th><th>AVG</th>'+
  '<th>ATT</th><th>YDS</th><th>TD</th>'+
  '<th>TAR</th><th>YDS</th><th>TD</th>'+
  '<th>ATT</th><th>YDS</th><th>TD</th><th></th></tr>'+
  '</thead><tbody>';
 var n=0;
 for(var i=0;i<S.pool.length&&n<90;i++){
  var p=S.pool[i];
  if(p.taken)continue;
  if(S.filter!="ALL"&&p.pos!=S.filter)continue;
  if(q&&p.n.toLowerCase().indexOf(q)<0)continue;
  n++;
  var t=(SL&&p.pid&&SL[p.pid])||{};
  h+='<tr><td class="rk">'+p.adp+'</td>'+
   '<td class="pn"><b>'+p.n+'</b><i><span class="pg '+
   p.pos+'">'+p.pos+'</span> '+p.tm+'</i></td>'+
   '<td>'+p.adp+'</td><td>'+(p.bye||"-")+'</td>'+
   '<td class="hi">'+(t.pts!=null?t.pts:p.ppg.toFixed(1))+
   '</td><td>'+(t.avg!=null?t.avg:p.ppg.toFixed(1))+'</td>'+
   '<td>'+v(t.car)+'</td><td>'+v(t.ryd)+'</td>'+
   '<td>'+v(t.rtd)+'</td><td>'+v(t.tar)+'</td>'+
   '<td>'+v(t.recyd)+'</td><td>'+v(t.rectd)+'</td>'+
   '<td>'+v(t.patt)+'</td><td>'+v(t.pyd)+'</td>'+
   '<td>'+v(t.ptd)+'</td>'+
   '<td><button onclick="userPick('+i+')"'+
   (me?"":" disabled")+'>Draft</button></td></tr>';}
 document.getElementById("plist").innerHTML=
  h+'</tbody></table>';}

function setFilt(i){
 var P=["ALL","QB","RB","WR","TE","K","DST"];
 S.filter=P[i];drawTabs();renderList();}
function drawTabs(){
 var P=["ALL","QB","RB","WR","TE","K","DST"],h="";
 var c=need(S.slot);
 var mine=S.picks.filter(function(p){return p.t==S.slot}).length;
 for(var i=0;i<P.length;i++){
  var lab=P[i],sub;
  if(lab=="ALL") sub=mine+"/"+S.rounds;
  else sub=(c[lab]||0)+"/"+(S.slots[lab]||0);
  h+='<button class="'+(S.filter==P[i]?"on":"")+
   '" onclick="setFilt('+i+')">'+lab+
   '<small>'+sub+'</small></button>';}
 document.getElementById("tabs").innerHTML=h;}

function drawFeed(){
 var h="",a=S.picks.slice(-8).reverse();
 for(var i=0;i<a.length;i++){var p=a[i];
  h+='<div class="fi">'+p.pk+'. <b>'+p.pl.n+'</b> ('+
   p.pl.pos+') \\u2192 '+(p.t==S.slot?"YOU":
   NAMES[(p.t-1)%NAMES.length])+
   (p.reach?'<span class="badge">REACH +'+p.over+
    '</span>':'')+'</div>';}
 document.getElementById("feed").innerHTML=h;}

function drawRoster(){
 var mine=S.picks.filter(function(p){return p.t==S.slot});
 var h="";
 for(var i=0;i<mine.length;i++)
  h+='<div class="rs"><span>'+mine[i].pl.pos+
   '</span><span>'+mine[i].pl.n+'</span></div>';
 document.getElementById("ros").innerHTML=
  h||'<div class="fi">No picks yet.</div>';}

function finish(){
 var mine=S.picks.filter(function(p){return p.t==S.slot});
 var tot=0,val=0;
 mine.forEach(function(p){tot+=p.pl.ppg;
  val+=(p.pl.adp-p.pk)});
 var all=[];
 for(var t=1;t<=S.teams;t++){
  var s=0;S.picks.filter(function(p){return p.t==t})
   .forEach(function(p){s+=p.pl.ppg});
  all.push({t:t,s:s})}
 all.sort(function(a,b){return b.s-a.s});
 var rank=all.findIndex(function(x){return x.t==S.slot})+1;
 var pct=rank/S.teams;
 var g=pct<=.17?"A":pct<=.34?"B+":pct<=.5?"B":
  pct<=.67?"C+":pct<=.84?"C":"D";
 document.getElementById("onclk").textContent="Draft Complete";
 document.getElementById("clk").textContent="\\u2713";
 var h='<div class="card" style="margin-top:12px">'+
  '<h1>Grade: '+g+'</h1><div class="sub">Projected '+
  tot.toFixed(1)+' ppg \\u00b7 ranked '+rank+' of '+
  S.teams+' \\u00b7 value vs ADP '+(val>0?"+":"")+val+
  '</div></div>';
 document.getElementById("feed").innerHTML=h+
  document.getElementById("feed").innerHTML;}

function startDraft(){
 ORD=order();
 document.getElementById("setup").style.display="none";
 document.getElementById("draft").style.display="";
 loadPool().then(function(){
  drawTabs();drawGrid();renderList();drawRoster();
  schedule();})
 .catch(function(e){
  document.getElementById("plist").innerHTML=
   '<div class="fi">Could not load player pool: '+e+
   '</div>';});}

drawCfg();
</script></div></body></html>''')

os.makedirs("site", exist_ok=True)
open("site/mock.html", "w").write(H.getvalue())
print("wrote site/mock.html (%d KB)"
      % (len(H.getvalue()) // 1024))
