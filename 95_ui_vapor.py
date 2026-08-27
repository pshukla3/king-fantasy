import json, pandas as pd

U = json.load(open("ui_data.json"))
B = pd.read_csv("board_final.csv", low_memory=False)
C = pd.read_csv("coaching_2026.csv").fillna("")

nc = 0
for _, r in C.iterrows():
    t = str(r["team"])
    if t not in U["teams"]:
        continue
    U["teams"][t]["coach"] = {
        "head_coach": str(r["head_coach"]).strip(),
        "off_coordinator": str(r["off_coordinator"]).strip(),
        "def_coordinator": str(r["def_coordinator"]).strip(),
        "scheme_note": str(r["scheme_note"]).strip()}
    if str(r["head_coach"]).strip():
        nc += 1

def num(v, d=1):
    return None if v != v else round(float(v), d)

def txt(v):
    return "" if v != v else str(v)

board = []
for _, r in B.sort_values("rank").iterrows():
    board.append({"rk": int(r["rank"]),
                  "nm": txt(r["player_display_name"]),
                  "ps": txt(r["position"]),
                  "pr": int(r["pos_rank"]),
                  "tm": txt(r["team"]),
                  "pp": num(r["points"]),
                  "eg": num(r["exp_games"]),
                  "vp": num(r["vorp"], 2),
                  "ad": num(r["adp"]),
                  "st": txt(r["status"]),
                  "id": txt(r["player_id"])})

U["board"] = board
U["meta"] = {"teams": len(U["teams"]),
             "players": len(U["players"]),
             "board": len(board),
             "coaches": nc,
             "injured": sum(1 for x in board if x["st"])}

DATA = json.dumps(U, separators=(",", ":"))
print("payload %.1f MB" % (len(DATA) / 1e6))
print("board %d | injured %d | coaches filled %d of 32"
      % (len(board), U["meta"]["injured"], nc))

