CSS = """
*{box-sizing:border-box}
body{margin:0;padding:0 2px 30px;background:transparent;
color:#EAF2F8;font:14px/1.45 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1060px;margin:0 auto}
.top{display:flex;align-items:center;gap:12px;
margin:10px 0 18px}
.top h2{margin:0;font-size:24px;letter-spacing:-.5px}
.wk{margin-left:auto;background:#0A1E33;color:#EAF2F8;
border:1px solid #1C4265;border-radius:10px;
padding:8px 14px;font-size:14px;font-weight:600}
.gm{display:flex;gap:10px;margin-bottom:14px}
.sd{flex:1;background:#0A1E33;border:1px solid #1C4265;
border-radius:14px;padding:14px 16px;min-width:0;
position:relative}
.sd.me{border-color:#FFC20E}
.sd.win{border-color:#0080C6}
.sd .hd{display:flex;align-items:center;gap:10px}
.sd.r .hd{flex-direction:row-reverse;text-align:right}
.sd img{width:48px;height:48px;border-radius:50%;
background:#102C47;object-fit:cover;flex:none;
border:2px solid #1C4265}
.sd .who{min-width:0;flex:1}
.sd .hn{font-size:12px;color:#6F8CA6;white-space:nowrap;
overflow:hidden;text-overflow:ellipsis}
.sd .tn{font-size:16px;font-weight:700;white-space:nowrap;
overflow:hidden;text-overflow:ellipsis}
.sd .pt{font-size:26px;font-weight:800;letter-spacing:-1px;
flex:none}
.bar{height:5px;border-radius:99px;background:#12293F;
margin:12px 0 6px;overflow:hidden}
.bar i{display:block;height:100%;background:#0080C6}
.sd.r .bar i{margin-left:auto;background:#4ADE80}
.ft{display:flex;justify-content:space-between;
font-size:12px;color:#93AFC6}
.sd.r .ft{flex-direction:row-reverse}
.ft b{color:#EAF2F8}
.vs{align-self:center;font-weight:800;
font-size:12px;color:#5C7A94;padding:0 4px}
.fin{position:absolute;top:-9px;left:50%;
transform:translateX(-50%);font-size:9px;font-weight:800;
letter-spacing:.6px;background:#FFC20E;color:#04121F;
padding:2px 9px;border-radius:99px}
.mut{color:#93AFC6;font-size:12px}
.note{margin-top:16px;font-size:11px;color:#6F8CA6}
@media(max-width:620px){.gm{flex-direction:column}
.sd.r .hd{flex-direction:row;text-align:left}
.sd.r .ft{flex-direction:row}}
"""

