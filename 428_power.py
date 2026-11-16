import re

CSS = """
*{box-sizing:border-box}
body{margin:0;padding:0 2px 30px;background:transparent;
color:#EAF2F8;font:14px/1.45 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1060px;margin:0 auto}
.card{background:#0A1E33;border:1px solid #1C4265;
border-radius:16px;padding:16px 18px;margin:0 0 16px}
.card h2{margin:0;font-size:21px;letter-spacing:-.5px}
.hd{display:flex;align-items:center;gap:12px;
margin-bottom:14px;flex-wrap:wrap}
.wk{margin-left:auto;background:#102C47;color:#EAF2F8;
border:1px solid #1C4265;border-radius:10px;
padding:7px 12px;font-size:13px;font-weight:600}
.pw{display:grid;grid-template-columns:30px 40px 1fr 92px 64px;
gap:10px;align-items:center;padding:10px 0;
border-bottom:1px solid #12293F}
.pw:last-child{border:0}
.pw.me{background:rgba(255,194,14,.06);border-radius:8px}
.pw .rk{font-size:16px;font-weight:800;text-align:center;
color:#6F8CA6}
.pw.me .rk{color:#FFC20E}
.pw img{width:40px;height:40px;border-radius:50%;
background:#102C47;object-fit:cover}
.pw .nm b{display:block;font-size:15px;font-weight:700}
.pw .nm span{font-size:12px;color:#93AFC6}
.pw .pj{text-align:right;font-size:19px;font-weight:800;
letter-spacing:-.5px;font-variant-numeric:tabular-nums}
.pw .pj em{display:block;font-style:normal;font-size:10px;
color:#6F8CA6;font-weight:600;letter-spacing:.5px;
text-transform:uppercase}
.mv{text-align:right;font-size:12px;font-weight:700}
.mv.up{color:#4ADE80}.mv.dn{color:#F87171}
.mv.fl{color:#5C7A94}
.sb{height:4px;border-radius:99px;background:#12293F;
margin-top:5px;overflow:hidden}
.sb i{display:block;height:100%;background:#0080C6}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:#93AFC6;font-size:10px;font-weight:700;
text-transform:uppercase;letter-spacing:.5px;padding:8px 7px;
text-align:right;border-bottom:1px solid #1C4265}
th.l,td.l{text-align:left}
td{padding:8px 7px;text-align:right;
border-bottom:1px solid #12293F;
font-variant-numeric:tabular-nums}
tr:last-child td{border:0}
tr.me td{background:rgba(255,194,14,.06)}
.od{position:relative;min-width:120px}
.od i{position:absolute;left:0;top:50%;
transform:translateY(-50%);height:16px;border-radius:4px;
background:rgba(0,128,198,.32);z-index:0}
.od span{position:relative;z-index:1;font-weight:700}
.pl{display:flex;align-items:center;gap:8px}
.pl img{width:30px;height:30px;border-radius:50%;
background:#102C47;object-fit:cover;flex:none}
.pl span{font-weight:600}
td .sb{margin-top:4px;width:70px;margin-left:auto}
.mut{color:#93AFC6;font-size:12px}
.note{font-size:11px;color:#6F8CA6;margin-top:12px;
line-height:1.6}
"""