HEAD = """<!doctype html><html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VaporAI</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0c11;color:#e6e8ee;
 font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1200px;margin:0 auto;padding:0 18px}
header{background:#0d1017;border-bottom:1px solid #1b2029;
 position:sticky;top:0;z-index:30}
.brand{font-size:24px;font-weight:800;letter-spacing:.16em;
 padding:18px 0 10px;display:inline-block;
 background:linear-gradient(90deg,#7bdff2,#b28dff,#ff8fd0);
 -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:#6f7891;font-size:12px;margin-left:12px;letter-spacing:.04em}
nav{display:flex;gap:4px}
nav button{background:none;border:0;color:#8b93a7;cursor:pointer;
 padding:11px 16px;font-size:13px;font-weight:600;
 border-bottom:2px solid transparent}
nav button.on{color:#fff;border-bottom-color:#b28dff}
section{display:none;padding:26px 0 60px}
section.on{display:block}
h2{font-size:15px;letter-spacing:.1em;text-transform:uppercase;
 color:#8b93a7;margin:22px 0 12px;font-weight:700}
.hero{padding:54px 0 30px;text-align:center}
.hero h1{font-size:44px;font-weight:800;letter-spacing:.02em;
 background:linear-gradient(90deg,#7bdff2,#b28dff,#ff8fd0);
 -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{color:#8b93a7;margin-top:12px;font-size:15px}
.stats{display:flex;gap:12px;justify-content:center;
 flex-wrap:wrap;margin-top:28px}
.stat{background:#11151e;border:1px solid #1e2431;border-radius:10px;
 padding:14px 20px;min-width:120px}
.stat b{display:block;font-size:22px;font-weight:800}
.stat span{color:#6f7891;font-size:11px;letter-spacing:.08em;
 text-transform:uppercase}
.grid{display:grid;gap:8px;
 grid-template-columns:repeat(auto-fill,minmax(96px,1fr))}
.tm{background:#11151e;border:1px solid #1e2431;border-radius:9px;
 padding:14px 6px;text-align:center;cursor:pointer;font-weight:800;
 letter-spacing:.06em;font-size:15px}
.tm:hover{border-color:#b28dff;background:#151a26}
.tm i{display:block;font-style:normal;font-size:10px;
 color:#6f7891;font-weight:600;margin-top:4px}
.coach{background:#11151e;border:1px solid #1e2431;border-radius:11px;
 padding:16px 18px;margin-bottom:16px;
 display:flex;flex-wrap:wrap;gap:26px;align-items:center}
.coach .who{font-size:19px;font-weight:800}
.coach .role{color:#6f7891;font-size:10px;letter-spacing:.1em;
 text-transform:uppercase}
.coach .empty{color:#6f7891;font-size:12px}
.subnav{display:flex;gap:4px;margin-bottom:16px;flex-wrap:wrap}
.subnav button{background:#11151e;border:1px solid #1e2431;
 color:#8b93a7;border-radius:7px;padding:8px 14px;cursor:pointer;
 font-size:11px;font-weight:700;letter-spacing:.08em}
.subnav button.on{color:#fff;border-color:#b28dff;background:#1a1426}
.cards{display:grid;gap:10px;
 grid-template-columns:repeat(auto-fill,minmax(258px,1fr))}
.card{background:#11151e;border:1px solid #1e2431;border-radius:11px;
 overflow:hidden}
.card .slot{background:#161b26;padding:6px 12px;font-size:10px;
 font-weight:800;letter-spacing:.12em;color:#8b93a7;
 border-bottom:1px solid #1e2431}
.row{display:flex;align-items:center;gap:10px;padding:9px 12px;
 cursor:pointer}
.row:hover{background:#161b26}
.row img{width:34px;height:34px;border-radius:50%;object-fit:cover;
 background:#1e2431;flex:none}
.row.bk img{width:24px;height:24px}
.row .nm{flex:1;min-width:0;font-weight:600;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row.bk{padding:6px 12px;border-top:1px solid #161b26}
.row.bk .nm{font-size:12px;color:#8b93a7;font-weight:500}
.badge{font-size:12px;font-weight:800;color:#7bdff2;flex:none}
.row.bk .badge{font-size:11px}
.hurt{color:#ff7b72}
.dot{color:#ff7b72;font-size:11px;flex:none}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:#6f7891;font-size:10px;font-weight:700;
 letter-spacing:.1em;text-transform:uppercase;padding:8px 10px;
 border-bottom:1px solid #1e2431;position:sticky;top:60px;
 background:#0a0c11}
td{padding:7px 10px;border-bottom:1px solid #141922}
tbody tr{cursor:pointer}
tbody tr:hover{background:#11151e}
input,select{background:#11151e;border:1px solid #1e2431;color:#e6e8ee;
 border-radius:7px;padding:8px 11px;font-size:13px;outline:none}
input:focus,select:focus{border-color:#b28dff}
.bar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.inj{background:#11151e;border:1px solid #2a1c22;border-radius:9px;
 padding:10px 13px;margin-bottom:7px}
.inj b{color:#ff7b72}
.inj i{font-style:normal;color:#6f7891;font-size:12px;display:block;
 margin-top:3px}
.modal{position:fixed;inset:0;background:rgba(4,6,10,.82);z-index:50;
 display:none;align-items:center;justify-content:center;padding:20px}
.modal.on{display:flex}
.box{background:#11151e;border:1px solid #262d3d;border-radius:14px;
 padding:22px;max-width:460px;width:100%}
.box h3{font-size:20px;margin-bottom:2px}
.box .meta{color:#6f7891;font-size:12px;margin-bottom:14px}
.kv{display:flex;justify-content:space-between;padding:6px 0;
 border-bottom:1px solid #171d28;font-size:13px}
.kv span{color:#8b93a7}
.close{margin-top:16px;width:100%;background:#1a1426;
 border:1px solid #2f2545;color:#cbb8ff;border-radius:8px;
 padding:9px;cursor:pointer;font-weight:700}
.note{color:#6f7891;font-size:12px;margin-top:14px}
</style></head><body>
<header><div class="wrap">
<span class="brand">VAPOR<span style="opacity:.75">AI</span></span>
<span class="sub" id="sub"></span>
<nav>
<button class="on" data-t="home">Home</button>
<button data-t="rosters">Rosters</button>
<button data-t="board">Rankings</button>
</nav></div></header>
<div class="wrap">
<section class="on" id="home"></section>
<section id="rosters"></section>
<section id="board"></section>
</div>
<div class="modal" id="modal"><div class="box" id="mbox"></div></div>
<script>const D=__DATA__;</script>
<script>
"""

