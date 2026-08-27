import json, pandas as pd

TM = {
 "ARI": ("Arizona Cardinals", "ari", "NFC West"),
 "ATL": ("Atlanta Falcons", "atl", "NFC South"),
 "BAL": ("Baltimore Ravens", "bal", "AFC North"),
 "BUF": ("Buffalo Bills", "buf", "AFC East"),
 "CAR": ("Carolina Panthers", "car", "NFC South"),
 "CHI": ("Chicago Bears", "chi", "NFC North"),
 "CIN": ("Cincinnati Bengals", "cin", "AFC North"),
 "CLE": ("Cleveland Browns", "cle", "AFC North"),
 "DAL": ("Dallas Cowboys", "dal", "NFC East"),
 "DEN": ("Denver Broncos", "den", "AFC West"),
 "DET": ("Detroit Lions", "det", "NFC North"),
 "GB": ("Green Bay Packers", "gb", "NFC North"),
 "HOU": ("Houston Texans", "hou", "AFC South"),
 "IND": ("Indianapolis Colts", "ind", "AFC South"),
 "JAX": ("Jacksonville Jaguars", "jax", "AFC South"),
 "KC": ("Kansas City Chiefs", "kc", "AFC West"),
 "LA": ("Los Angeles Rams", "lar", "NFC West"),
 "LAC": ("Los Angeles Chargers", "lac", "AFC West"),
 "LV": ("Las Vegas Raiders", "lv", "AFC West"),
 "MIA": ("Miami Dolphins", "mia", "AFC East"),
 "MIN": ("Minnesota Vikings", "min", "NFC North"),
 "NE": ("New England Patriots", "ne", "AFC East"),
 "NO": ("New Orleans Saints", "no", "NFC South"),
 "NYG": ("New York Giants", "nyg", "NFC East"),
 "NYJ": ("New York Jets", "nyj", "AFC East"),
 "PHI": ("Philadelphia Eagles", "phi", "NFC East"),
 "PIT": ("Pittsburgh Steelers", "pit", "AFC North"),
 "SEA": ("Seattle Seahawks", "sea", "NFC West"),
 "SF": ("San Francisco 49ers", "sf", "NFC West"),
 "TB": ("Tampa Bay Buccaneers", "tb", "NFC South"),
 "TEN": ("Tennessee Titans", "ten", "AFC South"),
 "WAS": ("Washington Commanders", "wsh", "NFC East"),
}
ALIAS = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX",
         "STL": "LA", "SD": "LAC", "OAK": "LV"}

U = json.load(open("ui_data.json"))
B = pd.read_csv("board_final.csv", low_memory=False)
C = pd.read_csv("coaching_2026.csv").fillna("")

bad = [k for k in U["teams"] if k not in TM and k not in ALIAS]
print("team keys with no logo mapping: %s" % (bad if bad else "none"))

meta = {}
for k in U["teams"]:
    kk = ALIAS.get(k, k)
    if kk in TM:
        n, slug, div = TM[kk]
        meta[k] = {"name": n, "div": div,
                   "logo": "https://a.espncdn.com/i/teamlogos/"
                           "nfl/500/%s.png" % slug}
    else:
        meta[k] = {"name": k, "div": "", "logo": ""}

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
                  "ps": txt(r["position"]), "pr": int(r["pos_rank"]),
                  "tm": txt(r["team"]), "pp": num(r["points"]),
                  "eg": num(r["exp_games"]), "vp": num(r["vorp"], 2),
                  "ad": num(r["adp"]), "st": txt(r["status"]),
                  "id": txt(r["player_id"])})

U["board"] = board
U["tmeta"] = meta
U["meta"] = {"teams": len(U["teams"]), "players": len(U["players"]),
             "board": len(board), "coaches": nc,
             "injured": sum(1 for x in board if x["st"])}
DATA = json.dumps(U, separators=(",", ":"))
print("payload %.1f MB | board %d | injured %d | coaches %d of 32"
      % (len(DATA) / 1e6, len(board), U["meta"]["injured"], nc))

