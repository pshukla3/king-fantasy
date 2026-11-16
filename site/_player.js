var D=__DATA__;
function q(n){var m=new RegExp('[?&]'+n+'=([^&]*)').exec(
location.search);return m?decodeURIComponent(m[1]):null;}
function e(s){return String(s==null?'':s).replace(/&/g,'&amp;')
.replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function n(v,d){if(v==null||v!==v)return '-';
return Number(v).toFixed(d===undefined?0:d);}
function avg(y,c){if(!c)return '-';return (y/c).toFixed(1);}
function statTable(p){
 var qb=p.ps=='QB',a=p.s25,b=p.p26;
 if(!a&&!b)return '<div class=miss>No history or projection.</div>';
 var h=qb?['YEAR','GM','CMP','ATT','YDS','TD','INT','CAR','RYDS','RTD']
  :['YEAR','GM','TAR','REC','YDS','AVG','TD','CAR','RYDS','RTD'];
 var s='<div class=card><table><tr>';
 h.forEach(function(x){s+='<th>'+x+'</th>';});
 s+='</tr>';
 function row(lbl,d,cls){
  if(!d)return '';
  var c='<tr class="'+cls+'"><td>'+lbl+'</td><td>'+n(d.gm)+'</td>';
  if(qb){c+='<td>'+n(d.cmp)+'</td><td>'+n(d.att)+'</td><td>'+n(d.pyd)
   +'</td><td>'+n(d.ptd)+'</td><td>'+n(d.int)+'</td>';}
  else{c+='<td>'+n(d.tar)+'</td><td>'+n(d.rec)+'</td><td>'+n(d.cyd)
   +'</td><td>'+avg(d.cyd,d.rec)+'</td><td>'+n(d.ctd)+'</td>';}
  return c+'<td>'+n(d.car)+'</td><td>'+n(d.ryd)+'</td><td>'
   +n(d.rtd)+'</td></tr>';}
 s+=row('2025 STATISTICS',a,'');
 s+=row('2026 PROJECTIONS',b,'proj');
 return s+'</table></div>';}
function gameLog(p){
 var s='<div class=card><table><tr><th>WK</th><th>OPP</th>'
  +'<th>PROJ</th><th>FPTS</th></tr>';
 p.wk.forEach(function(w){
  var bye=w.opp=='BYE';
  s+='<tr class="'+(bye?'byeR':'')+'"><td>'+w.w+'</td><td>'+e(w.opp)
   +'</td><td>'+(bye?'-':n(w.proj,2))+'</td><td>-</td></tr>';});
 return s+'</table></div>';}
function career(p){
 if(!p.career||!p.career.length)return '<div class=miss>'
  +'No prior NFL seasons.</div>';
 var qb=p.ps=='QB';
 var h=qb?['YR','TM','GM','PPR','CMP','ATT','YDS','TD','INT','CAR','RYDS','RTD']
  :['YR','TM','GM','PPR','TAR','REC','YDS','TD','CAR','RYDS','RTD'];
 var s='<div class=card><table><tr>';
 h.forEach(function(x){s+='<th>'+x+'</th>';});
 s+='</tr>';
 p.career.forEach(function(c){
  s+='<tr><td>'+c.yr+'</td><td>'+e(c.tm)+'</td><td>'+n(c.gm)
   +'</td><td>'+n(c.ppr,1)+'</td>';
  if(qb){s+='<td>'+n(c.cmp)+'</td><td>'+n(c.att)+'</td><td>'+n(c.pyd)
   +'</td><td>'+n(c.ptd)+'</td><td>'+n(c.int)+'</td>';}
  else{s+='<td>'+n(c.tar)+'</td><td>'+n(c.rec)+'</td><td>'+n(c.cyd)
   +'</td><td>'+n(c.ctd)+'</td>';}
  s+='<td>'+n(c.car)+'</td><td>'+n(c.ryd)+'</td><td>'+n(c.rtd)
   +'</td></tr>';});
 return s+'</table></div>';}
function bi(k,v){return '<div class=bi><div class=k>'+k+'</div>'
 +'<div class=v>'+(v==null||v===''?'-':e(v))+'</div></div>';}
function rk(v,k){return '<div class=rk><div class=v>'+v+'</div>'
 +'<div class=k>'+k+'</div></div>';}
function render(){
 var id=q('id'),p=D[id];
 if(!p){document.getElementById('root').innerHTML='<div class=wrap>'
  +'<h2>Player not found</h2><div class=miss>id: '+e(id)
  +'</div></div>';return;}
 var ps=p.ps=='DST'?'DEF':p.ps;
 var img=p.hs?'<img class=shot src="'+e(p.hs)+'">':'<div class=shot></div>';
 var h='<div class=hero><div class=hrow>'+img+'<div>'
  +'<h1 class=nm>'+e(p.nm)+'</h1><div class=sub>'
  +'<span class="pos '+ps+'">'+ps+'</span> &nbsp;'+e(p.tm)
  +(p.jer?' &nbsp;#'+e(p.jer):'')
  +(p.st?' &nbsp;<b style="color:#f4739a">'+e(p.st)+'</b>':'')
  +'</div><div class=bio>'+bi('AGE',p.age)+bi('HEIGHT',p.ht)
  +bi('WEIGHT',p.wt?p.wt+' lbs':null)+bi('EXP',p.exp)
  +bi('COLLEGE',p.col)+'</div><div class=rank>'
  +rk('#'+(p.prk==null?'-':p.prk),ps)
  +rk('#'+(p.rk==null?'-':p.rk),'OVERALL')
  +rk(n(p.ppg,2),'PROJ PPG')+rk(n(p.szn,1),'PROJ SEASON')
  +rk((p.vorp==null?'-':(p.vorp>0?'+':'')+n(p.vorp,2)),'VORP')
  +rk('WK '+(p.by||'-'),'BYE')+'</div></div></div></div>';
 h+='<div class=wrap><h2>Statistics &amp; Projections</h2>'
  +statTable(p)+'<div class=note>2025 is actual production from '
  +'nflverse play-by-play, verified against ESPN and NFL.com. '
  +'2026 is this model&#39;s projection over a full 17-game season.'
  +'</div><div class=two><div><h2>2026 Game Log</h2>'+gameLog(p)
  +'<div class=note>Weekly PROJ is the season rate per game with the '
  +'bye removed. No opponent adjustment: defense-vs-QB persists at '
  +'+0.25 year over year but vs-WR at -0.09, so a per-matchup curve '
  +'would be invented precision at the skill positions.</div></div>'
  +'<div><h2>Career</h2>'+career(p)+'</div></div></div>';
 document.getElementById('root').innerHTML=h;
 document.title=p.nm;}
function getId(){
 var h=location.hash||'';
 var m=/[#&]id=([^&]+)/.exec(h);
 if(m)return decodeURIComponent(m[1]);
 var s=location.search||'';
 m=/[?&]id=([^&]+)/.exec(s);
 return m?decodeURIComponent(m[1]):null;}
function index(filter){
 var k=Object.keys(D),f=(filter||'').toLowerCase();
 var L=k.map(function(i){return D[i];}).filter(function(p){
  return !f||p.nm.toLowerCase().indexOf(f)>=0
   ||(p.tm||'').toLowerCase().indexOf(f)>=0;});
 L.sort(function(a,b){return (a.rk||999)-(b.rk||999);});
 var s='<div class=card><table><tr><th>RK</th><th>PLAYER</th>'
  +'<th>POS</th><th>TM</th><th>PPG</th></tr>';
 L.slice(0,300).forEach(function(p){
  var ps=p.ps=='DST'?'DEF':p.ps;
  s+='<tr style="cursor:pointer" onclick="go(\''+p.id+'\')">'
   +'<td>'+(p.rk||'-')+'</td><td>'+e(p.nm)+'</td>'
   +'<td><span class="pos '+ps+'">'+ps+'</span></td>'
   +'<td>'+e(p.tm)+'</td><td>'+n(p.ppg,2)+'</td></tr>';});
 return s+'</table></div>';}
function go(id){location.hash='id='+id;render();}
function draw(){
 var f=document.getElementById('sq');
 document.getElementById('list').innerHTML=index(f?f.value:'');}
function render(){
 var id=getId(),p=id?D[id]:null;
 if(!p){
  document.getElementById('root').innerHTML='<div class=wrap>'
   +'<h2>Players</h2>'+(id?'<div class=miss>No card for id '
   +e(id)+'</div>':'')
   +'<input id=sq placeholder="Search player or team" '
   +'style="width:100%;max-width:420px;padding:11px 14px;'
   +'font-size:15px;background:#141926;border:1px solid #2f3648;'
   +'border-radius:10px;color:#e8ecf4;margin-bottom:14px">'
   +'<div id=list></div></div>';
  var f=document.getElementById('sq');
  f.addEventListener('input',draw);
  draw();return;}
 var ps=p.ps=='DST'?'DEF':p.ps;
 var img=p.hs?'<img class=shot src="'+e(p.hs)+'">':'<div class=shot></div>';
 var h='<div class=hero><div class=hrow>'+img+'<div>'
  +'<h1 class=nm>'+e(p.nm)+'</h1><div class=sub>'
  +'<span class="pos '+ps+'">'+ps+'</span> &nbsp;'+e(p.tm)
  +(p.jer?' &nbsp;#'+e(p.jer):'')
  +(p.st?' &nbsp;<b style="color:#f4739a">'+e(p.st)+'</b>':'')
  +' &nbsp;<a href="#" onclick="location.hash=\'\';render();'
  +'return false" style="color:#2dd4bf">all players</a>'
  +'</div><div class=bio>'+bi('AGE',p.age)+bi('HEIGHT',p.ht)
  +bi('WEIGHT',p.wt?p.wt+' lbs':null)+bi('EXP',p.exp)
  +bi('COLLEGE',p.col)+'</div><div class=rank>'
  +rk('#'+(p.prk==null?'-':p.prk),ps)
  +rk('#'+(p.rk==null?'-':p.rk),'OVERALL')
  +rk(n(p.ppg,2),'PROJ PPG')+rk(n(p.szn,1),'PROJ SEASON')
  +rk((p.vorp==null?'-':(p.vorp>0?'+':'')+n(p.vorp,2)),'VORP')
  +rk('WK '+(p.by||'-'),'BYE')+'</div></div></div></div>';
 h+='<div class=wrap><h2>Statistics &amp; Projections</h2>'
  +statTable(p)+'<div class=note>2025 is actual production from '
  +'nflverse play-by-play, verified against ESPN and NFL.com. '
  +'2026 is this model&#39;s projection over a full 17-game season.'
  +'</div><div class=two><div><h2>2026 Game Log</h2>'+gameLog(p)
  +'<div class=note>Weekly PROJ is the season rate per game with '
  +'the bye removed. No opponent adjustment: defense-vs-QB '
  +'persists at +0.25 year over year but vs-WR at -0.09, so a '
  +'per-matchup curve would be invented precision at the skill '
  +'positions.</div></div><div><h2>Career</h2>'+career(p)
  +'</div></div></div>';
 document.getElementById('root').innerHTML=h;
 document.title=p.nm;}
window.addEventListener('hashchange',render);
render();
