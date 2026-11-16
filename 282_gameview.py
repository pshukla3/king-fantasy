import os, sys
if os.path.exists("site/_game.js") and \
        "m.feat" in open("site/_game.js").read():
    print("SUPERSEDED by 283_wpm_fix.py - refusing to clobber _game.js")
    sys.exit(0)
import json
import re
import shutil

W = json.load(open("site/_wp.json"))

def norm(m):
    if not isinstance(m, dict):
        return None
    IK = ("intercept", "b0", "const", "bias", "b")
    CK = ("coef", "coefs", "coefficients", "beta",
          "w", "weights", "params")
    for ik in IK:
        for ck in CK:
            if ik in m and isinstance(m.get(ck), dict):
                return {"i": float(m[ik]),
                        "c": {k: float(v)
                              for k, v in m[ck].items()
                              if isinstance(v, (int, float))}}
    nums = {k: v for k, v in m.items()
            if isinstance(v, (int, float))}
    for ik in IK:
        if ik in nums and len(nums) > 1:
            return {"i": float(nums[ik]),
                    "c": {k: float(v)
                          for k, v in nums.items() if k != ik}}
    for k in ("model", "fit", "logit"):
        if k in m:
            r = norm(m[k])
            if r:
                return r
    return None

act = W.get("active") if isinstance(W.get("active"), dict) else {}
PN = act.get("pregame", "pregame")
IN = act.get("ingame", "mkt2")
PRE = norm(W.get(PN)) or norm(W.get("pregame"))
ING = norm(W.get(IN)) or norm(W.get("mkt2"))
OT = 0.602
if isinstance(act.get("ot_first_poss"), (int, float)):
    OT = float(act["ot_first_poss"])

if not PRE or not ING:
    print("COULD NOT NORMALIZE - structure follows")
    print("top keys:", list(W.keys()))
    print(json.dumps(W)[:1500])
    raise SystemExit(1)

print("pregame model '%s': intercept %+.4f, %d coefs"
      % (PN, PRE["i"], len(PRE["c"])))
for k, v in sorted(PRE["c"].items(),
                   key=lambda x: -abs(x[1]))[:6]:
    print("    %-20s %+.4f" % (k, v))
print("ingame model '%s': intercept %+.4f, %d coefs"
      % (IN, ING["i"], len(ING["c"])))
for k, v in sorted(ING["c"].items(),
                   key=lambda x: -abs(x[1]))[:8]:
    print("    %-20s %+.4f" % (k, v))
print("ot first possession: %.3f" % OT)