JS = """
const $=id=>document.getElementById(id);
const OFF=["QB","RB","FB","WR","TE","LT","LG","C","RG","RT"];
const SPC=["PK","P","LS","H","KR","PR"];
let TEAM=null,GRP="offense";
function esc(s){return String(s==null?"":s)
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function P(id){return D.players[id]||{};}
function order(o,pref){
  const k=Object.keys(o);
  k.sort((a,b)=>{
    const x=pref.indexOf(a),y=pref.indexOf(b);
    if(x<0&&y<0)return a<b?-1:1;
    if(x<0)return 1; if(y<0)return -1; return x-y;});
  return k;}
function badge(p){
  return p.proj==null?"":p.proj.toFixed(1);}
function rowHTML(e,bk){
  const p=P(e.id),h=p.injury?' <span class="dot">&#9873;</span>':"";
  return '<div class="row'+(bk?" bk":"")+'" onclick="show(\\''+
    e.id+'\\')"><img loading="lazy" src="'+esc(p.img||e.img||"")+
    '"><div class="nm'+(p.injury?" hurt":"")+'">'+esc(e.name)+h+
    '</div><div class="badge">'+badge(p)+'</div></div>';}
function cards(){
  const g=D.teams[TEAM].depth[GRP]||{};
  const pref=GRP=="offense"?OFF:(GRP=="special"?SPC:[]);
  const ks=order(g,pref);
  if(!ks.length)return '<p class="note">no depth data</p>';
  return '<div class="cards">'+ks.map(k=>{
    const men=g[k]||[];
    if(!men.length)return "";
    return '<div class="card"><div class="slot">'+esc(k)+'</div>'+
      rowHTML(men[0],false)+
      men.slice(1,3).map(m=>rowHTML(m,true)).join("")+'</div>';
  }).join("")+'</div>';}
function injList(){
  const inj=D.teams[TEAM].injuries||[];
  if(!inj.length)return '<p class="note">no injuries on file</p>';
  return inj.map(i=>'<div class="inj"><b>'+esc(i.name)+'</b> '+
    esc(i.pos)+' &middot; '+esc(i.status)+' &middot; '+esc(i.inj)+
    '<i>'+esc(i.timeline||i.note||"")+'</i></div>').join("");}
function coachHTML(){
  const c=D.teams[TEAM].coach||{};
  const f=[["Head Coach",c.head_coach],
           ["Offensive Coordinator",c.off_coordinator],
           ["Defensive Coordinator",c.def_coordinator]]
    .filter(x=>x[1]);
  if(!f.length)return '<div class="coach"><span class="empty">'+
    'coaching staff not loaded &mdash; fill coaching_2026.csv'+
    '</span></div>';
  return '<div class="coach">'+f.map(x=>'<div>'+
    '<div class="role">'+x[0]+'</div>'+
    '<div class="who">'+esc(x[1])+'</div></div>').join("")+
    (c.scheme_note?'<div><div class="role">Scheme</div>'+
     '<div class="who">'+esc(c.scheme_note)+'</div></div>':"")+
    '</div>';}
function openTeam(t){
  TEAM=t;GRP="offense";drawTeam();window.scrollTo(0,0);}
function drawTeam(){
  const tabs=[["offense","Offense"],["defense","Defense"],
              ["special","Special Teams"]];
  $("rosters").innerHTML=
    '<button class="close" style="width:auto;padding:7px 14px" '+
    'onclick="drawGrid()">&larr; all teams</button>'+
    '<h2>'+esc(TEAM)+'</h2>'+coachHTML()+
    '<div class="subnav">'+tabs.map(x=>'<button class="'+
      (x[0]==GRP?"on":"")+'" onclick="GRP=\\''+x[0]+
      '\\';drawTeam()">'+x[1]+'</button>').join("")+'</div>'+
    cards()+'<h2>Injuries</h2>'+injList()+
    '<p class="note">badge = projected ppg. blank means the model '+
    'has no projection for that position &mdash; it is not a zero.</p>';}
function drawGrid(){
  TEAM=null;
  const ts=Object.keys(D.teams).sort();
  $("rosters").innerHTML='<h2>Select a team</h2><div class="grid">'+
    ts.map(t=>{
      const n=(D.teams[t].injuries||[]).length;
      return '<div class="tm" onclick="openTeam(\\''+t+'\\')">'+
        esc(t)+'<i>'+(n?n+" inj":"&nbsp;")+'</i></div>';
    }).join("")+'</div>';}
function drawBoard(){
  const pos=$("fpos")?$("fpos").value:"ALL";
  const q=($("fq")?$("fq").value:"").toLowerCase().trim();
  const rows=D.board.filter(b=>
    (pos=="ALL"||b.ps==pos)&&
    (!q||b.nm.toLowerCase().includes(q))).slice(0,400);
  $("btbl").innerHTML='<table><thead><tr><th>#</th><th>Player</th>'+
    '<th>Pos</th><th>Tm</th><th>PPG</th><th>Games</th><th>VORP</th>'+
    '<th>ADP</th><th>Status</th></tr></thead><tbody>'+
    rows.map(b=>'<tr onclick="show(\\''+b.id+'\\')"><td>'+b.rk+
      '</td><td'+(b.st?' class="hurt"':"")+'>'+esc(b.nm)+
      '</td><td>'+esc(b.ps)+b.pr+'</td><td>'+esc(b.tm)+
      '</td><td>'+(b.pp==null?"":b.pp.toFixed(1))+
      '</td><td>'+(b.eg==null?"":b.eg.toFixed(1))+
      '</td><td>'+(b.vp==null?"":(b.vp>0?"+":"")+b.vp.toFixed(1))+
      '</td><td>'+(b.ad==null?"":b.ad.toFixed(1))+
      '</td><td>'+esc(b.st)+'</td></tr>').join("")+
    '</tbody></table>';}
function show(id){
  const p=D.players[id];if(!p)return;
  const b=D.board.find(x=>x.id==id);
  const kv=(k,v)=>v==null||v===""?"":
    '<div class="kv"><span>'+k+'</span><b>'+v+'</b></div>';
  $("mbox").innerHTML='<h3>'+esc(p.name)+'</h3>'+
    '<div class="meta">'+esc(p.team)+' &middot; '+esc(p.pos)+
    ' &middot; depth '+esc(p.rank)+'</div>'+
    kv("Projected ppg",p.proj==null?null:p.proj.toFixed(1))+
    kv("VORP",p.vorp==null?null:p.vorp.toFixed(2))+
    kv("Expected games",p.exp_games==null?null:p.exp_games)+
    kv("Board rank",b?b.rk:null)+
    kv("ADP",b&&b.ad!=null?b.ad.toFixed(1):null)+
    kv("Career ppg",p.ppg==null?null:p.ppg.toFixed(1))+
    kv("Games sampled",p.games)+
    kv("Median / p90",p.med==null?null:
       p.med.toFixed(1)+" / "+p.p90.toFixed(1))+
    (p.injury?'<div class="inj" style="margin-top:12px"><b>'+
      esc(p.injury.status)+'</b> &middot; '+esc(p.injury.inj)+
      '<i>'+esc(p.injury.timeline||p.injury.note||"")+'</i></div>':"")+
    '<button class="close" onclick="hide()">Close</button>';
  $("modal").classList.add("on");}
function hide(){$("modal").classList.remove("on");}
function drawHome(){
  const m=D.meta;
  $("home").innerHTML='<div class="hero"><h1>Welcome to VaporAI</h1>'+
    '<p>A fantasy football engine that only trusts what it can '+
    'measure.</p><div class="stats">'+
    [[m.teams,"Teams"],[m.players,"Players"],[m.board,"Ranked"],
     [m.injured,"Injured"]].map(x=>'<div class="stat"><b>'+x[0]+
      '</b><span>'+x[1]+'</span></div>').join("")+'</div></div>'+
    '<h2>What is measured</h2>'+
    '<p class="note">Year-over-year reliability: WR 0.765, TE 0.733,'+
    ' RB 0.709, QB 0.56. Rankings blend the model 50/50 with market '+
    'ADP. Injury effects come from 864 historical spells, and any '+
    'number without a measured basis is labelled as such rather than '+
    'quietly used.</p>';}
document.querySelectorAll("nav button").forEach(b=>{
  b.onclick=()=>{
    document.querySelectorAll("nav button").forEach(x=>
      x.classList.remove("on"));
    document.querySelectorAll("section").forEach(x=>
      x.classList.remove("on"));
    b.classList.add("on");$(b.dataset.t).classList.add("on");};});
$("modal").onclick=e=>{if(e.target.id=="modal")hide();};
document.addEventListener("keydown",e=>{if(e.key=="Escape")hide();});
$("sub").textContent="2026 season";
drawHome();drawGrid();
$("board").innerHTML='<div class="bar">'+
  '<input id="fq" placeholder="search player">'+
  '<select id="fpos"><option>ALL</option><option>QB</option>'+
  '<option>RB</option><option>WR</option><option>TE</option>'+
  '<option>K</option><option>DST</option></select></div>'+
  '<div id="btbl"></div>';
$("fq").oninput=drawBoard;$("fpos").onchange=drawBoard;
drawBoard();
</script></body></html>
"""

out = (HEAD + JS).replace("__DATA__", DATA)
with open("vaporai.html", "w") as f:
    f.write(out)
print("Saved vaporai.html  (%.1f MB)" % (len(out) / 1e6))
