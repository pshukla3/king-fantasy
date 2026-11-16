CSS = """
*{box-sizing:border-box}
body{margin:0;padding:0 2px 30px;background:transparent;
color:#EAF2F8;font:14px/1.45 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1060px;margin:0 auto}
.hd{display:flex;gap:10px;align-items:stretch;margin:6px 0 4px}
.tc{flex:1;background:#0A1E33;border:1px solid #1C4265;
border-radius:14px;padding:14px 16px;min-width:0;
position:relative}
.tc.me{border-color:#FFC20E}
.tc.win{border-color:#0080C6}
.tc h3{margin:0 0 2px;font-size:15px;white-space:nowrap;
overflow:hidden;text-overflow:ellipsis}
.tc .rec{color:#93AFC6;font-size:12px}
.tc .pr{font-size:30px;font-weight:800;letter-spacing:-1px;
margin:6px 0 0}
.tc .lv{font-size:12px;color:#93AFC6}
.vs{align-self:center;color:#5C7A94;font-weight:800;
font-size:13px;padding:0 2px}
.fin{position:absolute;top:-9px;left:50%;
transform:translateX(-50%);font-size:9px;font-weight:800;
letter-spacing:.6px;background:#FFC20E;color:#04121F;
padding:2px 9px;border-radius:99px}
.wpbar{height:8px;border-radius:99px;background:#12293F;
overflow:hidden;display:flex;margin:10px 0 4px}
.wpbar i{display:block;height:100%}
.wpl{display:flex;justify-content:space-between;
font-size:12px;color:#93AFC6;margin-bottom:16px}
.wpl b{color:#EAF2F8}
h4{margin:20px 0 8px;font-size:13px;text-transform:uppercase;
letter-spacing:.8px;color:#93AFC6;font-weight:700}
h4 i{float:right;font-style:normal;text-transform:none;
letter-spacing:0;font-size:11px;color:#6F8CA6}
.row{display:grid;grid-template-columns:1fr 62px 1fr;
align-items:center;gap:8px;padding:7px 0;
border-bottom:1px solid #12293F}
.side{display:flex;align-items:center;gap:9px;min-width:0}
.side.r{flex-direction:row-reverse;text-align:right}
.side img{width:34px;height:34px;border-radius:50%;
background:#102C47;object-fit:cover;flex:none}
.nm{min-width:0;flex:1}
.nm b{display:block;font-size:13px;white-space:nowrap;
overflow:hidden;text-overflow:ellipsis;cursor:pointer}
.nm b:hover{color:#FFC20E}
.nm span{font-size:11px;color:#93AFC6}
.pts{font-size:15px;font-weight:700;flex:none;min-width:52px;
text-align:right;font-variant-numeric:tabular-nums}
.side.r .pts{text-align:left}
.pts em{display:block;font-style:normal;font-size:10px;
color:#6F8CA6;font-weight:600}
.slot{text-align:center;font-size:10px;font-weight:800;
letter-spacing:.5px;color:#93AFC6;background:#102C47;
border-radius:99px;padding:4px 0}
.win{color:#4ADE80}.lose{color:#6F8CA6}
.card{background:#0A1E33;border:1px solid #1C4265;
border-radius:14px;padding:14px 16px;margin:12px 0}
.card h5{margin:0 0 8px;font-size:13px}
.gain{color:#4ADE80;font-weight:700}
.mut{color:#93AFC6;font-size:12px}
.note{font-size:11px;color:#6F8CA6;margin-top:8px;
padding-top:8px;border-top:1px solid #12293F;line-height:1.6}
.wk{float:right;background:#102C47;color:#EAF2F8;
border:1px solid #1C4265;border-radius:8px;padding:5px 9px;
font-size:12px}
table.an{width:100%;border-collapse:collapse;font-size:12px}
table.an td,table.an th{padding:5px 7px;text-align:left;
border-bottom:1px solid #12293F}
table.an th{color:#93AFC6;font-size:11px;font-weight:600;
text-transform:uppercase;letter-spacing:.4px}
td.num{text-align:right;font-variant-numeric:tabular-nums}
"""

