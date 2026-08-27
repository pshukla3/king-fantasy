import json

NICK = {
 "BUF": "Bills", "MIA": "Dolphins", "NE": "Patriots",
 "NYJ": "Jets", "BAL": "Ravens", "CIN": "Bengals",
 "CLE": "Browns", "PIT": "Steelers", "HOU": "Texans",
 "IND": "Colts", "JAX": "Jaguars", "TEN": "Titans",
 "DEN": "Broncos", "KC": "Chiefs", "LV": "Raiders",
 "LAC": "Chargers", "DAL": "Cowboys", "NYG": "Giants",
 "PHI": "Eagles", "WAS": "Commanders", "CHI": "Bears",
 "DET": "Lions", "GB": "Packers", "MIN": "Vikings",
 "ATL": "Falcons", "CAR": "Panthers", "NO": "Saints",
 "TB": "Buccaneers", "ARI": "Cardinals", "LA": "Rams",
 "SF": "49ers", "SEA": "Seahawks"}

DIVS = [
 ("AFC East", ["BUF", "MIA", "NE", "NYJ"]),
 ("AFC North", ["BAL", "CIN", "CLE", "PIT"]),
 ("AFC South", ["HOU", "IND", "JAX", "TEN"]),
 ("AFC West", ["DEN", "KC", "LV", "LAC"]),
 ("NFC East", ["DAL", "NYG", "PHI", "WAS"]),
 ("NFC North", ["CHI", "DET", "GB", "MIN"]),
 ("NFC South", ["ATL", "CAR", "NO", "TB"]),
 ("NFC West", ["ARI", "LA", "SF", "SEA"])]

ESPN = {
 "ARI": "ari", "ATL": "atl", "BAL": "bal", "BUF": "buf",
 "CAR": "car", "CHI": "chi", "CIN": "cin", "CLE": "cle",
 "DAL": "dal", "DEN": "den", "DET": "det", "GB": "gb",
 "HOU": "hou", "IND": "ind", "JAX": "jax", "KC": "kc",
 "LV": "lv", "LAC": "lac", "LA": "lar", "MIA": "mia",
 "MIN": "min", "NE": "ne", "NO": "no", "NYG": "nyg",
 "NYJ": "nyj", "PHI": "phi", "PIT": "pit", "SF": "sf",
 "SEA": "sea", "TB": "tb", "TEN": "ten", "WAS": "wsh"}
LG = {}
for k, v in ESPN.items():
    LG[k] = "https://a.espncdn.com/i/teamlogos/nfl/500/%s.png" % v

