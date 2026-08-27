import json
import pandas as pd
import nflreadpy as nfl

U = json.load(open("ui_data.json"))

C = pd.read_csv("coaching_2026.csv")
nc = 0
for _, r in C.iterrows():
    t = str(r["team"]).strip()
    if t not in U["teams"]:
        continue
    d = {}
    for k in ["head_coach", "off_coordinator",
              "def_coordinator", "scheme_note"]:
        v = r.get(k)
        d[k] = "" if v != v else str(v)
    U["teams"][t]["coach"] = d
    if d["head_coach"]:
        nc += 1
print("coaches filled: %d of %d" % (nc, len(U["teams"])))

S = nfl.load_schedules(seasons=[2026])
S = S.to_pandas() if hasattr(S, "to_pandas") else S
play = {}
for _, r in S.iterrows():
    w = int(r["week"])
    for c in ["home_team", "away_team"]:
        play.setdefault(str(r[c]), set()).add(w)
BYE = {}
for t, ws in play.items():
    miss = [w for w in range(1, 19) if w not in ws]
    BYE[t] = miss[0] if miss else 0
print("bye weeks: %d teams" % len(BYE))

def num(v, n=1):
    try:
        if v != v:
            return None
        return round(float(v), n)
    except Exception:
        return None

def txt(v):
    return "" if v != v else str(v)

B = pd.read_csv("board_final.csv", low_memory=False)
board = []
for _, r in B.sort_values("rank").iterrows():
    tm = txt(r["team"])
    board.append({"rk": int(r["rank"]),
                  "nm": txt(r["player_display_name"]),
                  "ps": txt(r["position"]),
                  "pr": int(r["pos_rank"]),
                  "tm": tm,
                  "pp": num(r["points"]),
                  "eg": num(r["exp_games"]),
                  "vp": num(r["vorp"], 2),
                  "ad": num(r["adp"]),
                  "st": txt(r["status"]),
                  "by": BYE.get(tm, 0),
                  "id": txt(r["player_id"])})

try:
    NEWS = json.load(open("news_2026.json"))
except Exception as e:
    NEWS = {"articles": [], "moves": [], "trades": []}
    print("news load failed: %s" % e)

BM = {x["nm"]: x for x in board}
MINE = []
try:
    R = pd.read_csv("my_roster.csv")
    for _, r in R.iterrows():
        nm = str(r["player"])
        h = BM.get(nm, {})
        MINE.append({"nm": nm, "ps": str(r["pos"]),
                     "sl": str(r["slot"]),
                     "tm": h.get("tm", ""),
                     "pp": h.get("pp"),
                     "eg": h.get("eg"),
                     "rk": h.get("rk"),
                     "st": h.get("st", ""),
                     "by": h.get("by", 0)})
    ms = [x["nm"] for x in MINE if x["pp"] is None]
    print("roster %d | unmatched %s" % (len(MINE), ms))
except Exception as e:
    print("roster load failed: %s" % e)

U["board"] = board
U["news"] = NEWS
U["mine"] = MINE
U["bye"] = BYE
U["meta"] = {"board": len(board), "coaches": nc,
             "teams": len(U["teams"]),
             "players": len(U["players"]),
             "injured": sum(1 for x in board if x["st"])}
DATA = json.dumps(U, separators=(",", ":"))
print("payload %.1f MB" % (len(DATA) / 1e6))

HEAD = """<!doctype html><html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VaporAI</title>
<style>
:root{
 --bg:#0b0d10; --panel:#15181e; --panel2:#1c2028;
 --line:#272c36; --text:#d8dee6; --dim:#8b95a5;
 --sky:#56c2ff; --sky2:#8fd8ff;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
 font:14px/1.5 -apple-system,BlinkMacSystemFont,
 "Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
header{background:var(--panel);
 border-bottom:1px solid var(--line);position:sticky;
 top:0;z-index:20}
.bar{display:flex;align-items:center;gap:16px;
 padding:14px 0;flex-wrap:wrap}
.brand{font-size:20px;font-weight:800;letter-spacing:1px}
.brand em{color:var(--sky);font-style:normal}
.sub{color:var(--dim);font-size:12px}
nav{margin-left:auto;display:flex;gap:6px;flex-wrap:wrap}
nav button{background:transparent;border:1px solid var(--line);
 color:var(--dim);border-radius:7px;padding:7px 13px;
 cursor:pointer;font-size:13px;font-weight:600}
nav button:hover{color:var(--text);border-color:var(--sky)}
nav button.on{background:var(--sky);color:#06222f;
 border-color:var(--sky)}
section{display:none;padding:22px 0 60px}
section.on{display:block}
h2{font-size:17px;margin:0 0 14px;font-weight:700}
h3.sec{font-size:14px;margin:26px 0 10px;
 color:var(--sky);font-weight:700;
 text-transform:uppercase;letter-spacing:.6px}
.cards{display:grid;gap:12px;
 grid-template-columns:repeat(auto-fill,minmax(210px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);
 border-radius:10px;padding:14px}
.card:hover{border-color:var(--sky)}
.kpi{font-size:26px;font-weight:800;color:var(--sky)}
.kpi-l{color:var(--dim);font-size:11px;
 text-transform:uppercase;letter-spacing:.7px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--dim);font-weight:600;
 font-size:11px;text-transform:uppercase;
 letter-spacing:.5px;padding:8px 9px;
 border-bottom:1px solid var(--line)}
td{padding:8px 9px;border-bottom:1px solid var(--panel2)}
tr:hover td{background:var(--panel)}
.hurt{color:#ff8f8f}
.tag{display:inline-block;background:var(--panel2);
 color:var(--sky2);border-radius:4px;padding:1px 6px;
 font-size:11px;margin-left:6px}
.bar2{display:flex;gap:10px;margin-bottom:14px;
 flex-wrap:wrap}
input,select{background:var(--panel);color:var(--text);
 border:1px solid var(--line);border-radius:7px;
 padding:8px 10px;font-size:13px}
input:focus,select:focus{outline:none;border-color:var(--sky)}
.tm{display:flex;align-items:center;gap:9px;
 margin-bottom:8px}
.tm img{width:26px;height:26px}
a{color:var(--sky);text-decoration:none}
a:hover{text-decoration:underline}
.note{color:var(--dim);font-size:12px;line-height:1.65;
 margin-top:14px}
.err{color:#ff8f8f;font-size:12px}
</style></head><body>
<header><div class="wrap"><div class="bar">
<span class="brand">VAPOR<em>AI</em></span>
<span class="sub">2026 Season</span>
<nav>
<button class="on" data-t="home">Home</button>
<button data-t="rosters">Rosters</button>
<button data-t="board">Rankings</button>
<button data-t="news">News</button>
<button data-t="trades">Trades</button>
<button data-t="calc">My Team</button>
</nav></div></div></header>
<div class="wrap">
<section class="on" id="home"></section>
<section id="rosters"></section>
<section id="board"></section>
<section id="news"></section>
<section id="trades"></section>
<section id="calc"></section>
</div>
<script>var D=__DATA__;</script>
<script>
"""

JS = """
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
  'from nflverse data under your league\\u2019s real Sleeper '+
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
console.log("vaporai ready");
</script></body></html>
"""

out = (HEAD + JS).replace("__DATA__", DATA)
with open("vaporai.html", "w") as f:
    f.write(out)
print("Saved vaporai.html  (%.1f MB)" % (len(out) / 1e6))
