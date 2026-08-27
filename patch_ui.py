import re
SRC = "99_ui_v3.py"
import shutil
shutil.copyfile("96_ui_v2.py", SRC)
print("fresh copy from 96_ui_v2.py")
s = open(SRC).read()

PY = '''
import json as _json
NEWS = {"articles": [], "moves": [], "trades": []}
try:
    NEWS = _json.load(open("news_2026.json"))
    print("news: %d articles, %d moves, %d trades"
          % (len(NEWS.get("articles", [])),
             len(NEWS.get("moves", [])),
             len(NEWS.get("trades", []))))
except Exception as _e:
    print("news_2026.json missing: %s" % _e)

BYE = {}
try:
    import nflreadpy as _nfl
    _s = _nfl.load_schedules(seasons=[2026])
    _s = _s.to_pandas() if hasattr(_s, "to_pandas") else _s
    if "game_type" in _s.columns:
        _s = _s[_s["game_type"] == "REG"]
    _wk = {}
    for _, _r in _s.iterrows():
        _wk.setdefault(_r["home_team"], set()).add(int(_r["week"]))
        _wk.setdefault(_r["away_team"], set()).add(int(_r["week"]))
    _all = set(range(1, 19))
    for _t, _w in _wk.items():
        _m = sorted(_all - _w)
        BYE[_t] = _m[0] if _m else 0
    print("bye weeks derived for %d teams" % len(BYE))
except Exception as _e:
    print("bye weeks unavailable: %s" % _e)

BIDX = {}
for _b in board:
    BIDX[_b["nm"]] = _b

MINE = []
try:
    _mr = pd.read_csv("my_roster.csv")
    for _, _r in _mr.iterrows():
        _nm = str(_r["player"]).strip()
        _h = BIDX.get(_nm, {})
        _tm = _h.get("tm", "")
        MINE.append({"nm": _nm, "ps": str(_r["pos"]).strip(),
                     "slot": str(_r["slot"]).strip(),
                     "pp": _h.get("pp"), "eg": _h.get("eg"),
                     "tm": _tm, "st": _h.get("st", ""),
                     "rk": _h.get("rk"),
                     "bye": BYE.get(_tm, 0)})
    _ms = [x["nm"] for x in MINE if x["pp"] is None]
    print("roster: %d players | %d not on board: %s"
          % (len(MINE), len(_ms), _ms))
except Exception as _e:
    print("my_roster.csv missing: %s" % _e)

for _b in board:
    _b["by"] = BYE.get(_b["tm"], 0)

U["news"] = NEWS
U["bye"] = BYE
U["mine"] = MINE
'''

A = 'DATA = json.dumps(U, separators=(",", ":"))'
assert A in s, "anchor A not found"
s = s.replace(A, PY + "\n" + A, 1)
open(SRC, "w").write(s)
print("block 1 injected")

s = open(SRC).read()

CSS = """
.sec{font-size:19px;margin:22px 0 10px;color:#012a56;
 border-bottom:2px solid #ffb612;padding-bottom:6px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.ncard{display:block;background:#fff;border:1px solid #dbe4ef;
 border-radius:10px;overflow:hidden;text-decoration:none;
 color:inherit;transition:box-shadow .15s}
.ncard:hover{box-shadow:0 4px 14px rgba(1,42,86,.15)}
.ncard img{width:100%;height:132px;object-fit:cover;display:block}
.nbody{padding:11px}
.nhd{font-weight:700;font-size:14px;line-height:1.35;color:#12243a}
.ndk{font-size:12px;color:#5a6b82;margin-top:6px;line-height:1.45}
.nmeta{font-size:11px;color:#8797ab;margin-top:8px}
.pill{background:#f26522;color:#fff;border-radius:3px;
 padding:1px 5px;font-weight:700;font-size:10px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.ck{display:block;font-size:13px;padding:4px 0;cursor:pointer}
.mut{color:#8797ab}
.vd{margin-top:16px;padding:16px;border-radius:10px;
 border-left:6px solid #012a56;background:#fff}
.big{font-size:30px;font-weight:800}
.good{color:#1f8a4c}.bad{color:#c0392b}
.flag{background:#fff4ed;border-left:4px solid #f26522;
 padding:8px 10px;margin:6px 0;font-size:13px;border-radius:4px}
#getin{padding:8px;width:60%;margin:8px 6px 8px 0}
</style></head><body>"""