JS = r"""
var T=null,BD=null,LGJ=null,PM=null,PROJ=null;
var MU=null,SLOTS=[],WK=2,MYID=1,SD=22.5,LID=null;

function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function n1(v){return (v==null||v!==v)?"\u2013":
 (Math.round(v*100)/100).toFixed(2);}
function norm(s){return String(s||"").toLowerCase()
 .replace(/[^a-z ]/g,"").replace(/\s+/g," ").trim().replace(/ (jr|sr|iii|ii|iv|v)$/,"");}
function cdf(z){
 var t=1/(1+0.2316419*Math.abs(z));
 var d=0.3989423*Math.exp(-z*z/2);
 var p=d*t*(0.3193815+t*(-0.3565638+t*(1.781478
   +t*(-1.821256+t*1.330274))));
 return z>0?1-p:p;}

var BM={},BDST={};
function info(pid){
 var m=(PM&&PM[pid])||{};
 return {pid:pid,n:m.n||pid,pos:m.p||"",tm:m.t||""};}
function bd(p){
 if(p.pos==="DEF"||p.pos==="DST")
  return BDST[p.tm]||BDST[p.pid]||null;
 return BM[norm(p.n)]||null;}
function img(p){var b=bd(p);return (b&&b.img)?b.img:"";}

// our projection for that player, that week
function projOf(p,wk){
 var m=PROJ&&PROJ[String(wk)];
 if(m){
  var k=(p.pos==="DEF"||p.pos==="DST")?p.tm:norm(p.n);
  if(m[k]!=null)return m[k];
 }
 var b=bd(p);
 return (b&&b.live!=null)?b.live:null;}

function slots(){
 return (SLOTS||[]).filter(function(s){
  return s!=="BN"&&s!=="IR"&&s!=="TAXI";});}

function mrow(rid){
 var o=null;
 (MU||[]).forEach(function(r){
  if(Number(r.roster_id)===Number(rid))o=r;});
 return o;}
function oppRow(me){
 if(!me)return null;
 var o=null;
 (MU||[]).forEach(function(r){
  if(r.matchup_id===me.matchup_id
   && Number(r.roster_id)!==Number(me.roster_id))o=r;});
 return o;}
function teamMeta(rid){
 var o=null;
 (T.teams||[]).forEach(function(t){
  if(Number(t.id)===Number(rid))o=t;});
 return o;}

// a week is live/final once anyone has scored
function started(){
 var s=false;
 (MU||[]).forEach(function(r){
  if(Number(r.points||0)>0)s=true;});
 return s;}

function lineup(r){
 var out=[];
 if(!r)return out;
 var st=r.starters||[],sp=r.starters_points||[];
 st.forEach(function(pid,i){
  if(!pid||pid==="0"){out.push(null);return;}
  var p=info(pid);
  p.act=(sp[i]==null?null:Number(sp[i]));
  out.push(p);});
 return out;}

function value(p,live){
 if(!p)return 0;
 if(live&&p.act!=null)return p.act;
 var v=projOf(p,WK);
 return (v==null)?0:v;}

function cell(p,side,live){
 if(!p)return '<div class="side '+side+'">'
  +'<div class="nm mut">empty</div>'
  +'<div class="pts">0.00</div></div>';
 var v=value(p,live);
 var pj=projOf(p,WK);
 var sub=esc(p.pos)+' \u00b7 '+esc(p.tm||"FA");
 var tail=(live&&p.act!=null&&pj!=null)
  ?('<em>proj '+n1(pj)+'</em>'):'';
 return '<div class="side '+side+'">'
  +(img(p)?'<img src="'+esc(img(p))+'">':
    '<div style="width:34px"></div>')
  +'<div class="nm"><b data-kfp="'+esc(p.n)+'">'
  +esc(p.n)+'</b><span>'+sub+'</span></div>'
  +'<div class="pts">'+n1(v)+tail+'</div></div>';}

function draw(){
 var me=mrow(MYID),him=oppRow(me);
 if(!me){$("v").innerHTML='<p class="mut">No matchup '
  +'for roster '+MYID+' in week '+WK+'.</p>';return;}
 var live=started();
 var meta=teamMeta(MYID),hmeta=him?
  teamMeta(him.roster_id):null;
 var lu=lineup(me),hl=lineup(him);

 var my=live?Number(me.points||0):0;
 var his=live?Number(him?him.points:0):0;
 if(!live){
  lu.forEach(function(p){my+=value(p,false);});
  hl.forEach(function(p){his+=value(p,false);});
 }

 var done=KFwk.isFinal(WK);
 var wp,wpA;
 if(done){wpA=my>his?100:(my<his?0:50);}
 else{wpA=Math.round(cdf((my-his)/(SD*Math.SQRT2))*1000)/10;}

 var h='<div class="wrap">';
 h+='<select class="wk" id="wksel">';
 for(var w=1;w<=18;w++)h+='<option value="'+w+'"'
  +(w===WK?' selected':'')+'>Week '+w+'</option>';
 h+='</select>';

 h+='<div class="hd" style="position:relative">'
  +(done?'<span class="fin">FINAL</span>':'')
  +'<div class="tc me'+(done&&my>his?' win':'')+'">'
  +'<h3>'+esc(meta?(meta.owner||("Team "+MYID)):"You")
  +'</h3><div class="rec">'
  +(meta?(meta.w+'-'+meta.l+' \u00b7 '+n1(meta.pf)+' PF')
    :'')+'</div>'
  +'<div class="pr">'+n1(my)+'</div>'
  +'<div class="lv">'+(done?'final':(live?'live':
    'projected'))+'</div></div>'
  +'<div class="vs">VS</div>'
  +'<div class="tc'+(done&&his>my?' win':'')+'">'
  +'<h3>'+esc(hmeta?(hmeta.owner||"Opponent"):"Bye")
  +'</h3><div class="rec">'
  +(hmeta?(hmeta.w+'-'+hmeta.l+' \u00b7 '+n1(hmeta.pf)
    +' PF'):'no opponent')+'</div>'
  +'<div class="pr">'+n1(his)+'</div>'
  +'<div class="lv">'+(done?'final':(live?'live':
    'projected'))+'</div></div></div>';

 h+='<div class="wpbar">'
  +'<i style="width:'+wpA+'%;background:#FFC20E"></i>'
  +'<i style="width:'+(100-wpA)+'%;background:#1C4265">'
  +'</i></div><div class="wpl"><span><b>'+wpA
  +'%</b> '+(done?'result':'win probability')+'</span>'
  +'<span>'+(done?'final margin':'projected margin')
  +' <b>'+(my-his>=0?'+':'')+n1(my-his)+'</b></span></div>';

 var ss=slots();
 h+='<h4>Starters<i>'+(done?
   'lineups as actually played':'current lineups')
  +'</i></h4>';
 var n=Math.max(lu.length,hl.length,ss.length);
 for(var i=0;i<n;i++){
  h+='<div class="row">'+cell(lu[i],"",live)
   +'<div class="slot">'+esc(ss[i]||"")+'</div>'
   +cell(hl[i],"r",live)+'</div>';
 }

 // retrospective optimiser for finished weeks
 if(done&&me.players_points){
  var pp=me.players_points,best=[];
  Object.keys(pp).forEach(function(pid){
   var p=info(pid);p.act=Number(pp[pid]);best.push(p);});
  var got=0;
  lu.forEach(function(p){if(p&&p.act!=null)got+=p.act;});
  var opt=bestLineup(best,ss);
  var ot=0;opt.forEach(function(p){if(p)ot+=p.act;});
  h+='<div class="card"><h5>Points left on your bench'
   +'</h5>';
  if(ot-got<0.05){
   h+='<p class="mut">You started the optimal lineup '
    +'this week. Nothing left behind.</p>';
  }else{
   h+='<p class="mut">Your best legal lineup would have '
    +'scored <b>'+n1(ot)+'</b> \u2014 <span class="gain">+'
    +n1(ot-got)+'</span> over the '+n1(got)
    +' you started.</p>';
   var inLU={};
   lu.forEach(function(p){if(p)inLU[p.pid]=1;});
   opt.forEach(function(p,i){
    if(!p||inLU[p.pid])return;
    h+='<div class="mut" style="padding:3px 0">'
     +esc(ss[i]||"")+': <b>'+esc(p.n)+'</b> scored '
     +n1(p.act)+' on your bench</div>';});
  }
  h+='</div>';
 }

 h+='<p class="note">'+(done
  ? 'Lineups, per-player points and team totals come '
    +'straight from Sleeper\u2019s record of that week, '
    +'scored under your league\u2019s settings. '
    +'\u201cProj\u201d is what we forecast before '
    +'kickoff, frozen at the time.'
  : 'Projections use our weekly model with byes and Out '
    +'designations at zero. Win probability assumes a '
    +n1(SD)+'-point weekly spread per team.')
  +'</p></div>';
 $("v").innerHTML=h;
 var w=$("wksel");
 if(w)w.onchange=function(){
  WK=Number(w.value);boot2();};
 try{parent.postMessage(
  {kfh:document.body.scrollHeight+24},"*");}catch(e){}
}

var EL={QB:["QB"],RB:["RB"],WR:["WR"],TE:["TE"],K:["K"],
DEF:["DEF","DST"],DST:["DEF","DST"],FLEX:["RB","WR","TE"],
WRRB_FLEX:["RB","WR"],REC_FLEX:["WR","TE"],
SUPER_FLEX:["QB","RB","WR","TE"]};
function elig(p,s){var a=EL[s];
 return a?a.indexOf(p.pos)>=0:false;}
function bestLineup(pool,ss){
 pool=pool.slice().sort(function(a,b){
  return (b.act||0)-(a.act||0);});
 var used={},out=[],fx=[];
 ss.forEach(function(s,i){
  if(s.indexOf("FLEX")>=0){fx.push(i);out[i]=null;return;}
  for(var j=0;j<pool.length;j++){
   if(used[pool[j].pid])continue;
   if(elig(pool[j],s)){out[i]=pool[j];
    used[pool[j].pid]=1;break;}}});
 fx.forEach(function(i){
  for(var j=0;j<pool.length;j++){
   if(used[pool[j].pid])continue;
   if(elig(pool[j],ss[i])){out[i]=pool[j];
    used[pool[j].pid]=1;break;}}});
 return out;}

function boot2(){
 $("v").innerHTML='<p class="mut">Loading week '+WK
  +'\u2026</p>';
 fetch("https://api.sleeper.app/v1/league/"+LID
   +"/matchups/"+WK)
  .then(function(r){return r.json();})
  .then(function(m){MU=m||[];draw();})
  .catch(function(e){
   $("v").innerHTML='<p class="mut">Could not load '
    +'week '+WK+': '+esc(e.message)+'</p>';});
}

function boot(){
 try{var v=localStorage.getItem("kf_myteam");
  if(v)MYID=Number(v);}catch(e){}
 Promise.all([
  fetch("_slteams.json").then(function(r){return r.json();}),
  fetch("_board.json").then(function(r){return r.json();}),
  fetch("_pmap.json").then(function(r){return r.json();}),
  fetch("_wkproj.json").then(function(r){return r.json();})
   .catch(function(){return {};}),
  fetch("_league.json").then(function(r){return r.json();})
   .catch(function(){return null;})
 ]).then(function(a){
  T=a[0];BD=a[1];PM=a[2];PROJ=a[3];LGJ=a[4];
  LID=T.league;SLOTS=T.slots||[];
  (BD.rows||[]).forEach(function(r){
   var p=String(r.pos||"");
   if(p==="DEF"||p==="DST")BDST[String(r.tm||"")]=r;
   else BM[norm(r.n)]=r;});
  if(LGJ&&LGJ.sd)SD=Number(LGJ.sd)||22.5;
  WK=KFwk.cur();
  boot2();
 }).catch(function(e){
  $("v").innerHTML='<p class="mut">Could not load: '
   +esc(e.message)+'</p>';});
}
boot();
"""

