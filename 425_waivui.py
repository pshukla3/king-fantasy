CSS = """
*{box-sizing:border-box}
body{margin:0;padding:0 2px 30px;background:transparent;
color:#EAF2F8;font:14px/1.45 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto}
h4{margin:18px 0 8px;font-size:12px;text-transform:uppercase;
letter-spacing:.8px;color:#93AFC6;font-weight:700}
h4 i{float:right;font-style:normal;text-transform:none;
letter-spacing:0;font-size:11px;color:#6F8CA6}
.tr{display:grid;
grid-template-columns:repeat(auto-fill,minmax(186px,1fr));
gap:8px}
.tc{background:#0A1E33;border:1px solid #1C4265;
border-radius:12px;padding:10px 11px;cursor:pointer;
position:relative}
.tc:hover{border-color:#0080C6}
.tc .hd{display:flex;gap:9px;align-items:center}
.tc img{width:40px;height:40px;border-radius:50%;
background:#102C47;object-fit:cover;flex:none}
.tc b{display:block;font-size:13px;white-space:nowrap;
overflow:hidden;text-overflow:ellipsis}
.tc .sm{font-size:11px;color:#93AFC6}
.tc .mt{display:flex;justify-content:space-between;
margin-top:8px;font-size:11px;color:#93AFC6}
.tc .mt b{font-size:13px;color:#EAF2F8;display:inline}
.tag{position:absolute;top:8px;right:9px;font-size:9px;
padding:2px 6px;border-radius:99px;font-weight:700;
letter-spacing:.4px}
.tag.free{background:#FFC20E;color:#04121F}
.tag.own{background:#1C4265;color:#93AFC6}
.fit{font-weight:700}
.fit.up{color:#4ADE80}.fit.dn{color:#6F8CA6}
.bar{display:flex;gap:8px;align-items:center;
flex-wrap:wrap;margin:14px 0 10px}
.pills{display:flex;gap:3px;background:#0A1E33;
border:1px solid #1C4265;border-radius:99px;padding:3px}
.pills button{background:none;border:0;color:#93AFC6;
padding:6px 13px;border-radius:99px;font-size:12px;
font-weight:700;cursor:pointer}
.pills button.on{background:#0080C6;color:#fff}
input.s{flex:1;min-width:170px;padding:8px 12px;
border-radius:99px;border:1px solid #1C4265;
background:#0A1E33;color:#EAF2F8;font-size:13px}
label.ck{display:flex;align-items:center;gap:6px;
font-size:12px;color:#93AFC6;cursor:pointer}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:#93AFC6;font-size:10px;font-weight:700;
text-transform:uppercase;letter-spacing:.5px;
padding:8px 7px;text-align:right;cursor:pointer;
white-space:nowrap;border-bottom:1px solid #1C4265;
position:sticky;top:0;background:#04121F}
th:hover{color:#EAF2F8}
th.l,td.l{text-align:left}
th.on{color:#FFC20E}
td{padding:7px;text-align:right;
border-bottom:1px solid #12293F;
font-variant-numeric:tabular-nums}
tr:hover td{background:#0A1E33}
.pl{display:flex;align-items:center;gap:9px;cursor:pointer}
.pl img{width:32px;height:32px;border-radius:50%;
background:#102C47;object-fit:cover;flex:none}
.pl b{display:block;font-size:13px}
.pl b:hover{color:#FFC20E}
.pl span{font-size:11px;color:#93AFC6}
.gp{background:#0A1E33;color:#93AFC6;font-size:10px;
padding:4px 7px;text-transform:uppercase;letter-spacing:.5px;
text-align:center;font-weight:700}
.mut{color:#93AFC6;font-size:12px}
.more{display:block;margin:14px auto;padding:8px 20px;
border-radius:8px;border:1px solid #1C4265;
background:#0A1E33;color:#EAF2F8;cursor:pointer;
font-size:12px;font-weight:600}
.pillx{display:inline-block;font-size:9px;padding:1px 6px;
border-radius:99px;background:#1C4265;color:#93AFC6;
margin-left:5px}
.pillx.out{background:#3A1F1F;color:#F87171}
"""