JS = r'''(function(){
var M=__WPM__;
var E2N={"LAR":"LA","WSH":"WAS","JAC":"JAX","AZ":"ARI"};
function nz(a){a=(a||"").toUpperCase();return E2N[a]||a;}
var SCH=null,QT=null,PM=null,BUSY=false;
function J(u){return fetch(u).then(function(r){
 if(!r.ok)throw new Error("HTTP "+r.status);
 return r.json();});}
function lg(z){return 1/(1+Math.exp(-z));}
function ev(m,f){if(!m)return 0.5;var z=m.i,k;
 for(k in m.c){z+=m.c[k]*(f[k]||0);}return lg(z);}
function ft(sd,t,y,dn,ds,sp){t=Math.max(1,t);
 return {sd_t:sd/Math.sqrt(t/60+1),
  expt:Math.exp(-4*t/3600),score_differential:sd,
  t:t,half:t<=1800?t:t-1800,down:dn||1,
  ydstogo:ds||10,yardline_100:(y==null?50:y),
  to_diff:0,is4:(dn===4?1:0),spread_pos:sp||0,
  sp_t:(sp||0)*(t/3600)};}
function esc(x){return String(x==null?"":x).replace(
 /[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",
 ">":"&gt;","\"":"&quot;"}[c];});}
function pad(n){return (n<10?"0":"")+n;}
function secs(clock,per){
 var p=String(clock||"0:00").split(":");
 var s=(parseInt(p[0],10)||0)*60+(parseInt(p[1],10)||0);
 var q=Math.min(4,per||1);
 return s+(4-q)*900;}

function field(y,dir,ha,aa){
 var x=10+(dir>0?(100-y):y);
 var g="",i;
 for(i=1;i<10;i++){g+='<line x1="'+(10+i*10)+'" y1="0" x2="'
  +(10+i*10)+'" y2="53.3" stroke="#2a2c30" stroke-width=".3"/>';}
 return '<svg viewBox="0 0 120 53.3" class="gvfld">'
 +'<rect x="0" y="0" width="120" height="53.3" fill="#0d1a12"/>'
 +'<rect x="0" y="0" width="10" height="53.3" fill="#16241a"/>'
 +'<rect x="110" y="0" width="10" height="53.3" fill="#16241a"/>'
 +g+'<line x1="60" y1="0" x2="60" y2="53.3" stroke="#3a3d42" '
 +'stroke-width=".5"/>'
 +'<circle cx="'+x+'" cy="26.6" r="2.2" fill="#e8eaed"/>'
 +'<text x="5" y="30" fill="#5f6368" font-size="5" '
 +'text-anchor="middle">'+esc(aa)+'</text>'
 +'<text x="115" y="30" fill="#5f6368" font-size="5" '
 +'text-anchor="middle">'+esc(ha)+'</text></svg>';}

function curve(pts){
 if(!pts.length)return '<div class="gvmut">'
  +'win probability chart appears once the game starts</div>';
 var w=560,h=110,d="",i;
 for(i=0;i<pts.length;i++){
  var x=w*i/Math.max(1,pts.length-1);
  var y=h*(1-pts[i]);
  d+=(i?"L":"M")+x.toFixed(1)+" "+y.toFixed(1);}
 return '<svg viewBox="0 0 '+w+' '+h+'" class="gvcrv">'
 +'<line x1="0" y1="'+(h/2)+'" x2="'+w+'" y2="'+(h/2)+'" '
 +'stroke="#2a2c30" stroke-width="1"/>'
 +'<path d="'+d+'" fill="none" stroke="#8ab4f8" '
 +'stroke-width="2"/></svg>';}

function qtab(sd,q){
 if(!QT)return "";
 var rows="",k,tb=QT.table||QT;
 for(k in tb){
  var v=tb[k];
  if(typeof v==="number"){
   rows+='<tr><td>'+esc(k)+'</td><td>'
   +(100*v).toFixed(1)+'%</td></tr>';}}
 if(!rows)return "";
 return '<h4>Empirical, 3,018 games</h4>'
 +'<table class="gvqt">'+rows+'</table>';}

function shell(){
 if(document.getElementById("gvx"))return;
 var d=document.createElement("div");
 d.id="gvx";d.className="gvov";d.style.display="none";
 d.innerHTML='<div class="gvbx"><button class="gvcl" '
 +'id="gvclose">close</button><div id="gvbody"></div></div>';
 document.body.appendChild(d);
 d.addEventListener("click",function(e){
  if(e.target===d)hide();});
 document.getElementById("gvclose")
  .addEventListener("click",hide);
 document.addEventListener("keydown",function(e){
  if(e.key==="Escape")hide();});}
function hide(){var d=document.getElementById("gvx");
 if(d)d.style.display="none";}
function show(h){shell();
 document.getElementById("gvbody").innerHTML=h;
 document.getElementById("gvx").style.display="flex";}

function findDate(a,h){
 if(!SCH||!SCH.sched)return null;
 var t=SCH.sched[h],w;
 if(t){for(w in t){if(t[w].o===a&&t[w].at==="vs")
  return t[w].d;}}
 t=SCH.sched[a];
 if(t){for(w in t){if(t[w].o===h&&t[w].at==="@")
  return t[w].d;}}
 return null;}

function open2(a,h,meta){
 if(BUSY)return;BUSY=true;
 show('<div class="gvhd"><b>'+esc(a)+' @ '+esc(h)
  +'</b><span>'+esc(meta)+'</span></div>'
  +'<div class="gvmut">loading...</div>');
 var d=findDate(a,h);
 if(!d){render(a,h,meta,null,null);BUSY=false;return;}
 var ds=d.replace(/-/g,"");
 J("https://site.api.espn.com/apis/site/v2/sports/"
  +"football/nfl/scoreboard?dates="+ds)
 .then(function(sb){
  var ev=(sb.events||[]),i,found=null;
  for(i=0;i<ev.length;i++){
   var c=(ev[i].competitions||[])[0];if(!c)continue;
   var t=(c.competitors||[]).map(function(x){
    return nz((x.team||{}).abbreviation);});
   if(t.indexOf(a)>=0&&t.indexOf(h)>=0){found=ev[i];break;}}
  if(!found){render(a,h,meta,null,null);BUSY=false;return;}
  return J("https://site.api.espn.com/apis/site/v2/sports/"
   +"football/nfl/summary?event="+found.id)
   .then(function(sm){render(a,h,meta,found,sm);BUSY=false;});})
 .catch(function(e){
  render(a,h,meta,null,null);BUSY=false;});}

function render(a,h,meta,evt,sm){
 var sp=0,hasSp=false,st="",series=[],ply=[];
 var sd=0,tl=3600,y=75,dn=1,ds=10,posHome=true,live=false;
 if(evt){var c=(evt.competitions||[])[0]||{};
  st=((evt.status||{}).type||{}).shortDetail||"";
  var od=(c.odds||[])[0];
  if(od&&typeof od.spread==="number"){sp=od.spread;hasSp=true;}
  live=(((evt.status||{}).type||{}).state==="in");}
 var hAdv=hasSp?(-sp):0;
 if(sm&&sm.drives){
  var prev=(sm.drives.previous||[]),i,k;
  for(i=0;i<prev.length;i++){
   var pl=(prev[i].plays||[]);
   for(k=0;k<pl.length;k++){
    var p=pl[k],s=p.start||{};
    if(!s.down)continue;
    var per=((p.period||{}).number)||1;
    var tt=secs(((p.clock||{}).displayValue),per);
    var ph=String(((s.team||{}).id))===String(
     ((((sm.header||{}).competitions||[])[0]||{})
      .competitors||[]).filter(function(x){
      return x.homeAway==="home";}).map(function(x){
      return x.id;})[0]);
    var pd=(p.homeScore||0)-(p.awayScore||0);
    var msd=ph?pd:-pd;
    var msp=ph?hAdv:-hAdv;
    var f=ft(msd,tt,(s.yardsToEndzone==null?50:
     s.yardsToEndzone),s.down,s.distance,msp);
    var w=ev(M.ing,f);
    series.push(ph?w:1-w);
    ply.push({t:p.text||"",q:per,
     c:((p.clock||{}).displayValue)||""});
    sd=msd;tl=tt;y=(s.yardsToEndzone==null?50:
     s.yardsToEndzone);dn=s.down;ds=s.distance;posHome=ph;}}}
 var hw;
 if(series.length){hw=series[series.length-1];}
 else{hw=ev(M.pre,ft(0,3600,75,1,10,hAdv));}
 var aw=1-hw;
 var spTxt=hasSp?((sp<0?h:a)+" by "+Math.abs(sp).toFixed(1))
  :"line unavailable";
 var mdl=series.length?"in-game (mkt2)":"pregame (line)";
 var pl2=ply.slice(-12).reverse().map(function(p){
  return '<div class="gvpl"><span>Q'+p.q+" "+esc(p.c)
  +'</span>'+esc(p.t)+'</div>';}).join("")
  ||'<div class="gvmut">no plays yet</div>';
 var roster="";
 if(PM){var ct=0,id;
  for(id in PM){var q=PM[id];
   if(!q||ct>=16)continue;
   var tm=nz(q.team||q.t);
   if(tm===a||tm===h){
    roster+='<div class="gvrp"><b>'+esc(q.name||q.n)
    +'</b><span>'+esc((q.pos||q.p)+" "+tm)+'</span></div>';
    ct++;}}}
 show('<div class="gvhd"><b>'+esc(a)+' @ '+esc(h)+'</b>'
  +'<span>'+esc(st||meta)+'</span></div>'
  +'<div class="gvwp"><div class="gvt"><i>'+esc(a)+'</i>'
  +'<b>'+(100*aw).toFixed(1)+'%</b></div>'
  +'<div class="gvbar"><div style="width:'
  +(100*hw).toFixed(1)+'%"></div></div>'
  +'<div class="gvt"><i>'+esc(h)+'</i><b>'
  +(100*hw).toFixed(1)+'%</b></div></div>'
  +'<div class="gvsub">'+esc(spTxt)+' &middot; model: '
  +esc(mdl)+'</div>'
  +field(y,posHome?1:-1,h,a)
  +'<div class="gvgrid"><div><h4>Win probability</h4>'
  +curve(series)+'<h4>Plays</h4>'+pl2+'</div>'
  +'<div>'+qtab(sd,tl)
  +(roster?'<h4>Fantasy players</h4>'+roster:"")
  +'</div></div>');}

function boot(){
 var cards=document.querySelectorAll(".sbc");
 if(!cards.length)return;
 Promise.all([
  J("_sched.json").then(function(d){SCH=d;})
   .catch(function(){}),
  J("_qtr.json").then(function(d){QT=d;})
   .catch(function(){}),
  J("_pmap.json").then(function(d){PM=d;})
   .catch(function(){})
 ]).then(function(){
  Array.prototype.forEach.call(cards,function(c){
   var im=c.querySelectorAll(".sbrow img");
   if(im.length<2)return;
   var a=nz(im[0].getAttribute("alt"));
   var h=nz(im[1].getAttribute("alt"));
   var mt=(c.querySelector(".sbmeta")||{}).textContent||"";
   c.style.cursor="pointer";
   c.setAttribute("title","win probability");
   c.addEventListener("click",function(){
    open2(a,h,mt);});});
  console.log("game view wired to "+cards.length+" games");});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",boot);}
else{boot();}
})();'''