CSS = """
<style>
:root{
 --bg:#050506; --panel:#0b0b0e; --panel2:#111116;
 --line:#1b1b21; --text:#e4e7ec; --dim:#767c88;
 --sky:#4db8ff; --sky2:#93dbff;
}
body{background:#050506;
 -webkit-font-smoothing:antialiased;letter-spacing:-.005em}
header{background:#050506;border-bottom:1px solid #1b1b21}
.scorebar{background:#08080a;border-bottom:1px solid #1b1b21}
.sbc{border-right:1px solid #16161b}
.welc{background:linear-gradient(105deg,#0d1219,#050506);
 border:1px solid #1b1b21}
.welc h1{letter-spacing:-.02em}
.hero{border:1px solid #1b1b21}
.hgrad{background:linear-gradient(to top,
 rgba(3,3,4,.98) 10%,rgba(3,3,4,.55) 50%,rgba(3,3,4,0) 82%)}
section,.card,table{background:transparent}
nav button{color:#767c88;letter-spacing:.02em}
nav button.on{color:#e4e7ec}
.divwrap{display:grid;grid-template-columns:repeat(4,1fr);
 gap:14px 22px;margin:6px 0 26px}
@media(max-width:1000px){.divwrap{
 grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.divwrap{grid-template-columns:1fr}}
.divcol h4{margin:0 0 8px;padding-bottom:8px;font-size:12px;
 letter-spacing:.11em;text-transform:uppercase;color:#8b93a1;
 border-bottom:1px solid #21212a;font-weight:700}
.tmrow{display:flex;align-items:center;gap:12px;padding:9px 8px;
 border-radius:8px;cursor:pointer;transition:background .12s}
.tmrow:hover{background:#101015}
.tmrow.sel{background:#12161d;
 box-shadow:inset 0 0 0 1px #24303d}
.tmrow img{width:30px;height:30px;object-fit:contain}
.tmrow b{font-size:16px;font-weight:700;color:#e4e7ec;
 letter-spacing:-.01em}
.tmrow.sel b{color:#4db8ff}
.dcard{background:#0b0b0e;border:1px solid #1b1b21;
 border-radius:12px;padding:20px 22px;margin-bottom:26px}
.dhead{display:flex;align-items:center;gap:14px;
 padding-bottom:14px;margin-bottom:14px;
 border-bottom:1px solid #1b1b21}
.dhead img{width:44px;height:44px;object-fit:contain}
.dhead h3{margin:0;font-size:20px;color:#fff;
 letter-spacing:-.01em}
.dhead span{color:#767c88;font-size:12.5px;display:block;
 margin-top:3px}
.dgrid{display:grid;grid-template-columns:repeat(4,1fr);
 gap:16px}
@media(max-width:900px){.dgrid{
 grid-template-columns:repeat(2,1fr)}}
.dpos h5{margin:0 0 7px;font-size:10.5px;letter-spacing:.1em;
 text-transform:uppercase;color:#4db8ff;font-weight:800}
.dp{display:flex;align-items:center;gap:8px;padding:4px 0;
 font-size:13px;color:#c3c8d1}
.dp img{width:26px;height:26px;border-radius:50%;
 object-fit:cover;background:#16161b}
.dp i{font-style:normal;color:#5d636e;font-size:11px;
 width:16px;flex:0 0 16px}
.dp em{font-style:normal;color:#ff8b6b;font-size:11px}
.dnote{color:#767c88;font-size:12px;margin:14px 0 0;
 line-height:1.6}
</style>
</head>"""
print("palette + roster css built: %d chars" % len(CSS))

JS = """
var RSEL=null;
var RNICK=__NICK__;
var RDIV=__DIVS__;
var RLOGO=__LOGO__;
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
   h+='<div class="tmrow'+sel+'" onclick="pickTeam(\\''+t+
    '\\')"><img src="'+RLOGO[t]+'" alt="'+RE(t)+'">'+
    '<b>'+RE(RNICK[t])+'</b></div>';
  });
  h+='</div>';
 });
 h+='</div>';
 RQ("rosters").innerHTML=h;
}
"""
JS = JS.replace("__NICK__", json.dumps(NICK, separators=(",", ":")))
JS = JS.replace("__DIVS__", json.dumps(DIVS, separators=(",", ":")))
JS = JS.replace("__LOGO__", json.dumps(LG, separators=(",", ":")))
print("roster js built: %d chars" % len(JS))

H = open("vaporai.html").read()
A2 = "</head>"
A4 = "</script></body></html>"
for a in (A2, A4):
    assert a in H, "MISSING ANCHOR: %r" % a

H = H.replace(A2, CSS, 1)
H = H.replace(A4, "\n" + JS + "\nsafe(drawRosters,'rosters');\n"
              + A4, 1)
open("vaporai.html", "w").write(H)

print("\n=== VERIFY ===")
V = open("vaporai.html").read()
for k, lbl in [("--bg:#050506", "satan-black palette"),
               ("class=\"divwrap\"", "division grid css"),
               ("function drawRosters", "roster override"),
               ("var RDIV=", "division data"),
               ("pickTeam", "team click handler"),
               ("safe(drawRosters,'rosters')", "render call")]:
    print("  %-16s %s" % ("OK" if k in V else "MISSING", lbl))
print("\nSaved vaporai.html  (%.1f MB)" % (len(V) / 1e6))
