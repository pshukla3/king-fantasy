CSS = """
*{box-sizing:border-box}
body{margin:0;padding:0 2px 30px;background:transparent;
color:#EAF2F8;font:14px/1.45 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1060px;margin:0 auto}
.card{background:#0A1E33;border:1px solid #1C4265;
border-radius:16px;padding:16px 18px;margin:0 0 16px}
.card h2{margin:0 0 14px;font-size:22px;letter-spacing:-.5px}
.card h3{margin:0 0 12px;font-size:15px}
.st{display:grid;grid-template-columns:26px 40px 1fr auto;
gap:10px;align-items:center;padding:11px 0;
border-bottom:1px solid #12293F}
.st:last-child{border:0}
.st .rk{font-size:15px;font-weight:700;color:#6F8CA6;
text-align:center}
.st.me .rk{color:#FFC20E}
.st img{width:40px;height:40px;border-radius:50%;
background:#102C47;object-fit:cover}
.st .nm b{font-size:16px;font-weight:700}
.st .nm i{font-style:normal;font-size:12px;color:#6F8CA6;
margin-left:7px}
.st .sub{display:flex;gap:16px;margin-top:3px;
font-size:12px;color:#93AFC6}
.st .sub b{color:#EAF2F8;font-weight:600}
.st .rec{font-size:17px;font-weight:700;text-align:right;
white-space:nowrap}
.st .wv{font-size:11px;color:#6F8CA6;text-align:right;
margin-top:3px;white-space:nowrap}
.rg{display:grid;
grid-template-columns:repeat(auto-fit,minmax(224px,1fr));
gap:10px}
.rc{background:#102C47;border:1px solid #1C4265;
border-radius:12px;padding:12px 13px}
.rc .lb{font-size:10px;text-transform:uppercase;
letter-spacing:.7px;color:#93AFC6;font-weight:700}
.rc .vl{font-size:24px;font-weight:800;letter-spacing:-1px;
margin:5px 0 2px}
.rc .wh{font-size:12px;color:#93AFC6}
.rc.gold .vl{color:#FFC20E}
.rc.blue .vl{color:#4FB3E8}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:#93AFC6;font-size:10px;font-weight:700;
text-transform:uppercase;letter-spacing:.5px;padding:7px;
text-align:right;border-bottom:1px solid #1C4265}
th.l,td.l{text-align:left}
td{padding:7px;text-align:right;
border-bottom:1px solid #12293F;
font-variant-numeric:tabular-nums}
tr:last-child td{border:0}
.luck.up{color:#4ADE80}.luck.dn{color:#F87171}
.mut{color:#93AFC6;font-size:12px}
.note{font-size:11px;color:#6F8CA6;margin-top:10px}
"""