JS = r"""
var W=null,SL=null,MYID=1,POS="ALL",Q="",MODE="proj";
var FA=true,SORT="proj",DIR=-1,LIM=60,WORST={};

function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function n1(v){return (v==null||v!==v)?"\u2013":
 (Math.round(v*10)/10).toFixed(1);}
function n0(v){return (v==null||v!==v||v===0)?"\u2013":
 String(Math.round(v));}
function norm(s){return String(s||"").toLowerCase()
 .replace(/[^a-z ]/g,"").replace(/\s+/g," ").trim().replace(/ (jr|sr|iii|ii|iv|v)$/,"");}

// Worst current starter at each position = the bar a
// waiver add has to clear to actually help you.
function worst(){
 var me=null;
 (SL.teams||[]).forEach(function(t){
  if(Number(t.id)===Number(MYID))me=t;});
 if(!me)return {};
 var slots=(SL.slots||[]).filter(function(s){
  return s!=="BN"&&s!=="IR";});
 var by={};
 (me.players||[]).forEach(function(p){by[p.pid]=p;});
 var pj={};
 (W.players||[]).forEach(function(p){
  pj[norm(p.n)]=p.proj;});
 var out={};
 (me.starters||[]).forEach(function(pid,i){
  var p=by[pid];
  if(!p)return;
  var v=pj[norm(p.n)];
  if(v==null)v=p.ppg||0;
  var ps=p.pos;
  if(out[ps]==null||v<out[ps])out[ps]=v;
 });
 return out;
}
function fit(p){
 var w=WORST[p.pos];
 if(w==null||p.proj==null)return null;
 return p.proj-w;
}

var COLS={
 proj:[["n","Player","l"],["pos","Pos",""],
  ["tm","Tm",""],["proj","Proj",""],["floor","Floor",""],
  ["ceil","Ceil",""],["fit","Fit",""],["rk","Rk",""],
  ["posrk","PosRk",""],["tier","Tier",""],
  ["bye","Bye",""],["savg","Sn/G",""]],
 stats:[["n","Player","l"],["pos","Pos",""],
  ["tm","Tm",""],["g","G",""],["ratt","Att",""],
  ["ryd","RuYd",""],["rtd","RuTD",""],["tar","Tar",""],
  ["rec","Rec",""],["cyd","ReYd",""],["ctd","ReTD",""],
  ["cmp","Cmp",""],["patt","PAtt",""],["pyd","PaYd",""],
  ["ptd","PaTD",""],["int","Int",""]]
};

function val(p,k){
 if(k==="fit")return fit(p);
 if(["g","ratt","ryd","rtd","tar","rec","cyd","ctd",
     "cmp","patt","pyd","ptd","int"].indexOf(k)>=0)
  return (p.st||{})[k];
 return p[k];
}

function rows(){
 var a=(W.players||[]).filter(function(p){
  if(FA&&p.owner)return false;
  if(POS!=="ALL"){
   if(POS==="DEF"){if(p.pos!=="DEF"&&p.pos!=="DST")
    return false;}
   else if(p.pos!==POS)return false;}
  if(Q&&norm(p.n).indexOf(Q)<0)return false;
  return true;});
 a.sort(function(x,y){
  var u=val(x,SORT),v=val(y,SORT);
  if(typeof u==="string"||typeof v==="string")
   return String(u||"").localeCompare(String(v||""))*DIR;
  u=(u==null||u!==u)?-1e9:u;
  v=(v==null||v!==v)?-1e9:v;
  return (u-v)*DIR;});
 return a;
}

function trend(){
 var a=(W.trend||[]).slice();
 a.forEach(function(x){x._f=fit(x);});
 a.sort(function(x,y){
  var fx=(x.owner?-1:1),fy=(y.owner?-1:1);
  if(fx!==fy)return fy-fx;
  var a1=(x._f==null?-99:x._f),b1=(y._f==null?-99:y._f);
  if(Math.abs(a1-b1)>0.4)return b1-a1;
  return y.adds-x.adds;});
 var h='<div class="tr">';
 a.slice(0,12).forEach(function(x){
  var f=x._f;
  h+='<div class="tc" data-kfp="'+esc(x.n)+'">'
   +'<span class="tag '+(x.owner?"own":"free")+'">'
   +(x.owner?"ROSTERED":"FREE")+'</span>'
   +'<div class="hd">'
   +(x.img?'<img src="'+esc(x.img)+'">':
     '<div style="width:40px"></div>')
   +'<div style="min-width:0"><b>'+esc(x.n)+'</b>'
   +'<span class="sm">'+esc(x.pos)+' &middot; '
   +esc(x.tm||"")+(x.posrk?(' &middot; '+x.pos+x.posrk)
   :'')+'</span></div></div>'
   +'<div class="mt"><span>adds <b>'
   +(x.adds>=1000?(Math.round(x.adds/1000)+"k"):x.adds)
   +'</b></span>'
   +'<span>proj <b>'+n1(x.proj)+'</b></span>'
   +'<span class="fit '+(f!=null&&f>0?"up":"dn")+'">'
   +(f==null?"":((f>0?"+":"")+n1(f)))+'</span></div>'
   +'</div>';
 });
 return h+'</div>';
}

function draw(){
 WORST=worst();
 var cols=COLS[MODE],a=rows();
 var h='<div class="wrap">';

 h+='<h4>Trending pickups<i>Sleeper adds, last 24h '
  +'&middot; ranked by fit to your roster</i></h4>'
  +trend();

 h+='<h4>All players<i>'+a.length+' shown</i></h4>';
 h+='<div class="bar"><div class="pills">';
 ["ALL","QB","RB","WR","TE","K","DEF"].forEach(function(p){
  h+='<button data-p="'+p+'"'+(POS===p?' class="on"':'')
   +'>'+p+'</button>';});
 h+='</div><div class="pills">'
  +'<button data-m="proj"'+(MODE==="proj"?' class="on"':'')
  +'>Projection</button>'
  +'<button data-m="stats"'+(MODE==="stats"?' class="on"':'')
  +'>Stats</button></div>'
  +'<input class="s" id="q" placeholder="Find player" '
  +'value="'+esc(Q)+'">'
  +'<label class="ck"><input type="checkbox" id="fa"'
  +(FA?' checked':'')+'> Free agents only</label></div>';

 h+='<table><thead><tr>';
 cols.forEach(function(c){
  h+='<th class="'+(c[2]||"")+(SORT===c[0]?" on":"")
   +'" data-s="'+c[0]+'">'+c[1]
   +(SORT===c[0]?(DIR<0?" \u25be":" \u25b4"):"")+'</th>';});
 h+='</tr></thead><tbody>';

 if(!a.length)h+='<tr><td colspan="'+cols.length
  +'" class="l mut">No players match.</td></tr>';

 a.slice(0,LIM).forEach(function(p){
  h+='<tr>';
  cols.forEach(function(c){
   var k=c[0];
   if(k==="n"){
    var tg="";
    if(p.inj&&!/Active/i.test(p.inj))
     tg='<span class="pillx out">'
      +esc(String(p.inj).slice(0,4).toUpperCase())
      +'</span>';
    h+='<td class="l"><div class="pl" data-kfp="'
     +esc(p.n)+'">'
     +(p.img?'<img src="'+esc(p.img)+'">':
       '<div style="width:32px"></div>')
     +'<div><b>'+esc(p.n)+tg+'</b><span>'
     +(p.owner?esc(p.owner):"free agent")
     +'</span></div></div></td>';
   }else if(k==="pos"||k==="tm"){
    h+='<td>'+esc(p[k]||"")+'</td>';
   }else if(k==="fit"){
    var f=fit(p);
    h+='<td class="fit '+(f!=null&&f>0?"up":"dn")+'">'
     +(f==null?"\u2013":((f>0?"+":"")+n1(f)))+'</td>';
   }else if(k==="rk"||k==="posrk"||k==="tier"
     ||k==="bye"){
    h+='<td>'+(p[k]||"\u2013")+'</td>';
   }else if(MODE==="stats"){
    h+='<td>'+n0(val(p,k))+'</td>';
   }else{
    h+='<td>'+n1(val(p,k))+'</td>';
   }
  });
  h+='</tr>';
 });
 h+='</tbody></table>';
 if(a.length>LIM)
  h+='<button class="more" id="more">Show '
   +Math.min(60,a.length-LIM)+' more ('+(a.length-LIM)
   +' left)</button>';
 h+='<p class="mut" style="margin-top:12px">Fit = a '
  +'player\u2019s projection minus your weakest current '
  +'starter at that position. Positive means he would '
  +'upgrade your lineup this week. Trending counts are '
  +'Sleeper-wide, not your league.</p>';
 h+='<p class="mut">Updated '+esc(W.gen||"")+'</p></div>';

 $("v").innerHTML=h;
 wire();
 try{parent.postMessage(
  {kfh:document.body.scrollHeight+24},"*");}catch(e){}
}

function wire(){
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-p]"),function(e){
  e.onclick=function(){POS=e.getAttribute("data-p");
   LIM=60;draw();};});
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-m]"),function(e){
  e.onclick=function(){MODE=e.getAttribute("data-m");
   SORT=(MODE==="stats")?"ryd":"proj";DIR=-1;draw();};});
 Array.prototype.forEach.call(
  document.querySelectorAll("[data-s]"),function(e){
  e.onclick=function(){
   var k=e.getAttribute("data-s");
   if(SORT===k)DIR=-DIR;else{SORT=k;DIR=-1;}
   draw();};});
 var q=$("q");
 if(q)q.oninput=function(){
  Q=norm(q.value);LIM=60;draw();
  var n=$("q");if(n){n.focus();
   n.setSelectionRange(n.value.length,n.value.length);}};
 var f=$("fa");
 if(f)f.onchange=function(){FA=f.checked;LIM=60;draw();};
 var m=$("more");
 if(m)m.onclick=function(){LIM+=60;draw();};
}

function boot(){
 try{var v=localStorage.getItem("kf_myteam");
  if(v)MYID=Number(v);}catch(e){}
 Promise.all([
  fetch("_waiv.json").then(function(r){return r.json();}),
  fetch("_slteams.json").then(function(r){return r.json();})
 ]).then(function(a){
  W=a[0];SL=a[1];draw();
 }).catch(function(e){
  $("v").innerHTML='<p class="mut">Could not load '
   +'waivers: '+esc(e.message)+'</p>';});
}
boot();
"""

HTML = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,'
        'initial-scale=1"><style>__CSS__</style></head>'
        '<body><div id="v" class="mut">Loading waivers\u2026'
        '</div><script src="_card.js"></script>'
        '<script>__JS__</script></body></html>')
HTML = HTML.replace("__CSS__", CSS).replace("__JS__", JS)
open("site/waivers.html", "w").write(HTML)
print("wrote site/waivers.html (%d KB)" % (len(HTML) // 1024))

H = open("vaporai.html").read()
OLD = ('<section id="lgh_wv"><iframe '
       'data-src="league.html?tab=wv"')
NEW = '<section id="lgh_wv"><iframe data-src="waivers.html"'
if OLD in H:
    H = H.replace(OLD, NEW, 1)
    open("vaporai.html", "w").write(H)
    print("lgh_wv -> waivers.html")
else:
    assert NEW in H, "lgh_wv iframe not found"
    print("lgh_wv already points at waivers.html")