HTML = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,'
        'initial-scale=1"><style>__CSS__</style></head>'
        '<body><div id="v" class="mut">Loading matchup\u2026'
        '</div><script src="_score.js"></script>'
        '<script src="_wkpts.js"></script>'
        '<script src="_card.js"></script>'
        '<script>__JS__</script></body></html>')
HTML = HTML.replace("__CSS__", CSS).replace("__JS__", JS)
open("site/matchup.html", "w").write(HTML)
print("wrote site/matchup.html (%d KB)" % (len(HTML) // 1024))

H = open("vaporai.html").read()
OLD = ('<section id="lgh_mu"><iframe '
       'data-src="league.html?tab=mu"')
NEW = '<section id="lgh_mu"><iframe data-src="matchup.html"'
if OLD in H:
    H = H.replace(OLD, NEW, 1)
    open("vaporai.html", "w").write(H)
    print("lgh_mu -> matchup.html")
else:
    assert NEW in H, "lgh_mu iframe not found"
    print("lgh_mu already points at matchup.html")

LZ = open("site/_lazyframe.js").read()
if "kfh" not in LZ:
    LZ = LZ.rstrip() + (
        '\n(function(){window.addEventListener("message",'
        'function(e){var d=e.data;if(!d||!d.kfh)return;'
        'var f=document.querySelectorAll("iframe");'
        'Array.prototype.forEach.call(f,function(x){'
        'if(x.contentWindow===e.source){'
        'x.style.height=Math.max(400,d.kfh)+"px";}});'
        '});})();')
    open("site/_lazyframe.js", "w").write(LZ)
    print("lazyframe: auto-height added")
