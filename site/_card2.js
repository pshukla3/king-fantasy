(function(){
var CSS=`
#kfc{position:fixed;inset:0;background:rgba(0,0,0,.82);
 z-index:99999;display:none;overflow:auto;
 backdrop-filter:blur(3px)}
#kfc.on{display:block}
.kfw{max-width:1180px;margin:26px auto;background:#0a0a0a;
 border:1px solid #232323;border-radius:16px;
 font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",
 Roboto,sans-serif;color:#eee;overflow:hidden}
.kfh{display:flex;align-items:center;gap:14px;padding:16px 20px;
 border-bottom:1px solid #1c1c1c}
.kfchip{display:flex;align-items:center;gap:11px;
 background:#141414;border:1px solid #262626;
 border-radius:14px;padding:8px 14px 8px 8px}
.kfchip img{width:42px;height:42px;border-radius:11px;
 object-fit:cover;background:#222}
.kfchip b{font-size:15px;font-weight:700;display:block}
.kfbadge{display:inline-block;font-size:10px;font-weight:800;
 padding:2px 8px;border-radius:5px;margin-right:5px}
.b-QB{background:#3ddc84;color:#06180f}
.b-RB{background:#4da3ff;color:#06101d}
.b-WR{background:#ff4d6d;color:#1d0810}
.b-TE{background:#b07cff;color:#140823}
.b-K,.b-DEF{background:#666;color:#111}
.kftm{background:#1e1e1e;color:#bbb;font-size:10px;
 font-weight:700;padding:2px 8px;border-radius:5px}
.kfx{margin-left:auto;background:#161616;border:1px solid #2a2a2a;
 color:#aaa;width:34px;height:34px;border-radius:50%;
 cursor:pointer;font-size:17px;line-height:1}
.kfx:hover{color:#fff;border-color:#555}
.kftabs{display:flex;gap:2px;padding:0 20px;
 border-bottom:1px solid #1c1c1c;overflow-x:auto}
.kftabs button{background:none;border:0;border-bottom:2px solid
 transparent;color:#777;padding:12px 16px;cursor:pointer;
 font-size:14px;font-weight:600;white-space:nowrap}
.kftabs button:hover{color:#ccc}
.kftabs button.on{color:#fff;border-bottom-color:#ff7a18}
.kfbody{padding:20px}
.kfhero{text-align:center;padding:14px 0 6px}
.kfhero h1{font-size:34px;font-weight:800;letter-spacing:-1px}
.kfhero h1 span{color:#4da3ff}
.kfhero img{height:190px;object-fit:contain;margin:10px 0}
.kfstat{display:grid;grid-template-columns:repeat(5,1fr);
 border-radius:10px;overflow:hidden;margin-top:12px}
.kfstat div{padding:10px;text-align:center;background:#121212}
.kfstat div:nth-child(odd){background:#4da3ff;color:#06101d}
.kfstat .lb{font-size:11px;font-weight:800;letter-spacing:.6px;
 text-transform:uppercase;opacity:.85}
.kfstat .vl{font-size:24px;font-weight:800;margin-top:2px}
.kfcard{background:#101010;border:1px solid #1e1e1e;
 border-radius:13px;padding:16px;margin-top:14px}
.kfcard h3{font-size:15px;font-weight:800;margin-bottom:10px}
.kfsum{color:#bbb;font-size:13.5px;line-height:1.65}
.kfsum b{color:#fff}
.kfpill{display:inline-block;background:#161616;
 border:1px solid #282828;border-radius:20px;
 padding:4px 11px;margin:3px 5px 3px 0;font-size:12px;
 color:#bbb}
.kfpill b{color:#fff}
table.kft{width:100%;border-collapse:collapse;font-size:12.5px}
table.kft th{color:#777;font-size:10px;font-weight:700;
 text-transform:uppercase;letter-spacing:.7px;
 padding:7px 6px;text-align:right;border-bottom:1px solid #1e1e1e}
table.kft th:first-child{text-align:left}
table.kft td{padding:7px 6px;text-align:right;
 border-bottom:1px solid #151515}
table.kft td:first-child{text-align:left;color:#ddd;
 font-weight:600}
.hi{color:#3ddc84}.mid{color:#ffa63d}.lo{color:#ff5d6c}
.dim{color:#555}
.kfproj{background:#0d1521;border-left:2px solid #4da3ff}
`;
var st=document.createElement("style");
st.textContent=CSS;document.head.appendChild(st);

var DB=null,RH=null,CUR=null,TAB="general";
function load(){
 if(DB)return Promise.resolve(DB);
 return Promise.all([
  fetch("_cards.json?v="+Date.now()).then(function(r){return r.json()}),
  fetch("_rankhist.json?v="+Date.now()).then(function(r){
    return r.json()}).catch(function(){return {}})
 ]).then(function(a){DB=a[0];RH=a[1]||{};return DB});}
function nm(s){return String(s||"").toLowerCase()
 .replace(/[^a-z ]/g,"").replace(/\s+/g," ").trim().replace(/ (jr|sr|iii|ii|iv|v)$/,"");}
var BYID=null;
function idx(){
 if(BYID)return BYID;
 BYID={};
 for(var k in DB){if(DB[k].pid)BYID[String(DB[k].pid)]=DB[k];}
 return BYID;}
function find(name){
 var ix=idx();
 if(ix[String(name)])return ix[String(name)];
 var k=nm(name);
 if(DB[k])return DB[k];
 var sf=[" sr"," jr"," ii"," iii"," iv"," v"];
 for(var i=0;i<sf.length;i++){
  if(DB[k+sf[i]])return DB[k+sf[i]];
  if(k.endsWith(sf[i])&&DB[k.slice(0,-sf[i].length)])
   return DB[k.slice(0,-sf[i].length)];}
 for(var kk in DB){if(kk.indexOf(k)>=0||k.indexOf(kk)>=0)
  return DB[kk];}
 return null;}
window.KFcard2={open:function(name){
 load().then(function(){
  var p=find(name);
  if(!p){alert("No card data for "+name);return}
  CUR=p;TAB="general";render();
  document.getElementById("kfc").classList.add("on");
  document.body.style.overflow="hidden";});
},close:function(){
  document.getElementById("kfc").classList.remove("on");
  document.body.style.overflow="";}};

function fmt(v,d){return (v==null||v!==v)?"-":
 Number(v).toFixed(d==null?1:d);}
function col(v,a,b){return v>=b?"hi":(v>=a?"mid":"lo");}

function summary(p){
 var s=[],pos=p.pos,log=(p.log||[]).filter(function(x){
  return x.s===2026});
 var n=log.length||1;
 var pts=log.reduce(function(a,x){return a+x.p},0)/n;
 var proj=(p.proj||[]).filter(function(x){
  return x.o!=="BYE"&&!x.out});
 var pj=proj.length?proj.reduce(function(a,x){
  return a+x.m},0)/proj.length:0;
 s.push("<b>"+p.n+"</b> is projected for <b>"+fmt(pj)+
  "</b> points per game the rest of the way, ranked <b>"+
  (p.pos||"")+(p.posrk||"?")+"</b> overall <b>#"+
  (p.rk||"?")+"</b>.");
 if(log.length)
  s.push("He is averaging <b>"+fmt(pts)+
   "</b> through "+n+" game"+(n>1?"s":"")+" this season.");
 if(pos==="WR"||pos==="TE"){
  var t=log.reduce(function(a,x){return a+x.ta},0)/n;
  var r=log.reduce(function(a,x){return a+x.re},0)/n;
  var y=log.reduce(function(a,x){return a+x.yd},0)/n;
  s.push("Usage: <b>"+fmt(t)+"</b> targets, <b>"+fmt(r)+
   "</b> catches and <b>"+fmt(y,0)+
   "</b> receiving yards per game.");
 }else if(pos==="RB"){
  var c=log.reduce(function(a,x){return a+x.ca},0)/n;
  var ry=log.reduce(function(a,x){return a+x.ry},0)/n;
  var cs=log.reduce(function(a,x){return a+x.cs},0)/n;
  var tg=log.reduce(function(a,x){return a+x.ta},0)/n;
  s.push("Usage: <b>"+fmt(c)+"</b> carries (<b>"+fmt(cs,0)+
   "%</b> of the backfield), <b>"+fmt(ry,0)+
   "</b> rushing yards and <b>"+fmt(tg)+
   "</b> targets per game.");
 }else if(pos==="K"){
  var fa=log.reduce(function(a,x){return a+x.fa},0);
  var fm=log.reduce(function(a,x){return a+x.fm},0);
  var k5=log.reduce(function(a,x){return a+x.k5},0);
  var xm=log.reduce(function(a,x){return a+x.xm},0);
  s.push("Kicking: <b>"+fm+"/"+fa+"</b> on field goals ("+
   (fa?Math.round(fm/fa*100):0)+"%), <b>"+k5+
   "</b> from 50+, <b>"+xm+"</b> extra points.");
  s.push("<b>Low confidence:</b> kicker scoring is close to "+
   "random week to week (r=0.04 measured over 10 seasons), "+
   "so treat the ranking order loosely.");
 }else if(pos==="QB"){
  var at=log.reduce(function(a,x){return a+x.at},0)/n;
  var py=log.reduce(function(a,x){return a+x.py},0)/n;
  var rr=log.reduce(function(a,x){return a+x.ry},0)/n;
  s.push("Usage: <b>"+fmt(at,0)+"</b> attempts, <b>"+
   fmt(py,0)+"</b> passing and <b>"+fmt(rr,0)+
   "</b> rushing yards per game.");
 }
 var sn=log.filter(function(x){return x.sn!=null});
 if(sn.length>=2){
  var last=sn[sn.length-1].sn,
      base=sn.reduce(function(a,x){return a+x.sn},0)/sn.length;
  if(last<base*0.7)
   s.push("<b>Snap share is falling</b> \u2014 "+last+
    "% last week against a "+Math.round(base)+"% baseline.");
  else if(last>base*1.25)
   s.push("<b>Snap share is climbing</b> \u2014 "+last+
    "% last week against a "+Math.round(base)+"% baseline.");
 }
 if(p.inj_wks)
  s.push("<b>Injury:</b> "+(p.inj||"")+
   (p.inj_body?" ("+p.inj_body+")":"")+" \u2014 "+
   p.inj_wks+(p.inj_why?", "+p.inj_why:"")+".");
 if(proj.length){
  var best=proj.slice().sort(function(a,b){return b.m-a.m})[0];
  var wst=proj.slice().sort(function(a,b){return a.m-b.m})[0];
  s.push("Best upcoming matchup is <b>week "+best.w+
   " vs "+best.o+"</b> ("+fmt(best.m)+
   "), toughest is <b>week "+wst.w+" vs "+wst.o+
   "</b> ("+fmt(wst.m)+").");
 }
 return s.join(" ");}

function tabGeneral(p){
 var log26=(p.log||[]).filter(function(x){return x.s===2026});
 var ppg=log26.length?log26.reduce(function(a,x){
  return a+x.p},0)/log26.length:0;
 var h='<div class="kfhero"><h1>'+
  p.n.split(" ")[0]+' <span>'+
  p.n.split(" ").slice(1).join(" ")+'</span></h1>';
 if(p.img)h+='<img src="'+p.img+'">';
 h+='</div><div class="kfstat">'+
  '<div><div class="lb">Rank</div><div class="vl">#'+
   (p.rk||"-")+'</div></div>'+
  '<div><div class="lb">Pos Rank</div><div class="vl">'+
   (p.pos||"")+(p.posrk||"-")+'</div></div>'+
  '<div><div class="lb">Proj PPG</div><div class="vl">'+
   fmt(p.ppg)+'</div></div>'+
  '<div><div class="lb">2026 PPG</div><div class="vl">'+
   fmt(ppg)+'</div></div>'+
  '<div><div class="lb">Games Left</div><div class="vl">'+
   (p.gleft!=null?p.gleft:"-")+'</div></div></div>';
 h+='<div class="kfcard"><h3>Summary</h3>'+
  '<div class="kfsum">'+summary(p)+'</div></div>';
 h+='<div class="kfcard"><h3>Profile</h3>'+
  '<span class="kfpill">Team <b>'+(p.tm||"-")+'</b></span>'+
  '<span class="kfpill">Bye <b>'+(p.bye||"-")+'</b></span>'+
  '<span class="kfpill">ADP <b>'+fmt(p.adp)+'</b></span>'+
  '<span class="kfpill">Trade value <b>'+
   (p.val!=null?p.val:"-")+'</b></span>'+
  '<span class="kfpill">Status <b>'+
   (p.inj||"Active")+'</b></span></div>';
 return h;}

function chart(p){
 var log=(p.log||[]).slice(-12);
 var pj=(p.proj||[]).filter(function(x){
  return x.o!=="BYE"}).slice(0,6);
 var all=log.map(function(x){return {v:x.p,l:x.w,f:0}})
  .concat(pj.map(function(x){
   return {v:x.out?0:x.m,l:x.w,f:1}}));
 if(!all.length)return "";
 var mx=Math.max.apply(null,all.map(function(x){return x.v})
  .concat([20]));
 var Wd=Math.max(620,all.length*44),Ht=200,pd=26;
 var bw=(Wd-pd*2)/all.length;
 var h='<svg viewBox="0 0 '+Wd+' '+(Ht+32)+
  '" style="width:100%;height:auto">';
 for(var g=0;g<=3;g++){
  var y=pd+(Ht-pd)*g/3;
  h+='<line x1="'+pd+'" y1="'+y+'" x2="'+(Wd-pd)+'" y2="'+y+
   '" stroke="#1d1d1d" stroke-dasharray="3 4"/>'+
   '<text x="2" y="'+(y+4)+'" fill="#555" font-size="10">'+
   Math.round(mx*(3-g)/3)+'</text>';}
 var sp=-1;
 for(var i=1;i<all.length;i++)
  if(all[i].f&&!all[i-1].f)sp=i;
 all.forEach(function(x,i){
  var hh=Math.max(2,(Ht-pd)*(x.v/mx));
  var xx=pd+i*bw+bw*0.22,ww=bw*0.56,yy=Ht-hh;
  var c=x.f?"#4da3ff":(x.v>=18?"#3ddc84":
   (x.v>=10?"#ffa63d":"#ff5d6c"));
  h+='<rect x="'+xx+'" y="'+yy+'" width="'+ww+'" height="'+
   hh+'" rx="3" fill="'+c+'"'+(x.f?' opacity=".5"':'')+'/>'+
   '<text x="'+(xx+ww/2)+'" y="'+(yy-5)+'" fill="'+c+
   '" font-size="10" font-weight="700" text-anchor="middle">'+
   x.v.toFixed(1)+'</text>'+
   '<text x="'+(xx+ww/2)+'" y="'+(Ht+14)+
   '" fill="#666" font-size="10" text-anchor="middle">'+
   x.l+'</text>';});
 if(sp>0){
  var sx=pd+sp*bw;
  h+='<line x1="'+sx+'" y1="8" x2="'+sx+'" y2="'+Ht+
   '" stroke="#555"/><text x="'+(sx+5)+'" y="18" '+
   'fill="#777" font-size="10">PROJECTED</text>';}
 return h+'</svg>';}

function tabPerf(p){
 var h='<div class="kfcard"><h3>Player Performance</h3>'+
  chart(p)+'</div>';
 h+='<div class="kfcard"><h3>Player Logs</h3>'+
  '<div style="overflow:auto"><table class="kft"><tr>'+
  '<th>Week</th><th>PPR</th><th>Snp%</th>';
 h+=(p.pos==="K")
  ? '<th>FG</th><th>Att</th><th>Long</th><th>50+</th>'+
    '<th>XP</th><th>XPA</th>'
  :(p.pos==="QB")
  ? '<th>Att</th><th>PYd</th><th>PTD</th><th>Int</th>'+
    '<th>Car</th><th>RYd</th><th>RTD</th>'
  : '<th>Car</th><th>RYd</th><th>Y/A</th><th>Car%</th>'+
    '<th>RTD</th><th>Tar</th><th>Rec</th><th>Yds</th>'+
    '<th>TD</th>';
 h+='</tr>';
 (p.log||[]).filter(function(x){return x.s===2026})
  .forEach(function(x){
   h+='<tr><td>'+x.w+'. '+(x.h?"":"@ ")+x.o+'</td>'+
    '<td class="'+col(x.p,10,18)+'">'+fmt(x.p)+'</td>'+
    '<td>'+(x.sn!=null?x.sn+"%":"-")+'</td>';
   h+=(p.pos==="K")
    ? '<td>'+x.fm+'</td><td>'+x.fa+'</td><td>'+
      (x.fl||'-')+'</td><td>'+x.k5+'</td><td>'+x.xm+
      '</td><td>'+x.xa+'</td>'
    :(p.pos==="QB")
    ? '<td>'+x.at+'</td><td>'+x.py+'</td><td>'+x.pt+
      '</td><td>'+x["in"]+'</td><td>'+x.ca+'</td><td>'+
      x.ry+'</td><td>'+x.rt+'</td>'
    : '<td>'+x.ca+'</td><td>'+x.ry+'</td><td>'+
      (x.ca?fmt(x.ry/x.ca,1):"-")+'</td><td>'+x.cs+
      '%</td><td>'+x.rt+'</td><td>'+x.ta+'</td><td>'+
      x.re+'</td><td>'+x.yd+'</td><td>'+x.td+'</td>';
   h+='</tr>';});
 (p.proj||[]).forEach(function(x){
  var cs=(p.pos==="K")?6:((p.pos==="QB")?7:9);
  if(x.o==="BYE"){
   h+='<tr class="kfproj"><td>'+x.w+'. BYE</td>'+
    '<td class="dim">-</td><td class="dim" colspan="'+
    (cs+1)+'"></td></tr>';return;}
  h+='<tr class="kfproj"><td>'+x.w+'. '+(x.h?"":"@ ")+x.o+
   '</td><td style="color:#4da3ff;font-weight:700">'+
   (x.out?"OUT":fmt(x.m))+'</td>'+
   '<td class="dim" colspan="'+(cs+1)+'">'+
   (x.out?"injured":"projected \u00b7 floor "+fmt(x.lo)+
    " \u00b7 ceiling "+fmt(x.hi))+'</td></tr>';});
 return h+'</table></div></div>';}

function tabCareer(p){
 var h='<div class="kfcard"><h3>Player Career</h3>'+
  '<div style="overflow:auto"><table class="kft"><tr>'+
  '<th>Season</th><th>Tm</th><th>GP</th><th>PPR</th>'+
  '<th>Snp%</th><th>Car</th><th>RuYd</th><th>Y/A</th>'+
  '<th>Tar</th><th>Rec</th><th>Yds</th><th>TD</th></tr>';
 (p.car||[]).slice().reverse().forEach(function(c){
  h+='<tr><td>'+c.s+'</td><td>'+c.tm+'</td><td>'+c.gp+
   '</td><td class="'+col(c.ppr,10,16)+'">'+fmt(c.ppr)+
   '</td><td>'+(c.sn!=null?c.sn+"%":"-")+'</td><td>'+
   fmt(c.ca)+'</td><td>'+fmt(c.ry,0)+'</td><td>'+
   fmt(c.ypc,2)+'</td><td>'+fmt(c.ta)+'</td><td>'+
   fmt(c.re)+'</td><td>'+fmt(c.yd,0)+'</td><td>'+
   fmt(c.td,0)+'</td></tr>';});
 return h+'</table></div></div>';}

function tabOut(p){
 var k=nm(p.n),a=(RH&&RH[k])||[];
 if(a.length<2)
  return '<div class="kfcard"><h3>Ranking History</h3>'+
   '<div class="kfsum">Tracking begins today \u2014 the '+
   'series fills in as rankings update each week.</div></div>';
 var Wd=760,Ht=210,pd=34;
 var vs=a.map(function(x){return x[1]});
 var mn=Math.min.apply(null,vs),mx=Math.max.apply(null,vs);
 if(mx===mn)mx=mn+1;
 var pt=a.map(function(x,i){
  return [pd+(Wd-pd*2)*i/(a.length-1),
          pd+(Ht-pd*2)*(x[1]-mn)/(mx-mn)];});
 var h='<div class="kfcard"><h3>Ranking History</h3>'+
  '<svg viewBox="0 0 '+Wd+' '+(Ht+16)+'" style="width:100%">'+
  '<polyline fill="none" stroke="#4da3ff" stroke-width="2" '+
  'points="'+pt.map(function(q){return q[0]+","+q[1]})
   .join(" ")+'"/>';
 var step=Math.max(1,Math.ceil(a.length/7));
 pt.forEach(function(q,i){
  h+='<circle cx="'+q[0]+'" cy="'+q[1]+'" r="4" fill="#fff"/>'+
   '<text x="'+q[0]+'" y="'+(q[1]-10)+'" fill="#4da3ff" '+
   'font-size="10" text-anchor="middle">'+a[i][1]+'</text>';
  if(i%step===0)
   h+='<text x="'+q[0]+'" y="'+(Ht+8)+'" fill="#666" '+
    'font-size="9" text-anchor="middle">'+
    a[i][0].slice(5)+'</text>';});
 return h+'</svg></div>';}

var TABS=[["general","General"],["perf","Performance"],
 ["career","Career"],["out","Outcomes"]];

function render(){
 var p=CUR,el=document.getElementById("kfc");
 if(!el){
  el=document.createElement("div");el.id="kfc";
  el.onclick=function(e){if(e.target===el)KFcard2.close()};
  document.body.appendChild(el);}
 var h='<div class="kfw"><div class="kfh">'+
  '<div class="kfchip">'+
  (p.img?'<img src="'+p.img+'">':'')+
  '<div><b>'+p.n+'</b><div style="margin-top:3px">'+
  '<span class="kfbadge b-'+p.pos+'">'+p.pos+'</span>'+
  '<span class="kftm">'+(p.tm||"")+'</span></div></div>'+
  '</div><button class="kfx" onclick="KFcard2.close()">'+
  '&times;</button></div><div class="kftabs">';
 TABS.forEach(function(t){
  h+='<button class="'+(TAB===t[0]?"on":"")+
   '" onclick="KFcard2.tab(\''+t[0]+'\')">'+t[1]+
   '</button>';});
 h+='</div><div class="kfbody">';
 h+=TAB==="general"?tabGeneral(p):
    TAB==="perf"?tabPerf(p):
    TAB==="career"?tabCareer(p):tabOut(p);
 el.innerHTML=h+'</div></div>';}

window.KFcard2.tab=function(t){TAB=t;render();};
document.addEventListener("keydown",function(e){
 if(e.key==="Escape")KFcard2.close();});
})();