JS = r"""
var T=null,SCH=null,AV={},WV={},BUD=0;

function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function n1(v){return (Math.round(v*100)/100).toFixed(2);}
function n2(v){return (Math.round(v*10)/10).toFixed(1);}

function team(id){
 var o=null;
 (T.teams||[]).forEach(function(t){
  if(Number(t.id)===Number(id))o=t;});
 return o;}
function nameOf(id){
 var t=team(id);
 return t?(t.owner||("Team "+id)):("Team "+id);}

// Every completed game, flattened.
function games(){
 var out=[];
 Object.keys(SCH||{}).forEach(function(w){
  (SCH[w]||[]).forEach(function(g){
   var a=g[0],b=g[1];
   var pa=Number(a.pts||0),pb=Number(b.pts||0);
   if(pa<=0&&pb<=0)return;
   out.push({w:Number(w),a:a.id,b:b.id,pa:pa,pb:pb});
  });});
 out.sort(function(x,y){return x.w-y.w;});
 return out;}

function records(G){
 var mw=null,lw=null,ml=null,lo=null,hi=null;
 G.forEach(function(g){
  [[g.a,g.pa,g.pb],[g.b,g.pb,g.pa]].forEach(function(s){
   var id=s[0],p=s[1],o=s[2];
   var e={id:id,p:p,o:o,w:g.w};
   if(hi===null||p>hi.p)hi=e;
   if(lo===null||p<lo.p)lo=e;
   if(p>o){
    if(mw===null||p>mw.p)mw=e;
    if(lw===null||p<lw.p)lw=e;
   }else if(p<o){
    if(ml===null||p>ml.p)ml=e;
   }
  });});
 return {mw:mw,lw:lw,ml:ml,lo:lo,hi:hi};}

// All-play: how each team would fare against every
// other team every week. Strips schedule luck out.
function allplay(G){
 var byw={};
 G.forEach(function(g){
  var a=byw[g.w]=byw[g.w]||{};
  a[g.a]=g.pa;a[g.b]=g.pb;});
 var ap={};
 Object.keys(byw).forEach(function(w){
  var sc=byw[w],ids=Object.keys(sc);
  ids.forEach(function(i){
   var r=ap[i]=ap[i]||{w:0,l:0,t:0};
   ids.forEach(function(j){
    if(i===j)return;
    if(sc[i]>sc[j])r.w++;
    else if(sc[i]<sc[j])r.l++;
    else r.t++;});});});
 return ap;}

function rcard(lb,e,cls){
 if(!e)return '<div class="rc"><div class="lb">'+lb
  +'</div><div class="vl">\u2013</div>'
  +'<div class="wh">not yet</div></div>';
 return '<div class="rc '+(cls||"")+'">'
  +'<div class="lb">'+lb+'</div>'
  +'<div class="vl">'+n1(e.p)+'</div>'
  +'<div class="wh">'+esc(nameOf(e.id))
  +' &middot; wk '+e.w+'</div></div>';}

function draw(){
 var G=games();
 var teams=(T.teams||[]).slice();
 teams.sort(function(a,b){
  var wa=(a.w||0)-(a.l||0),wb=(b.w||0)-(b.l||0);
  if(wb!==wa)return wb-wa;
  return (b.pf||0)-(a.pf||0);});

 var my=1;
 try{var v=localStorage.getItem("kf_myteam");
  if(v)my=Number(v);}catch(e){}

 var h='<div class="wrap"><div class="card">'
  +'<h2>Standings</h2>';
 teams.forEach(function(t,i){
  var av=AV[t.id]||{};
  var wv=WV[t.id]||{};
  var left=(BUD?(BUD-(wv.used||0)):null);
  h+='<div class="st'+(Number(t.id)===my?" me":"")+'">'
   +'<div class="rk">'+(i+1)+'</div>'
   +(av.img?'<img src="'+esc(av.img)+'">':
     '<div style="width:40px;height:40px;'
     +'border-radius:50%;background:#102C47"></div>')
   +'<div class="nm"><b>'+esc(t.owner||("Team "+t.id))
   +'</b><i>'+esc(av.h||"")+'</i>'
   +'<div class="sub"><span>PF <b>'+n1(t.pf||0)
   +'</b></span><span>PA <b>'+n1(t.pa||0)+'</b></span>'
   +'<span>Diff <b>'+((t.pf-t.pa)>=0?"+":"")
   +n2(t.pf-t.pa)+'</b></span></div></div>'
   +'<div><div class="rec">'+(t.w||0)+'-'+(t.l||0)
   +((t.t)?("-"+t.t):"")+'</div>'
   +'<div class="wv">'+(left!=null?("WAIVER $"+left
     +(wv.pos?(" ("+wv.pos+")"):"")):"")+'</div></div>'
   +'</div>';});
 h+='</div>';

 var R=records(G);
 h+='<div class="card"><h3>League records</h3>'
  +'<div class="rg">'
  +rcard("Most points in a win",R.mw,"gold")
  +rcard("Least points in a win",R.lw,"")
  +rcard("Most points in a loss",R.ml,"blue")
  +rcard("Least points in a week",R.lo,"")
  +rcard("Most points in a week",R.hi,"gold")
  +'</div>'
  +'<p class="note">From '+G.length+' completed game'
  +(G.length===1?"":"s")+'. These fill out as the season '
  +'goes.</p></div>';

 var AP=allplay(G);
 var gp=0;
 Object.keys(AP).forEach(function(i){
  gp=Math.max(gp,AP[i].w+AP[i].l+AP[i].t);});
 var lk=teams.map(function(t){
  var a=AP[t.id]||{w:0,l:0,t:0};
  var tot=a.w+a.l+a.t;
  var pct=tot?a.w/tot:0;
  var gpl=(t.w||0)+(t.l||0)+(t.t||0);
  return {t:t,ap:a,pct:pct,
   exp:pct*gpl,luck:(t.w||0)-pct*gpl};});
 lk.sort(function(x,y){return y.pct-x.pct;});

 h+='<div class="card"><h3>All-play standings</h3>'
  +'<table><thead><tr><th class="l">Team</th>'
  +'<th>Record</th><th>All-play</th><th>Win %</th>'
  +'<th>Expected W</th><th>Luck</th></tr></thead><tbody>';
 lk.forEach(function(r){
  h+='<tr><td class="l">'+esc(r.t.owner||("Team "
   +r.t.id))+'</td>'
   +'<td>'+(r.t.w||0)+'-'+(r.t.l||0)+'</td>'
   +'<td>'+r.ap.w+'-'+r.ap.l+'</td>'
   +'<td>'+Math.round(r.pct*1000)/10+'%</td>'
   +'<td>'+n2(r.exp)+'</td>'
   +'<td class="luck '+(r.luck>=0?"up":"dn")+'">'
   +(r.luck>=0?"+":"")+n2(r.luck)+'</td></tr>';});
 h+='</tbody></table>'
  +'<p class="note">All-play is each team\u2019s record '
  +'if they played every other team every week \u2014 it '
  +'strips out schedule luck. Luck is actual wins minus '
  +'expected wins; positive means the schedule has been '
  +'kind.</p></div>';

 if(G.length){
  h+='<div class="card"><h3>Week by week</h3>'
   +'<table><thead><tr><th>Wk</th><th class="l">Winner'
   +'</th><th>Score</th><th class="l">Loser</th>'
   +'<th>Score</th><th>Margin</th></tr></thead><tbody>';
  G.slice().sort(function(x,y){
   return y.w-x.w||Math.abs(y.pa-y.pb)-Math.abs(x.pa-x.pb);
  }).forEach(function(g){
   var aw=g.pa>=g.pb;
   var wi=aw?g.a:g.b,li=aw?g.b:g.a;
   var wp=aw?g.pa:g.pb,lp=aw?g.pb:g.pa;
   h+='<tr><td>'+g.w+'</td>'
    +'<td class="l">'+esc(nameOf(wi))+'</td>'
    +'<td>'+n1(wp)+'</td>'
    +'<td class="l mut">'+esc(nameOf(li))+'</td>'
    +'<td class="mut">'+n1(lp)+'</td>'
    +'<td>'+n2(wp-lp)+'</td></tr>';});
  h+='</tbody></table></div>';
 }

 h+='</div>';
 $("v").innerHTML=h;
 try{parent.postMessage(
  {kfh:document.body.scrollHeight+24},"*");}catch(e){}
}

function extra(lid){
 if(!lid)return Promise.resolve();
 var B="https://api.sleeper.app/v1/league/"+lid;
 return Promise.all([
  fetch(B+"/users").then(function(r){return r.json();}),
  fetch(B+"/rosters").then(function(r){return r.json();}),
  fetch(B).then(function(r){return r.json();})
 ]).then(function(a){
  var u={};
  (a[0]||[]).forEach(function(x){u[x.user_id]=x;});
  (a[1]||[]).forEach(function(r){
   var x=u[r.owner_id];
   if(x)AV[r.roster_id]={
    h:x.display_name||"",
    img:x.avatar?("https://sleepercdn.com/avatars/thumbs/"
      +x.avatar):null};
   var s=r.settings||{};
   WV[r.roster_id]={used:Number(s.waiver_budget_used||0),
    pos:s.waiver_position};});
  var st=(a[2]||{}).settings||{};
  BUD=Number(st.waiver_budget||0);
 }).catch(function(){});
}

function boot(){
 Promise.all([
  fetch("_slteams.json").then(function(r){return r.json();}),
  fetch("_lgsched.json").then(function(r){return r.json();})
 ]).then(function(a){
  T=a[0];SCH=a[1];
  return extra(T.league);
 }).then(draw).catch(function(e){
  $("v").innerHTML='<p class="mut">Could not load '
   +'standings: '+esc(e.message)+'</p>';});
}
boot();
"""

HTML = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,'
        'initial-scale=1"><style>__CSS__</style></head>'
        '<body><div id="v" class="mut">Loading standings\u2026'
        '</div><script>__JS__</script></body></html>')
HTML = HTML.replace("__CSS__", CSS).replace("__JS__", JS)
open("site/standings.html", "w").write(HTML)
print("wrote site/standings.html (%d KB)" % (len(HTML) // 1024))

H = open("vaporai.html").read()
OLD = ('<section id="lgh_st"><iframe '
       'data-src="league.html?tab=st"')
NEW = '<section id="lgh_st"><iframe data-src="standings.html"'
if OLD in H:
    H = H.replace(OLD, NEW, 1)
    open("vaporai.html", "w").write(H)
    print("lgh_st -> standings.html")
else:
    assert NEW in H, "lgh_st iframe not found"
    print("lgh_st already points at standings.html")