JS = r"""
var T=null,SCH=null,BD=null,LGJ=null,AV={};
var SLOTS=[],WK=2,MYID=1,SD=22.5;

function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function n1(v){return (Math.round(v*10)/10).toFixed(1);}
function norm(s){return String(s||"").toLowerCase()
 .replace(/[^a-z ]/g,"").replace(/\s+/g," ").trim().replace(/ (jr|sr|iii|ii|iv|v)$/,"");}
function cdf(z){
 var t=1/(1+0.2316419*Math.abs(z));
 var d=0.3989423*Math.exp(-z*z/2);
 var p=d*t*(0.3193815+t*(-0.3565638+t*(1.781478
   +t*(-1.821256+t*1.330274))));
 return z>0?1-p:p;}

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
function ss(){return (SLOTS||[]).filter(function(s){
 return s!=="BN"&&s!=="IR"&&s!=="TAXI";});}

function team(id){
 var o=null;
 (T.teams||[]).forEach(function(t){
  if(Number(t.id)===Number(id))o=t;});
 return o;}

// Projected total from the team's actual starters.
function tproj(t,wk){
 if(!t)return 0;
 var by={},s=0;
 (t.players||[]).forEach(function(p){by[p.pid]=p;});
 (t.starters||[]).forEach(function(pid){
  var p=by[pid];
  if(p)s+=proj(p,wk);});
 return s;}

function side(t,pts,live,wp,cls){
 var av=t?AV[t.id]:null;
 return '<div class="sd '+cls+'">'
  +'<div class="hd">'
  +(av&&av.img?'<img src="'+esc(av.img)+'">':
    '<div style="width:48px;height:48px;border-radius:50%;'
    +'background:#102C47;flex:none"></div>')
  +'<div class="who">'
  +'<div class="hn">@'+esc(av&&av.h?av.h:"")+'</div>'
  +'<div class="tn">'+esc(t?(t.owner||("Team "+t.id))
    :"Bye")+'</div></div>'
  +'<div class="pt">'+n1(pts)+'</div></div>'
  +'<div class="bar"><i style="width:'+wp+'%"></i></div>'
  +'<div class="ft"><span><b>'+Math.round(wp)+'%</b></span>'
  +'<span>'+(t?(t.w+"-"+t.l):"")+'</span>'
  +'<span>'+(live?"live":"proj")+' <b>'+n1(pts)
  +'</b></span></div></div>';
}

function draw(){
 var games=(SCH[String(WK)]||[]);
 var h='<div class="wrap"><div class="top">'
  +'<h2>Matchups</h2><select class="wk" id="wksel">';
 for(var w=1;w<=18;w++)h+='<option value="'+w+'"'
  +(w===WK?' selected':'')+'>Wk. '+w+'</option>';
 h+='</select></div>';

 if(!games.length){
  h+='<p class="mut">No matchups scheduled for week '
   +WK+'.</p></div>';
  $("v").innerHTML=h;wire();return;
 }

 games.forEach(function(g){
  var ta=team(g[0].id),tb=team(g[1].id);
  var pa=Number(g[0].pts||0),pb=Number(g[1].pts||0);
  var done=(pa>0||pb>0);
  var a=done?pa:tproj(ta,WK);
  var b=done?pb:tproj(tb,WK);
  var wa,wb;
  if(done){wa=a>b?100:(a<b?0:50);wb=100-wa;}
  else{
   wa=cdf((a-b)/(SD*Math.SQRT2))*100;
   wb=100-wa;
  }
  var ca=(ta&&Number(ta.id)===Number(MYID))?"me":
   (done&&a>b?"win":"");
  var cb="r "+((tb&&Number(tb.id)===Number(MYID))?"me":
   (done&&b>a?"win":""));
  h+='<div class="gm" style="position:relative">'
   +(done?'<span class="fin">FINAL</span>':'')
   +side(ta,a,false,wa,ca)
   +'<div class="vs">VS</div>'
   +side(tb,b,false,wb,cb)+'</div>';
 });

 h+='<p class="note">Projections sum each team\u2019s '
  +'current Sleeper starters using our weekly model, '
  +'with byes and Out designations zeroed. Win '
  +'probability assumes a '+n1(SD)+'-point weekly spread '
  +'per team. Completed weeks show final scores.</p>';
 h+='</div>';
 $("v").innerHTML=h;
 wire();
 try{parent.postMessage(
  {kfh:document.body.scrollHeight+24},"*");}catch(e){}
}

function wire(){
 var w=$("wksel");
 if(w)w.onchange=function(){WK=Number(w.value);draw();};
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
   if(!x)return;
   AV[r.roster_id]={
    h:x.display_name||"",
    img:x.avatar?("https://sleepercdn.com/avatars/thumbs/"
      +x.avatar):null};
  });
 }).catch(function(){});
}

function boot(){
 try{var m=localStorage.getItem("kf_myteam");
  if(m)MYID=Number(m);}catch(e){}
 Promise.all([
  fetch("_slteams.json").then(function(r){return r.json();}),
  fetch("_lgsched.json").then(function(r){return r.json();}),
  fetch("_board.json").then(function(r){return r.json();}),
  fetch("_projweek.json").then(function(r){return r.json();})
   .catch(function(){return null;}),
  fetch("_league.json").then(function(r){return r.json();})
   .catch(function(){return null;})
 ]).then(function(a){
  T=a[0];SCH=a[1];BD=a[2];PW=a[3];LGJ=a[4];
  SLOTS=T.slots||[];
  (BD.rows||[]).forEach(function(r){
   var p=String(r.pos||"");
   if(p==="DEF"||p==="DST")BDST[String(r.tm||"")]=r;
   else BM[norm(r.n)]=r;});
  if(LGJ&&LGJ.sd)SD=Number(LGJ.sd)||22.5;
  if(LGJ&&LGJ.week)WK=Math.min(18,Number(LGJ.week)+1);
  return avatars(T.league);
 }).then(draw).catch(function(e){
  $("v").innerHTML='<p class="mut">Could not load '
   +'matchups: '+esc(e.message)+'</p>';});
}
boot();
"""

HTML = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,'
        'initial-scale=1"><style>__CSS__</style></head>'
        '<body><div id="v" class="mut">Loading matchups\u2026'
        '</div><script>__JS__</script></body></html>')
HTML = HTML.replace("__CSS__", CSS).replace("__JS__", JS)
open("site/games.html", "w").write(HTML)
print("wrote site/games.html (%d KB)" % (len(HTML) // 1024))

H = open("vaporai.html").read()
OLD = ('<section id="lgh_gm"><iframe '
       'data-src="league.html?tab=gm"')
NEW = '<section id="lgh_gm"><iframe data-src="games.html"'
if OLD in H:
    H = H.replace(OLD, NEW, 1)
    open("vaporai.html", "w").write(H)
    print("lgh_gm -> games.html")
else:
    assert NEW in H, "lgh_gm iframe not found"
    print("lgh_gm already points at games.html")