JS = r"""
var T=null,BD=null,LG=null,AV={},SLOTS=[],WK=2,MYID=1;

function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function n1(v){return (Math.round(v*10)/10).toFixed(1);}
function norm(s){return String(s||"").toLowerCase()
 .replace(/[^a-z ]/g,"").replace(/\s+/g," ").trim().replace(/ (jr|sr|iii|ii|iv|v)$/,"");}

var BM={},BDST={};
function bd(p){
 if(p.pos==="DEF"||p.pos==="DST")
  return BDST[p.tm]||BDST[p.pid]||null;
 return BM[p.k||norm(p.n)]||null;}

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
 var W=wkProj(p,wk);
 if(W!=null)return W;
 var b=bd(p);
 var v=(b&&b.live!=null)?b.live:(p.ppg||0);
 if(b&&b.bye&&Number(b.bye)===Number(wk))return 0;
 var inj=String(p.inj||(b?b.inj:"")||"");
 if(/^(Out|IR|Sus|NA|PUP|DNR)/i.test(inj))return 0;
 if(/Doubtful/i.test(inj))v*=0.35;
 if(/Question/i.test(inj))v*=0.88;
 return v;}
function elig(p,s){
 var E={QB:["QB"],RB:["RB"],WR:["WR"],TE:["TE"],K:["K"],
 DEF:["DEF","DST"],DST:["DEF","DST"],
 FLEX:["RB","WR","TE"],WRRB_FLEX:["RB","WR"],
 REC_FLEX:["WR","TE"],SUPER_FLEX:["QB","RB","WR","TE"]};
 var a=E[s];return a?a.indexOf(p.pos)>=0:false;}
function ss(){return (SLOTS||[]).filter(function(s){
 return s!=="BN"&&s!=="IR"&&s!=="TAXI";});}

// Best legal lineup for that week -- power ranking should
// reflect roster ceiling, not a stale saved lineup.
function best(t,wk){
 var S=ss(),pool=(t.players||[]).slice();
 pool.sort(function(a,b){return proj(b,wk)-proj(a,wk);});
 var used={},tot=0,fx=[];
 S.forEach(function(s,i){
  if(s.indexOf("FLEX")>=0){fx.push(s);return;}
  for(var j=0;j<pool.length;j++){
   if(used[pool[j].pid])continue;
   if(elig(pool[j],s)){used[pool[j].pid]=1;
    tot+=proj(pool[j],wk);break;}}});
 fx.forEach(function(s){
  for(var j=0;j<pool.length;j++){
   if(used[pool[j].pid])continue;
   if(elig(pool[j],s)){used[pool[j].pid]=1;
    tot+=proj(pool[j],wk);break;}}});
 return tot;}

function rankAt(wk){
 var a=(T.teams||[]).map(function(t){
  return {t:t,v:best(t,wk)};});
 a.sort(function(x,y){return y.v-x.v;});
 var m={};
 a.forEach(function(r,i){m[r.t.id]=i+1;});
 return {list:a,map:m};}

function draw(){
 var cur=rankAt(WK);
 var prev=(WK>1)?rankAt(WK-1).map:null;
 var top=cur.list.length?cur.list[0].v:1;
 var odd={};
 ((LG&&LG.rows)||[]).forEach(function(r){odd[r.id]=r;});

 var h='<div class="wrap"><div class="card">'
  +'<div class="hd"><h2>Power Rankings &amp; Playoff Odds'
  +'</h2><select class="wk" id="wksel">';
 for(var w=1;w<=18;w++)h+='<option value="'+w+'"'
  +(w===WK?' selected':'')+'>Week '+w+'</option>';
 h+='</select></div>';

 h+='<table><thead><tr>'
  +'<th>#</th><th class="l">Team</th><th>Rec</th>'
  +'<th>PF</th><th>Wk '+WK+' proj</th><th>Move</th>'
  +'<th>Proj W</th><th>Seed</th>'
  +'<th class="l">Playoff odds</th></tr></thead><tbody>';

 cur.list.forEach(function(r,i){
  var t=r.t,av=AV[t.id]||{},o=odd[t.id]||{};
  var mv=prev?(prev[t.id]-(i+1)):0;
  var mc=mv>0?"up":(mv<0?"dn":"fl");
  var mt=mv>0?("\u25b2"+mv):(mv<0?("\u25bc"+(-mv)):"\u2013");
  h+='<tr'+(Number(t.id)===MYID?' class="me"':'')+'>'
   +'<td><b>'+(i+1)+'</b></td>'
   +'<td class="l"><div class="pl">'
   +(av.img?'<img src="'+esc(av.img)+'">':
     '<div style="width:30px"></div>')
   +'<span>'+esc(t.owner||("Team "+t.id))+'</span>'
   +'</div></td>'
   +'<td>'+(t.w||0)+'-'+(t.l||0)+'</td>'
   +'<td>'+n1(t.pf||0)+'</td>'
   +'<td><b>'+n1(r.v)+'</b>'
   +'<div class="sb"><i style="width:'
   +(top?Math.round(100*r.v/top):0)+'%"></i></div></td>'
   +'<td class="mv '+mc+'">'+mt+'</td>'
   +'<td>'+(o.projw!=null?n1(o.projw):"\u2013")+'</td>'
   +'<td>'+(o.seed!=null?n1(o.seed):"\u2013")+'</td>'
   +'<td class="l od">'
   +(o.playoff!=null?('<i style="width:'
     +Math.round(o.playoff)+'%"></i><span>'
     +n1(o.playoff)+'%</span>'):'<span>\u2013</span>')
   +'</td></tr>';});
 h+='</tbody></table>';

 h+='<p class="note"><b>Wk '+WK+' proj</b> is each '
  +'team\u2019s best legal lineup that week under our '
  +'weekly player model, with byes and Out players at '
  +'zero \u2014 so the order shifts week to week as byes '
  +'land. Move compares to week '
  +(WK>1?(WK-1):"\u2013")+'.</p>';
 if(LG&&LG.rows){
  h+='<p class="note"><b>Proj W, Seed and Playoff odds</b> '
   +'come from '+(LG.sims||0).toLocaleString()+' simulated '
   +'seasons off the current rosters, through week '
   +(LG.week||0)+'. Weekly scores are drawn around roster '
   +'strength with a '+n1(LG.sd||0)+'-point spread derived '
   +'from measured player variance, roster strength is '
   +'recomputed per week so byes are priced in, and each '
   +'simulated season draws its own strength error rather '
   +'than assuming every team is rated correctly.</p>'
   +'<p class="note">One game is about 6% of a season, so '
   +'results have barely moved these yet \u2014 roster '
   +'quality still dominates.</p>';
 }
 h+='</div></div>';
 $("v").innerHTML=h;
 var w=$("wksel");
 if(w)w.onchange=function(){WK=Number(w.value);draw();};
 try{parent.postMessage(
  {kfh:document.body.scrollHeight+24},"*");}catch(e){}
}

function avatars(lid){
 if(!lid)return Promise.resolve();
 var B="https://api.sleeper.app/v1/league/"+lid;
 return Promise.all([
  fetch(B+"/users").then(function(r){return r.json();}),
  fetch(B+"/rosters").then(function(r){return r.json();})
 ]).then(function(a){
  var u={};
  (a[0]||[]).forEach(function(x){u[x.user_id]=x;});
  (a[1]||[]).forEach(function(r){
   var x=u[r.owner_id];
   if(x)AV[r.roster_id]={
    img:x.avatar?("https://sleepercdn.com/avatars/thumbs/"
     +x.avatar):null};});
 }).catch(function(){});
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
  T=a[0];BD=a[1];PW=a[2];LG=a[3];
  SLOTS=T.slots||[];
  (BD.rows||[]).forEach(function(r){
   var p=String(r.pos||"");
   if(p==="DEF"||p==="DST")BDST[String(r.tm||"")]=r;
   else BM[norm(r.n)]=r;});
  if(LG&&LG.week)WK=Math.min(18,Number(LG.week)+1);
  return avatars(T.league);
 }).then(draw).catch(function(e){
  $("v").innerHTML='<p class="mut">Could not load: '
   +esc(e.message)+'</p>';});
}
boot();
"""