B = "</style></head><body>"
assert B in s, "anchor B not found"
s = s.replace(B, CSS, 1)

C = '<button data-t="board">Rankings</button>'
assert C in s, "anchor C not found"
s = s.replace(C, C + '\n<button data-t="news">News</button>'
              '\n<button data-t="trades">Trades</button>'
              '\n<button data-t="calc">Trade Calc</button>', 1)

E = '<section id="board"></section>'
assert E in s, "anchor E not found"
s = s.replace(E, E + '\n<section id="news"></section>'
              '\n<section id="trades"></section>'
              '\n<section id="calc"></section>', 1)

open(SRC, "w").write(s)
print("block 2 injected")

JS1 = """
function E(x){return String(x==null?"":x)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}

function ncard(a){
 var im = a.img ? '<img src="'+E(a.img)+
   '" onerror="this.style.display=0?0:\\'none\\'">' : '';
 return '<a class="ncard" target="_blank" rel="noopener" href="'+
  E(a.url)+'">'+im+'<div class="nbody"><div class="nhd">'+
  E(a.hd)+'</div><div class="ndk">'+E(a.dk)+
  '</div><div class="nmeta">'+E(a.by||a.src)+' &middot; '+
  E(String(a.ts).slice(0,10))+
  (a.ins?' <span class="pill">BREAKING</span>':'')+
  '</div></div></a>';}

function drawNews(){
 var N=(D.news&&D.news.articles)||[];
 if(!N.length){$("news").innerHTML=
   '<div class="card">No articles. Run 98_news.py.</div>';return;}
 var br=N.filter(function(a){return a.ins;}).slice(0,6);
 var h='';
 if(br.length){h+='<h3 class="sec">Breaking &amp; Transactions</h3>'+
   '<div class="grid3">'+br.map(ncard).join('')+'</div>';}
 h+='<h3 class="sec">All NFL News ('+N.length+')</h3>'+
   '<div class="grid3">'+N.map(ncard).join('')+'</div>';
 h+='<p class="note">Source: CBS Sports NFL feed, built '+
   E((D.news&&D.news.built)||'')+
   '. ESPN blocks automated access, so Adam Schefter\\'s '+
   'reporting only appears here once another outlet writes it up.</p>';
 $("news").innerHTML=h;}

function drawTrades(){
 var T=(D.news&&D.news.trades)||[];
 var M=(D.news&&D.news.moves)||[];
 var pl=T.filter(function(t){return t.pfr_name&&t.pfr_name.trim();});
 var h='<h3 class="sec">2026 NFL Trades ('+pl.length+' players)</h3>';
 if(pl.length){
  h+='<table><tr><th>Date</th><th>Player</th><th>From</th>'+
     '<th>To</th></tr>';
  h+=pl.map(function(t){return '<tr><td>'+E(t.trade_date)+
    '</td><td>'+E(t.pfr_name)+'</td><td>'+E(t.gave)+
    '</td><td>'+E(t.received)+'</td></tr>';}).join('');
  h+='</table>';
 } else {h+='<div class="card">No 2026 player trades on file.</div>';}
 h+='<h3 class="sec">Offseason Movement &mdash; skill players who '+
    'changed teams</h3>';
 h+='<table><tr><th>Rk</th><th>Player</th><th>Pos</th>'+
    '<th>From</th><th>To</th><th>ppg</th></tr>';
 h+=M.map(function(m){
   var r=m.rank===""||m.rank==null?'--':Math.round(m.rank);
   var p=m.points===""||m.points==null?'--':Number(m.points).toFixed(1);
   return '<tr><td>'+r+'</td><td>'+E(m.player_display_name)+
    '</td><td>'+E(m.position)+'</td><td>'+E(m.from_tm)+
    '</td><td>'+E(m.to_tm)+'</td><td>'+p+'</td></tr>';}).join('');
 h+='</table><p class="note">Trades come from nflreadpy. '+
   'Movement compares each player\\'s last 2025 team to his 2026 '+
   'roster, so it includes free agency, not just trades.</p>';
 $("trades").innerHTML=h;}
"""
print("JS1 ready")