HEAD = """<!doctype html><html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VaporAI</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#f4f7fb;color:#12243a;
 font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1220px;margin:0 auto;padding:0 20px}
header{background:linear-gradient(135deg,#012a56,#01498f);
 position:sticky;top:0;z-index:30;
 box-shadow:0 2px 10px rgba(1,42,86,.18)}
header .bar{display:flex;align-items:flex-end;gap:24px;flex-wrap:wrap}
.brand{font-size:25px;font-weight:800;letter-spacing:.13em;
 color:#fff;padding:16px 0 12px}
.brand em{font-style:normal;
 background:linear-gradient(90deg,#ffb612,#f26522);
 -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:rgba(255,255,255,.6);font-size:11px;letter-spacing:.1em;
 text-transform:uppercase;padding-bottom:16px}
nav{display:flex;gap:2px;margin-left:auto}
nav button{background:none;border:0;color:rgba(255,255,255,.72);
 padding:13px 18px;font-size:13px;font-weight:700;cursor:pointer;
 letter-spacing:.04em;border-bottom:3px solid transparent}
nav button:hover{color:#fff}
nav button.on{color:#fff;border-bottom-color:#ffb612}
.gold{height:3px;background:linear-gradient(90deg,#ffb612,#f26522)}
section{display:none;padding:26px 0 70px}
section.on{display:block}
h2{font-size:13px;letter-spacing:.11em;text-transform:uppercase;
 color:#5a6b82;margin:24px 0 12px;font-weight:800}
.hero{background:#fff;border:1px solid #dfe6ef;border-radius:14px;
 padding:44px 36px;text-align:center;
 box-shadow:0 1px 3px rgba(18,36,58,.05)}
.hero h1{font-size:40px;font-weight:800;color:#012a56;
 letter-spacing:-.01em}
.hero h1 em{font-style:normal;
 background:linear-gradient(90deg,#ffb612,#f26522);
 -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{color:#5a6b82;margin-top:12px;font-size:16px}
.cta{margin-top:22px;background:#f26522;color:#fff;border:0;
 border-radius:8px;padding:12px 26px;font-size:14px;font-weight:700;
 cursor:pointer}
.cta:hover{background:#d9530f}
.stats{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;
 margin-top:30px}
.stat{background:#f4f7fb;border:1px solid #e2e9f2;border-radius:10px;
 padding:14px 22px;min-width:118px}
.stat b{display:block;font-size:23px;font-weight:800;color:#012a56}
.stat span{color:#7385a0;font-size:10px;letter-spacing:.09em;
 text-transform:uppercase;font-weight:700}
.divs{display:grid;gap:14px;
 grid-template-columns:repeat(auto-fit,minmax(258px,1fr))}
.div{background:#fff;border:1px solid #dfe6ef;border-radius:11px;
 padding:14px 16px 8px}
.div h3{font-size:13px;color:#012a56;font-weight:800;
 letter-spacing:.05em;padding-bottom:8px;
 border-bottom:2px solid #ffb612;margin-bottom:6px}
.trow{display:flex;align-items:center;gap:11px;padding:8px 6px;
 border-radius:7px;cursor:pointer;font-weight:600;color:#12243a}
.trow:hover{background:#eef4fb}
.trow img{width:26px;height:26px;object-fit:contain;flex:none}
.trow .n{flex:1}
.trow .flag{font-size:10px;font-weight:800;color:#c0392b;
 background:#fdeceb;border-radius:20px;padding:2px 8px}
.thead{background:#fff;border:1px solid #dfe6ef;border-radius:12px;
 padding:18px 20px;margin-bottom:14px;display:flex;
 align-items:center;gap:18px;flex-wrap:wrap;
 border-left:5px solid #012a56}
.thead img{width:54px;height:54px;object-fit:contain}
.thead .tn{font-size:24px;font-weight:800;color:#012a56}
.thead .td{color:#7385a0;font-size:11px;font-weight:700;
 letter-spacing:.09em;text-transform:uppercase}
.staff{display:flex;gap:26px;flex-wrap:wrap;margin-left:auto}
.staff .role{color:#7385a0;font-size:9px;letter-spacing:.1em;
 text-transform:uppercase;font-weight:800}
.staff .who{font-weight:700;color:#12243a}
.staff .empty{color:#8b9bb2;font-size:12px}
.back{background:#fff;border:1px solid #dfe6ef;color:#012a56;
 border-radius:8px;padding:8px 15px;font-weight:700;cursor:pointer;
 font-size:13px;margin-bottom:14px}
.back:hover{background:#eef4fb}
.subnav{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.subnav button{background:#fff;border:1px solid #dfe6ef;color:#12243a;
 border-radius:30px;padding:9px 20px;cursor:pointer;font-size:12px;
 font-weight:700;letter-spacing:.05em}
.subnav button.on{background:#012a56;border-color:#012a56;color:#fff}
.cards{display:grid;gap:12px;
 grid-template-columns:repeat(auto-fill,minmax(262px,1fr))}
.card{background:#fff;border:1px solid #dfe6ef;border-radius:11px;
 overflow:hidden;box-shadow:0 1px 2px rgba(18,36,58,.04)}
.card .slot{background:#eef4fb;padding:7px 13px;font-size:10px;
 font-weight:800;letter-spacing:.12em;color:#012a56;
 border-bottom:1px solid #dfe6ef}
.row{display:flex;align-items:center;gap:11px;padding:10px 13px;
 cursor:pointer}
.row:hover{background:#f7fafd}
.row img{width:36px;height:36px;border-radius:50%;object-fit:cover;
 background:#eef4fb;flex:none}
.row .nm{flex:1;min-width:0;font-weight:700;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row.bk{padding:7px 13px;border-top:1px solid #f0f4f9;
 background:#fcfdfe}
.row.bk img{width:25px;height:25px}
.row.bk .nm{font-size:12px;color:#5a6b82;font-weight:500}
.badge{font-size:13px;font-weight:800;color:#e8590c;flex:none}
.row.bk .badge{font-size:11px;color:#f0851f}
.hurt{color:#c0392b}
.dot{color:#c0392b;font-size:11px}
.panel{background:#fff;border:1px solid #dfe6ef;border-radius:12px;
 overflow:hidden}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:#012a56;font-size:10px;font-weight:800;
 letter-spacing:.1em;text-transform:uppercase;padding:11px 12px;
 background:#eef4fb;border-bottom:1px solid #dfe6ef}
td{padding:9px 12px;border-bottom:1px solid #f0f4f9}
tbody tr{cursor:pointer}
tbody tr:hover{background:#f7fafd}
input,select{background:#fff;border:1px solid #dfe6ef;color:#12243a;
 border-radius:8px;padding:9px 12px;font-size:13px;outline:none}
input:focus,select:focus{border-color:#012a56}
.bar2{display:flex;gap:9px;margin-bottom:13px;flex-wrap:wrap}
.inj{background:#fff;border:1px solid #f0dcda;border-left:4px solid
 #c0392b;border-radius:9px;padding:11px 14px;margin-bottom:8px}
.inj b{color:#c0392b}
.inj i{font-style:normal;color:#5a6b82;font-size:12px;display:block;
 margin-top:3px}
.modal{position:fixed;inset:0;background:rgba(1,42,86,.45);z-index:50;
 display:none;align-items:center;justify-content:center;padding:20px}
.modal.on{display:flex}
.box{background:#fff;border-radius:14px;padding:24px;max-width:470px;
 width:100%;box-shadow:0 20px 50px rgba(1,42,86,.3)}
.box h3{font-size:21px;color:#012a56}
.box .meta{color:#7385a0;font-size:12px;margin-bottom:15px}
.kv{display:flex;justify-content:space-between;padding:7px 0;
 border-bottom:1px solid #f0f4f9;font-size:13px}
.kv span{color:#5a6b82}
.close{margin-top:17px;width:100%;background:#012a56;border:0;
 color:#fff;border-radius:8px;padding:10px;cursor:pointer;
 font-weight:700}
.note{color:#7385a0;font-size:12px;margin-top:14px;line-height:1.6}
</style></head><body>
<header><div class="wrap"><div class="bar">
<span class="brand">VAPOR<em>AI</em></span>
<span class="sub">2026 Season</span>
<nav>
<button class="on" data-t="home">Home</button>
<button data-t="rosters">Rosters</button>
<button data-t="board">Rankings</button>
</nav></div></div><div class="gold"></div></header>
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
const DIVS=["AFC East","AFC North","AFC South","AFC West",
            "NFC East","NFC North","NFC South","NFC West"];
let TEAM=null,GRP="offense";
function esc(s){return String(s==null?"":s)
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function P(id){return D.players[id]||{};}
function M(t){return D.tmeta[t]||{name:t,div:"",logo:""};}
function go(t){
  document.querySelectorAll("nav button").forEach(x=>
    x.classList.toggle("on",x.dataset.t==t));
  document.querySelectorAll("section").forEach(x=>
    x.classList.toggle("on",x.id==t));
  window.scrollTo(0,0);}
function rowHTML(e,bk){
  const p=P(e.id),h=p.injury?' <span class="dot">&#9873;</span>':"";
  const b=p.proj==null?"":p.proj.toFixed(1);
  return '<div class="row'+(bk?" bk":"")+'" onclick="show(\\''+
    e.id+'\\')"><img loading="lazy" src="'+esc(p.img||e.img||"")+
    '" onerror="this.style.visibility=\\'hidden\\'"><div class="nm'+
    (p.injury?" hurt":"")+'">'+esc(e.name)+h+
    '</div><div class="badge">'+b+'</div></div>';}
function cards(){
  const g=D.teams[TEAM].depth[GRP]||{};
  const pref=GRP=="offense"?OFF:(GRP=="special"?SPC:[]);
  const ks=Object.keys(g).sort((a,b)=>{
    const x=pref.indexOf(a),y=pref.indexOf(b);
    if(x<0&&y<0)return a<b?-1:1;
    if(x<0)return 1; if(y<0)return -1; return x-y;});
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
function staffHTML(){
  const c=D.teams[TEAM].coach||{};
  const f=[["Head Coach",c.head_coach],
           ["Off. Coordinator",c.off_coordinator],
           ["Def. Coordinator",c.def_coordinator],
           ["Scheme",c.scheme_note]].filter(x=>x[1]);
  if(!f.length)return '<div class="staff"><span class="empty">'+
    'coaching staff not loaded</span></div>';
  return '<div class="staff">'+f.map(x=>'<div>'+
    '<div class="role">'+x[0]+'</div><div class="who">'+
    esc(x[1])+'</div></div>').join("")+'</div>';}
function openTeam(t){TEAM=t;GRP="offense";drawTeam();
  window.scrollTo(0,0);}
function drawTeam(){
  const m=M(TEAM);
  const tabs=[["offense","Offense"],["defense","Defense"],
              ["special","Special Teams"]];
  $("rosters").innerHTML=
    '<button class="back" onclick="drawGrid()">&larr; All Teams'+
    '</button><div class="thead"><img src="'+esc(m.logo)+
    '" onerror="this.style.display=\\'none\\'"><div>'+
    '<div class="tn">'+esc(m.name)+'</div>'+
    '<div class="td">'+esc(m.div)+' &middot; '+esc(TEAM)+
    '</div></div>'+staffHTML()+'</div>'+
    '<div class="subnav">'+tabs.map(x=>'<button class="'+
      (x[0]==GRP?"on":"")+'" onclick="GRP=\\''+x[0]+
      '\\';drawTeam()">'+x[1]+'</button>').join("")+'</div>'+
    cards()+'<h2>Injury Report</h2>'+injList()+
    '<p class="note">Orange badge = projected points per game. '+
    'Blank means the model carries no projection for that '+
    'position &mdash; it is not a zero.</p>';}
function drawGrid(){
  TEAM=null;
  const by={};
  Object.keys(D.teams).forEach(t=>{
    const d=M(t).div||"Other";
    (by[d]=by[d]||[]).push(t);});
  const keys=DIVS.filter(d=>by[d]).concat(
    Object.keys(by).filter(d=>DIVS.indexOf(d)<0));
  $("rosters").innerHTML='<h2>Teams</h2><div class="divs">'+
    keys.map(d=>'<div class="div"><h3>'+esc(d)+'</h3>'+
      by[d].sort((a,b)=>M(a).name<M(b).name?-1:1).map(t=>{
        const n=(D.teams[t].injuries||[]).length;
        return '<div class="trow" onclick="openTeam(\\''+t+
          '\\')"><img src="'+esc(M(t).logo)+
          '" onerror="this.style.visibility=\\'hidden\\'">'+
          '<span class="n">'+esc(M(t).name)+'</span>'+
          (n?'<span class="flag">'+n+'</span>':"")+'</div>';
      }).join("")+'</div>').join("")+'</div>'+
    '<p class="note">Red count = players on that team&rsquo;s '+
    'injury report.</p>';}
function drawBoard(){
  const pos=$("fpos")?$("fpos").value:"ALL";
  const q=($("fq")?$("fq").value:"").toLowerCase().trim();
  const rows=D.board.filter(b=>(pos=="ALL"||b.ps==pos)&&
    (!q||b.nm.toLowerCase().includes(q))).slice(0,400);
  $("btbl").innerHTML='<div class="panel"><table><thead><tr>'+
    '<th>#</th><th>Player</th><th>Pos</th><th>Team</th><th>PPG</th>'+
    '<th>Games</th><th>VORP</th><th>ADP</th><th>Status</th></tr>'+
    '</thead><tbody>'+rows.map(b=>'<tr onclick="show(\\''+b.id+
      '\\')"><td>'+b.rk+'</td><td'+(b.st?' class="hurt"':"")+
      '><b>'+esc(b.nm)+'</b></td><td>'+esc(b.ps)+b.pr+
      '</td><td>'+esc(b.tm)+'</td><td>'+
      (b.pp==null?"":b.pp.toFixed(1))+'</td><td>'+
      (b.eg==null?"":b.eg.toFixed(1))+'</td><td>'+
      (b.vp==null?"":(b.vp>0?"+":"")+b.vp.toFixed(1))+'</td><td>'+
      (b.ad==null?"":b.ad.toFixed(1))+'</td><td>'+esc(b.st)+
      '</td></tr>').join("")+'</tbody></table></div>';}
function show(id){
  const p=D.players[id];if(!p)return;
  const b=D.board.find(x=>x.id==id);
  const kv=(k,v)=>v==null||v===""?"":
    '<div class="kv"><span>'+k+'</span><b>'+v+'</b></div>';
  $("mbox").innerHTML='<h3>'+esc(p.name)+'</h3>'+
    '<div class="meta">'+esc(M(p.team).name)+' &middot; '+
    esc(p.pos)+' &middot; depth '+esc(p.rank)+'</div>'+
    kv("Projected ppg",p.proj==null?null:p.proj.toFixed(1))+
    kv("VORP",p.vorp==null?null:p.vorp.toFixed(2))+
    kv("Expected games",p.exp_games==null?null:p.exp_games)+
    kv("Board rank",b?b.rk:null)+
    kv("ADP",b&&b.ad!=null?b.ad.toFixed(1):null)+
    kv("Career ppg",p.ppg==null?null:p.ppg.toFixed(1))+
    kv("Games sampled",p.games)+
    kv("Median / p90",p.med==null?null:
       p.med.toFixed(1)+" / "+p.p90.toFixed(1))+
    (p.injury?'<div class="inj" style="margin-top:13px"><b>'+
      esc(p.injury.status)+'</b> &middot; '+esc(p.injury.inj)+
      '<i>'+esc(p.injury.timeline||p.injury.note||"")+
      '</i></div>':"")+
    '<button class="close" onclick="hide()">Close</button>';
  $("modal").classList.add("on");}
function hide(){$("modal").classList.remove("on");}
function drawHome(){
  const m=D.meta;
  $("home").innerHTML='<div class="hero">'+
    '<h1>Welcome to Vapor<em>AI</em></h1>'+
    '<p>A fantasy football engine that only trusts what it can '+
    'measure.</p>'+
    '<button class="cta" onclick="go(\\'rosters\\')">'+
    'Browse Team Rosters</button><div class="stats">'+
    [[m.teams,"Teams"],[m.players,"Players"],[m.board,"Ranked"],
     [m.injured,"Injured"]].map(x=>'<div class="stat"><b>'+x[0]+
      '</b><span>'+x[1]+'</span></div>').join("")+
    '</div></div><h2>What Is Measured</h2>'+
    '<div class="panel" style="padding:18px 20px">'+
    '<p class="note" style="margin:0">Year-over-year reliability: '+
    'WR 0.765, TE 0.733, RB 0.709, QB 0.56. Rankings blend the '+
    'model 50/50 with market ADP. Injury effects are derived from '+
    '864 historical injury spells, and any figure without a '+
    'measured basis is labelled rather than quietly used.</p>'+
    '</div>';}
document.querySelectorAll("nav button").forEach(b=>{
  b.onclick=()=>go(b.dataset.t);});
$("modal").onclick=e=>{if(e.target.id=="modal")hide();};
document.addEventListener("keydown",e=>{if(e.key=="Escape")hide();});
drawHome();drawGrid();
$("board").innerHTML='<div class="bar2">'+
  '<input id="fq" placeholder="Search player">'+
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