JS = JS.replace("__WPM__", json.dumps(
    {"pre": PRE, "ing": ING, "ot": OT}))
open("site/_game.js", "w").write(JS)
print("\nwrote site/_game.js (%d bytes)" % len(JS))

CSS = ('<!--GVCSS--><style>'
       '.gvov{position:fixed;inset:0;z-index:200;'
       'background:rgba(4,5,7,.86);display:flex;'
       'align-items:flex-start;justify-content:center;'
       'overflow-y:auto;padding:34px 16px}'
       '.gvbx{background:#0d0e10;border:1px solid #2a2c30;'
       'border-radius:4px;max-width:940px;width:100%;'
       'padding:20px 22px;position:relative}'
       '.gvcl{position:absolute;top:12px;right:14px;'
       'background:#1a1c1f;color:#9aa0a6;border:1px solid '
       '#2a2c30;border-radius:3px;padding:4px 10px;'
       'cursor:pointer;font-size:11px}'
       '.gvhd{display:flex;justify-content:space-between;'
       'align-items:baseline;border-bottom:1px solid #2a2c30;'
       'padding-bottom:10px;margin-bottom:14px}'
       '.gvhd b{font-size:19px;color:#e8eaed}'
       '.gvhd span{font-size:11px;color:#5f6368;'
       'text-transform:uppercase;letter-spacing:.07em}'
       '.gvwp{display:flex;align-items:center;gap:14px;'
       'margin:6px 0}'
       '.gvt{display:flex;flex-direction:column;min-width:64px}'
       '.gvt i{font-style:normal;font-size:11px;color:#5f6368}'
       '.gvt b{font-size:20px;color:#e8eaed}'
       '.gvbar{flex:1;height:9px;background:#3c4043;'
       'border-radius:5px;overflow:hidden}'
       '.gvbar div{height:100%;background:#8ab4f8}'
       '.gvsub{font-size:11px;color:#5f6368;margin-bottom:12px;'
       'text-transform:uppercase;letter-spacing:.06em}'
       '.gvfld{width:100%;height:auto;border:1px solid #2a2c30;'
       'border-radius:3px;margin-bottom:16px}'
       '.gvcrv{width:100%;height:auto;margin-bottom:8px}'
       '.gvgrid{display:grid;grid-template-columns:1.6fr 1fr;'
       'gap:22px}'
       '.gvgrid h4{margin:14px 0 7px;font-size:11px;'
       'color:#9aa0a6;text-transform:uppercase;'
       'letter-spacing:.08em;font-weight:600}'
       '.gvpl{font-size:12px;color:#c8ccd0;padding:6px 0;'
       'border-bottom:1px solid #1c1e21;line-height:1.45}'
       '.gvpl span{color:#5f6368;margin-right:8px;'
       'font-size:10px}'
       '.gvqt{width:100%;font-size:12px;color:#c8ccd0;'
       'border-collapse:collapse}'
       '.gvqt td{padding:4px 0;border-bottom:1px solid #1c1e21}'
       '.gvqt td:last-child{text-align:right;color:#8ab4f8}'
       '.gvrp{display:flex;justify-content:space-between;'
       'font-size:12px;padding:5px 0;'
       'border-bottom:1px solid #1c1e21}'
       '.gvrp span{color:#5f6368;font-size:11px}'
       '.gvmut{color:#5f6368;font-size:12px;padding:8px 0}'
       '@media(max-width:760px){.gvgrid{'
       'grid-template-columns:1fr}}'
       '</style>')

H = open("vaporai.html").read()
n0 = len(H)
if "<!--GVCSS-->" in H:
    i = H.index("<!--GVCSS-->")
    j = H.index("</style>", i) + 8
    H = H[:i] + CSS + H[j:]
    print("gv css replaced")
else:
    H = H.replace("</head>", CSS + "</head>", 1)
    print("gv css inserted")

TAG = '<script src="_game.js"></script>'
if TAG not in H:
    H = H.replace("</body>", TAG + "</body>", 1)
    print("game.js tag added")
else:
    print("game.js tag already present")

assert len(H) > n0 * 0.9, "size drop, abort"
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