JS2 = """
var SLOTS=["QB","RB","RB","WR","WR","TE","FLEX","FLEX","DST","K"];
var FLAT={"K":9.7,"DST":7.0};
function pts(p){
 if(p.pp!=null)return p.pp;
 return FLAT[p.ps]!=null?FLAT[p.ps]:0;}

function lineup(list){
 var pool=list.map(function(p){
   return {nm:p.nm,ps:p.ps,pp:pts(p),bye:p.bye||0,used:false};});
 var tot=0,fill=[];
 SLOTS.forEach(function(s){
  var c=pool.filter(function(p){return !p.used&&(s=="FLEX"?
    ["RB","WR","TE"].indexOf(p.ps)>=0:p.ps==s);});
  c.sort(function(a,b){return b.pp-a.pp;});
  if(c.length){c[0].used=true;tot+=c[0].pp;fill.push(c[0]);}
  else fill.push(null);});
 return {tot:tot,fill:fill};}

function byeHoles(list){
 var out=[];
 for(var w=1;w<=18;w++){
  var av=list.filter(function(p){return (p.bye||0)!=w;});
  var L=lineup(av);
  var gaps=[];
  L.fill.forEach(function(f,i){if(!f)gaps.push(SLOTS[i]);});
  if(gaps.length)out.push({wk:w,gaps:gaps});}
 return out;}

function ncdf(z){
 var t=1/(1+0.2316419*Math.abs(z));
 var d=0.3989422804014327*Math.exp(-0.5*z*z);
 var q=d*t*(0.319381530+t*(-0.356563782+t*(1.781477937+
   t*(-1.821255978+t*1.330274429))));
 return z>=0?1-q:q;}

var GET=[];
function drawCalc(){
 var M=D.mine||[];
 if(!M.length){$("calc").innerHTML=
   '<div class="card">my_roster.csv not loaded.</div>';return;}
 var h='<h3 class="sec">Trade Calculator</h3>';
 h+='<p class="note">Change in your projected starting-lineup '+
  'points per week, computed off the same board the Rankings tab '+
  'uses. Bye-week gaps and injury flags are checked separately.</p>';
 h+='<div class="two"><div class="card"><b>You send</b><div>';
 h+=M.map(function(p,i){
  return '<label class="ck"><input type="checkbox" class="sx" '+
   'data-i="'+i+'"> '+E(p.nm)+' <span class="mut">'+E(p.ps)+
   ' '+E(p.tm)+' &middot; '+(p.pp==null?'flat':p.pp.toFixed(1))+
   ' ppg'+(p.st?' &middot; '+E(p.st):'')+'</span></label>';}).join('');
 h+='</div></div><div class="card"><b>You get</b><div>'+
  '<input id="getin" list="alln" placeholder="type a player name">'+
  '<button id="addb" class="cta">Add</button></div>'+
  '<div id="getL"></div></div></div>';
 h+='<datalist id="alln">'+D.board.slice(0,400).map(function(b){
  return '<option value="'+E(b.nm)+'">';}).join('')+'</datalist>';
 h+='<div id="verdict"></div>';
 $("calc").innerHTML=h;
 $("addb").onclick=function(){
  var v=$("getin").value.trim();
  var f=D.board.filter(function(b){return b.nm==v;})[0];
  if(!f){alert("not on the board: "+v);return;}
  GET.push({nm:f.nm,ps:f.ps,pp:f.pp,tm:f.tm,st:f.st,
            rk:f.rk,bye:f.by||0});
  $("getin").value="";run();};
 document.querySelectorAll(".sx").forEach(function(c){
  c.onchange=run;});
 run();}

function run(){
 var M=D.mine||[];
 var send=[];
 document.querySelectorAll(".sx").forEach(function(c){
  if(c.checked)send.push(M[+c.dataset.i]);});
 $("getL").innerHTML=GET.length?GET.map(function(p,i){
  return '<div class="ck">'+E(p.nm)+' <span class="mut">'+
   E(p.ps)+' '+E(p.tm)+' &middot; '+
   (p.pp==null?'flat':p.pp.toFixed(1))+' ppg'+
   (p.st?' &middot; '+E(p.st):'')+'</span> '+
   '<a href="#" onclick="GET.splice('+i+',1);run();return false;">'+
   'remove</a></div>';}).join(''):'<div class="mut">nobody yet</div>';

 var before=lineup(M);
 var keep=M.filter(function(p){return send.indexOf(p)<0;});
 var after=lineup(keep.concat(GET));
 var d=after.tot-before.tot;
 var wp=100*(ncdf(d/29.5)-0.5);

 var f=[];
 if(send.length>GET.length&&d<0)
  f.push("You are sending "+send.length+" for "+GET.length+
   " and losing points. Consolidation trades should gain points.");
 GET.forEach(function(p){if(p.st)
  f.push("Incoming: "+p.nm+" carries a "+p.st+
   " tag on the current injury report.");});
 send.forEach(function(p){if(!p.st&&p.pp!=null&&p.pp>13)
  f.push("Outgoing: "+p.nm+" is a healthy "+p.pp.toFixed(1)+
   " ppg starter.");});
 var bh=byeHoles(keep.concat(GET));
 bh.forEach(function(b){
  f.push("Week "+b.wk+": no one to start at "+b.gaps.join("/")+".");});

 var cls=d>0.5?"good":(d<-0.5?"bad":"");
 var v='<div class="vd"><div class="big '+cls+'">'+
  (d>=0?"+":"")+d.toFixed(2)+' pts/week</div>';
 v+='<div class="mut">lineup '+before.tot.toFixed(1)+
  ' &rarr; '+after.tot.toFixed(1)+
  ' &nbsp;|&nbsp; approx win probability '+
  (wp>=0?"+":"")+wp.toFixed(1)+'% per matchup</div>';
 if(!send.length&&!GET.length)
  v+='<p class="note">Select players on both sides.</p>';
 v+=f.map(function(x){
  return '<div class="flag">'+E(x)+'</div>';}).join('');
 v+='<p class="note">The win-probability figure is a normal '+
  'approximation using the measured 29.5-point margin spread, '+
  'not the 1M-season playoff simulation. Projections carry '+
  'measured year-over-year reliability of 0.765 for WRs down to '+
  '0.56 for QBs, so treat single-point edges as noise. What this '+
  'catches reliably is the mechanical stuff: uneven player counts, '+
  'incoming players already on the injury report, and bye weeks '+
  'where a trade leaves you unable to field a lineup.</p></div>';
 $("verdict").innerHTML=v;}
"""

s = open(SRC).read()
T = 'drawBoard();\\n</script></body></html>'
if T not in s:
    T = "drawBoard();\n</script></body></html>"
assert T in s, "anchor T not found"
s = s.replace(T, "drawBoard();\ndrawNews();drawTrades();drawCalc();\n"
              + JS1 + JS2 + "\n</script></body></html>", 1)
open(SRC, "w").write(s)
print("block 4 injected -- 99_ui_v3.py ready")