HTML = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,'
        'initial-scale=1"><style>__CSS__</style></head>'
        '<body><div id="v" class="mut">Loading\u2026</div>'
        '<script>__JS__</script></body></html>')
HTML = HTML.replace("__CSS__", CSS).replace("__JS__", JS)
open("site/power.html", "w").write(HTML)
print("wrote site/power.html (%d KB)" % (len(HTML) // 1024))

STY = ('width:100%;height:2200px;border:0;'
       'background:transparent')
SEC = ('<section id="lgodds"><iframe data-src="power.html" '
       'style="%s"></iframe></section>' % STY)

H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<section id="lgodds">.*?</section>', SEC, H,
           count=1, flags=re.S)
assert H.count('<section id="lgodds">') == 1
assert 'data-src="power.html"' in H, "iframe not placed"

# retire the old two-panel renderer
H = H.replace('<script src="_lgpages.js"></script>', "")

assert H.count("</script></body></html>") == 1, "tail anchor"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav %d" % nav
open("vaporai.html", "w").write(H)
print("lgodds -> power.html | _lgpages.js retired | nav %d"
      % nav)

# --- rail: one entry instead of two -------------------
OLD = ('[["Playoff Odds", "lgodds"],\n'
       '          ["Power Rankings", "lgpower"],\n'
       '          ["Sync League", "lgsync"]]')
NEWI = ('[["Power & Odds", "lgodds"],\n'
        '          ["Sync League", "lgsync"]]')
P = open("416_hubtabs.py").read()
if '"Power Rankings"' in P:
    a = 'items += [["Playoff Odds", "lgodds"],'
    assert P.count(a) == 1, "416 items anchor"
    P = re.sub(r'items \+= \[\[.*?\]\]\n', 
               'items += [["Power & Odds", "lgodds"],\n'
               '          ["Sync League", "lgsync"]]\n',
               P, count=1, flags=re.S)
    open("416_hubtabs.py", "w").write(P)
    print("416_hubtabs: rail items collapsed to Power & Odds")
else:
    print("416_hubtabs: already collapsed")

N = open("289_nav2.py").read()
if '"lgpower"' in N:
    N = N.replace('["Playoff Odds", "lgodds"], '
                  '["Power Rankings", "lgpower"], ',
                  '["Power & Odds", "lgodds"], ')
    N = N.replace('["Playoff Odds", "lgodds"],'
                  '["Power Rankings", "lgpower"],',
                  '["Power & Odds", "lgodds"],')
    N = re.sub(r'\["Playoff Odds",\s*"lgodds"\]',
               '["Power & Odds", "lgodds"]', N)
    N = re.sub(r',?\s*\["Power Rankings",\s*"lgpower"\]',
               '', N)
    open("289_nav2.py", "w").write(N)
    print("289_nav2: lgpower removed from the rail")
else:
    print("289_nav2: already updated")
