
(function(){
if(window.KFcardReady)return;
window.KFcardReady=1;

var TOP=(window.parent===window);
var D={},LOADED=false,TAB="ov",CUR=null;

function norm(s){return String(s||"").toLowerCase()
 .replace(/[^a-z ]/g,"").replace(/\s+/g," ").trim().replace(/ (jr|sr|iii|ii|iv|v)$/,"");}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function n1(v){return v==null||v!==v?"\u2013":
 (Math.round(v*10)/10).toFixed(1);}
function n0(v){return v==null||v!==v?"\u2013":
 String(Math.round(v));}

function grab(u){return fetch(u).then(function(r){
 return r.json();}).catch(function(){return null;});}

function load(){
 if(LOADED)return Promise.resolve();
 return Promise.all([
  grab("_board.json"),grab("_reasons.json"),
  grab("_decomp.json"),grab("_dr.json"),
  grab("_inj.json"),grab("_pnews.json"),
  grab("_hist.json"),grab("_tc.json"),
  grab("_projweek.json")
 ]).then(function(a){
  D.board={};
  ((a[0]&&a[0].rows)||[]).forEach(function(r){
   D.board[norm(r.n)]=r;});
  D.reasons=a[1]||{};D.decomp=a[2]||{};
  D.dr={};(a[3]||[]).forEach(function(r){
   D.dr[norm(r.n)]=r;});
  D.inj=a[4]||{};D.pnews=a[5]||{};
  D.hist=a[6]||{};
  D.tc={};(a[7]||[]).forEach(function(r){
   D.tc[norm(r.n)]=r;});
  D.pw=a[8]||{};
  LOADED=true;
 });
}

function chart(rows){
 if(!rows||!rows.length)
  return '<p class="kfmut">No weekly history.</p>';
 var W=620,H=190,pl=28,pb=26,pt=16;
 var mx=0;
 rows.forEach(function(r){if(r.p>mx)mx=r.p;});
 mx=Math.max(10,Math.ceil(mx/10)*10);
 var avg=0;
 rows.forEach(function(r){avg+=r.p;});
 avg=avg/rows.length;
 var bw=(W-pl-8)/rows.length;
 var s='<svg viewBox="0 0 '+W+' '+H+'" width="100%" '
  +'style="display:block">';
 for(var g=0;g<=4;g++){
  var yv=mx*g/4;
  var y=pt+(H-pt-pb)*(1-g/4);
  s+='<line x1="'+pl+'" y1="'+y+'" x2="'+W+'" y2="'+y
   +'" stroke="#1C4265" stroke-width="1"/>'
   +'<text x="0" y="'+(y+4)+'" fill="#93AFC6" '
   +'font-size="10">'+Math.round(yv)+'</text>';
 }
 var ay=pt+(H-pt-pb)*(1-avg/mx);
 s+='<line x1="'+pl+'" y1="'+ay+'" x2="'+W+'" y2="'+ay
  +'" stroke="#FFC20E" stroke-width="1" '
  +'stroke-dasharray="3 3"/>';
 rows.forEach(function(r,i){
  var h=(H-pt-pb)*(r.p/mx);
  var x=pl+i*bw+bw*0.22,y=H-pb-h;
  var col=r.p>=avg*1.25?"#4ade80":
   (r.p>=avg*0.75?"#f5a524":"#f87171");
  s+='<rect x="'+x+'" y="'+y+'" width="'+(bw*0.56)
   +'" height="'+Math.max(1,h)+'" rx="2" fill="'+col+'">'
   +'<title>Wk '+r.w+" "+r.t+": "+r.p+'</title></rect>'
   +'<text x="'+(x+bw*0.28)+'" y="'+(H-pb+13)
   +'" fill="#93AFC6" font-size="9" '
   +'text-anchor="middle">'+r.w+'</text>';
 });
 s+='</svg>';
 s+='<p class="kfmut" style="margin:8px 0 0">Dashed line '
  +'is this player\u2019s average ('+n1(avg)+'). Green is '
  +'25% above it, red 25% below. Last '+rows.length
  +' games, 2025\u20132026.</p>';
 return s;
}

function body(k){
 var b=D.board[k]||{},rs=D.reasons[k]||{},
  dc=D.decomp[k]||{},dr=D.dr[k]||{},
  nw=D.pnews[k]||{},tc=D.tc[k]||{};
 var hist=(b.pid&&D.hist[b.pid])||[];

 if(TAB==="ov"){
  var h='<div class="kfg">'
   +kc(n1(b.floor),"Floor")+kc(n1(b.base),"Base")
   +kc(n1(b.live),"Live proj")+kc(n1(b.ceil),"Ceiling")
   +'</div>';
  var iv=D.inj[k];
  if(iv&&iv.status&&!/Active/i.test(iv.status)){
   h+='<div class="kfbar" style="border-color:#3A1F1F;'
    +'background:#1a0f0f;margin-bottom:12px">'
    +'<div style="font-size:11px;text-transform:uppercase;'
    +'letter-spacing:.7px;color:#f87171;font-weight:700">'
    +'Injury report</div>'
    +'<div style="font-size:15px;font-weight:700;'
    +'margin:6px 0 2px">'+esc(iv.status)
    +(iv.type?(' \u2014 '+esc(iv.type)):'')+'</div>'
    +(iv.mult!=null?('<div class="kfmut">Our model applies '
      +'a '+Math.round(100*(1-iv.mult))+'% reduction for '
      +'this designation.</div>'):'')
    +'</div>';
  }
  h+='<div class="kfbar">'
   +rw("Overall rank",b.rk?("#"+b.rk):"\u2013")
   +rw("Position rank",b.pos&&b.posrk?
      (b.pos+b.posrk):"\u2013")
   +rw("Tier",b.tier||"\u2013")
   +rw("ADP",b.adp!=null?n1(b.adp):"\u2013")
   +rw("Value vs replacement",b.vorp!=null?
      n1(b.vorp):"\u2013")
   +rw("Trade value",tc.g!=null?n1(tc.g):"\u2013")
   +rw("Bust risk",b.risk!=null?
      (Math.round(b.risk*100)+"%"):"\u2013")
   +rw("Bye week",b.bye||"\u2013")
   +rw("Status",b.inj||"Active")
   +'</div>';
  if(rs.line){
   h+='<h4 style="margin:16px 0 6px;font-size:12px;'
    +'text-transform:uppercase;letter-spacing:.7px;'
    +'color:#93AFC6">Why this projection</h4>'
    +'<div class="kfbar"><p style="margin:0">'
    +esc(rs.line)+'</p>';
   if(rs.move)h+='<p class="kfmut" style="margin:8px 0 0">'
    +'Week 1 moved this projection by '
    +(rs.move>0?"+":"")+n1(rs.move)+' points.</p>';
   h+='</div>';
  }
  return h;
 }
 if(TAB==="wk"){
  var pw=D.pw[k];
  if(!pw||!pw.wk||!pw.wk.length)
   return '<p class="kfmut">No weekly projection for '
    +'this player.</p>';
  var h5='<div class="kfbar"><table style="width:100%;'
   +'border-collapse:collapse;font-size:12px">'
   +'<tr><th style="text-align:left;padding:5px;'
   +'color:#93AFC6">Wk</th>'
   +'<th style="text-align:left;padding:5px;'
   +'color:#93AFC6">Opp</th>'
   +'<th style="text-align:right;padding:5px;'
   +'color:#93AFC6">Proj</th>'
   +'<th style="text-align:right;padding:5px;'
   +'color:#93AFC6">Floor</th>'
   +'<th style="text-align:right;padding:5px;'
   +'color:#93AFC6">Ceiling</th>'
   +'<th style="text-align:right;padding:5px;'
   +'color:#93AFC6">20+</th></tr>';
  pw.wk.forEach(function(w){
   var bye=(w.o==="BYE");
   h5+='<tr style="border-top:1px solid #1C4265'
    +(bye?';opacity:.45':'')+'">'
    +'<td style="padding:5px">'+w.w+'</td>'
    +'<td style="padding:5px">'+esc(w.o)+'</td>'
    +'<td style="padding:5px;text-align:right;'
    +'font-weight:700">'+(bye?"\u2013":n1(w.m))+'</td>'
    +'<td style="padding:5px;text-align:right;'
    +'color:#93AFC6">'+(bye?"":n1(w.f))+'</td>'
    +'<td style="padding:5px;text-align:right;'
    +'color:#93AFC6">'+(bye?"":n1(w.c))+'</td>'
    +'<td style="padding:5px;text-align:right">'
    +(bye?"":(Math.round(100*w.p20)+"%"))+'</td></tr>';});
  h5+='</table><p class="kfmut" style="margin:10px 0 0">'
   +'Each week projected separately against that '
   +'opponent\u2019s pass defence. Floor and ceiling are '
   +'the 10th and 90th percentile outcomes. Bye week '
   +'scores zero.</p></div>';
  return h5;
 }
 if(TAB==="pf")return chart(hist);
 if(TAB==="us"){
  var st=rs.stats||{};
  var h2='<div class="kfg">'
   +kc(rs.snap!=null?Math.round(rs.snap*100)+"%":"\u2013",
      "Snap share")
   +kc(dc.touch!=null?n0(dc.touch):"\u2013","Touches")
   +kc(dc.typt!=null?n1(dc.typt):"\u2013","Touches/gm")
   +kc(st.tgt||"\u2013","Targets")
   +'</div><div class="kfbar">'
   +rw("Carries",st.car||"\u2013")
   +rw("Rush yards",st.rushyd||"\u2013")
   +rw("Receptions",st.rec||"\u2013")
   +rw("Rec yards",st.recyd||"\u2013")
   +rw("Snap trend",dc.d_snap!=null?
      ((dc.d_snap>0?"+":"")+n1(dc.d_snap*100)+"%"):"\u2013")
   +rw("Touch trend",dc.d_touch!=null?
      ((dc.d_touch>0?"+":"")+n1(dc.d_touch)):"\u2013")
   +'</div>';
  if(!rs.snap&&!dc.touch)
   h2='<p class="kfmut">No usage data for this player '
    +'yet \u2014 usually means limited 2026 snaps.</p>';
  return h2;
 }
 if(TAB==="sn"){
  if(!dr.pts)return '<p class="kfmut">No season '
   +'projection on file.</p>';
  return '<div class="kfg">'
   +kc(n1(dr.pts),"Season pts")+kc(n1(dr.avg),"Per game")
   +kc(dr.rk?("#"+dr.rk):"\u2013","Rank")
   +kc(dr.prk?(dr.p+dr.prk):"\u2013","Pos rank")
   +'</div><div class="kfbar">'
   +rw("Carries",n0(dr.car))+rw("Rush yards",n0(dr.ryd))
   +rw("Rush TD",n0(dr.rtd))+rw("Targets",n0(dr.tar))
   +rw("Receptions",n0(dr.rec))+rw("Rec yards",n0(dr.cyd))
   +rw("Rec TD",n0(dr.ctd))+'</div>';
 }
 if(TAB==="nw"){
  var it=nw.items||[];
  if(nw.line&&!it.length)
   return '<div class="kfbar"><p style="margin:0">'
    +esc(nw.line)+'</p></div>';
  if(!it.length)return '<p class="kfmut">No recent news '
   +'matched this player in the current feed pool.</p>';
  var h3='<div class="kfbar">';
  if(nw.line)h3+='<p style="margin:0 0 10px">'
   +esc(nw.line)+'</p>';
  it.forEach(function(x){
   h3+='<a class="kfnw" target="_blank" rel="noopener" '
    +'href="'+esc(x.u||"#")+'"><b>'+esc(x.t)+'</b>'
    +'<em>'+esc(x.s||"")+'</em></a>';
  });
  return h3+'</div>';
 }
 return "";
}
function kc(v,l){return '<div class="kfc"><b>'+v
 +'</b><span>'+l+'</span></div>';}
function rw(l,v){return '<div class="kfrow"><span>'+l
 +'</span><b>'+esc(v)+'</b></div>';}

function render(){
 var k=CUR,b=D.board[k]||{},rs=D.reasons[k]||{};
 var nm=b.n||rs.n||k;
 var hist=(b.pid&&D.hist[b.pid])||[];
 var ppg=0;
 if(hist.length){hist.forEach(function(r){ppg+=r.p;});
  ppg=ppg/hist.length;}
 var inj=b.inj||"";
 var badge=(inj&&!/Active/i.test(inj))?
  '<span class="kfpill bad">'+esc(inj)+'</span>':'';
 document.getElementById("kfbx").innerHTML=
  '<div class="kfhd">'
  +(b.img?'<img src="'+esc(b.img)+'">':'')
  +'<div><h2>'+esc(nm)+badge+'</h2>'
  +'<div class="sub">'+esc(b.pos||"")+' &middot; '
  +esc(b.tm||"FA")
  +(b.bye?(' &middot; bye '+b.bye):'')+'</div></div>'
  +'<button class="kfx" id="kfclose">&times;</button>'
  +'</div>'
  +'<div class="kfkpi">'
  +kc(b.rk?("#"+b.rk):"\u2013","Overall")
  +kc(b.pos&&b.posrk?(b.pos+b.posrk):"\u2013","Position")
  +kc(n1(ppg),"PPG last 24")
  +kc(n1(b.live),"Projected")
  +'</div>'
  +'<div class="kftabs">'
  +tb("ov","Overview")+tb("wk","Weekly")+tb("pf","Performance")
  +tb("us","Usage")+tb("sn","Season")+tb("nw","News")
  +'</div><div id="kfbd">'+body(k)+'</div>';

 document.getElementById("kfclose").onclick=close;
 Array.prototype.forEach.call(
  document.querySelectorAll(".kftabs button"),
  function(e){
   e.onclick=function(){
    TAB=e.getAttribute("data-t");render();};});
}
function tb(id,l){return '<button data-t="'+id+'"'
 +(TAB===id?' class="on"':'')+'>'+l+'</button>';}

function close(){
 var o=document.getElementById("kfov");
 if(o)o.className="";
}

function shell(){
 if(document.getElementById("kfov"))return;
 var st=document.createElement("style");
 st.textContent="\n#kfov{position:fixed;inset:0;background:rgba(0,0,0,.72);\nz-index:99999;display:none;overflow:auto;padding:24px 14px}\n#kfov.on{display:block}\n#kfbx{max-width:940px;margin:0 auto;background:#04121F;\nborder:1px solid #1C4265;border-radius:16px;\nbox-shadow:0 20px 60px rgba(0,0,0,.6);overflow:hidden}\n.kfhd{display:flex;gap:16px;align-items:center;padding:18px 20px;\nborder-bottom:1px solid #1C4265;position:relative}\n.kfhd img{width:74px;height:74px;border-radius:50%;\nbackground:#1C4265;object-fit:cover;flex:none}\n.kfhd h2{margin:0;font-size:22px;letter-spacing:-.4px}\n.kfhd .sub{color:#93AFC6;font-size:13px;margin-top:3px}\n.kfx{position:absolute;top:14px;right:16px;width:30px;\nheight:30px;border-radius:50%;border:1px solid #1C4265;\nbackground:#0A1E33;color:#EAF2F8;cursor:pointer;font-size:15px;\nline-height:1}\n.kfkpi{display:grid;grid-template-columns:repeat(4,1fr);\nborder-bottom:1px solid #1C4265}\n.kfkpi div{padding:12px 14px;border-right:1px solid #1C4265}\n.kfkpi div:last-child{border-right:0}\n.kfkpi b{display:block;font-size:20px;font-weight:800;\nletter-spacing:-.5px}\n.kfkpi span{font-size:10px;color:#93AFC6;\ntext-transform:uppercase;letter-spacing:.7px}\n.kftabs{display:flex;gap:2px;padding:0 14px;\nborder-bottom:1px solid #1C4265;overflow-x:auto}\n.kftabs button{background:none;border:0;color:#93AFC6;\npadding:11px 13px;font-size:13px;font-weight:600;\ncursor:pointer;border-bottom:2px solid transparent;\nwhite-space:nowrap}\n.kftabs button.on{color:#EAF2F8;border-bottom-color:#FFC20E}\n#kfbd{padding:16px 20px 24px;min-height:200px}\n.kfg{display:grid;\ngrid-template-columns:repeat(auto-fit,minmax(150px,1fr));\ngap:8px;margin-bottom:14px}\n.kfc{background:#0A1E33;border:1px solid #1C4265;\nborder-radius:10px;padding:10px 12px}\n.kfc b{display:block;font-size:17px;font-weight:700}\n.kfc span{font-size:10px;color:#93AFC6;\ntext-transform:uppercase;letter-spacing:.6px}\n.kfbar{background:#0A1E33;border:1px solid #1C4265;\nborder-radius:10px;padding:12px}\n.kfrow{display:flex;justify-content:space-between;\npadding:6px 0;border-bottom:1px solid #1C4265;font-size:13px}\n.kfrow:last-child{border:0}\n.kfrow span{color:#93AFC6}\n.kfnw{display:block;padding:9px 0;\nborder-bottom:1px solid #1C4265;color:#EAF2F8;\ntext-decoration:none;font-size:13px}\n.kfnw:last-child{border:0}\n.kfnw:hover b{color:#FFC20E}\n.kfnw em{display:block;color:#93AFC6;font-size:11px;\nfont-style:normal;margin-top:2px}\n.kfmut{color:#93AFC6;font-size:13px}\n.kfpill{display:inline-block;font-size:10px;padding:2px 7px;\nborder-radius:99px;background:#26262e;color:#93AFC6;\nmargin-left:6px;vertical-align:middle}\n.kfpill.bad{background:#3a1f1f;color:#f87171}\n.kfpill.good{background:#14301c;color:#4ade80}\n[data-kfp]{cursor:pointer}\n";
 document.head.appendChild(st);
 var o=document.createElement("div");
 o.id="kfov";
 o.innerHTML='<div id="kfbx"></div>';
 o.addEventListener("click",function(e){
  if(e.target===o)close();});
 document.body.appendChild(o);
 document.addEventListener("keydown",function(e){
  if(e.key==="Escape")close();});
}

window.KFcard=function(name){
 var k=norm(name);
 if(!k)return;
 if(!TOP){
  try{parent.postMessage({kfcard:name},"*");return;}
  catch(e){}
 }
 shell();
 CUR=k;TAB="ov";
 document.getElementById("kfov").className="on";
 document.getElementById("kfbx").innerHTML=
  '<div class="kfhd"><h2>Loading\u2026</h2></div>';
 load().then(function(){
  if(!D.board[k]&&!D.reasons[k]){
   document.getElementById("kfbx").innerHTML=
    '<div class="kfhd"><h2>'+esc(name)+'</h2>'
    +'<button class="kfx" id="kfclose">&times;</button>'
    +'</div><div id="kfbd"><p class="kfmut">No profile '
    +'for this player \u2014 not in the projection set.'
    +'</p></div>';
   document.getElementById("kfclose").onclick=close;
   return;
  }
  render();
 });
};

if(TOP){
 window.addEventListener("message",function(e){
  var d=e.data;
  if(d&&d.kfcard)window.KFcard(d.kfcard);
 });
}

document.addEventListener("click",function(e){
 var t=e.target;
 while(t&&t!==document.body){
  if(t.getAttribute&&t.getAttribute("data-kfp")){
   e.preventDefault();
   window.KFcard(t.getAttribute("data-kfp"));
   return;
  }
  t=t.parentNode;
 }
},false);
})();
