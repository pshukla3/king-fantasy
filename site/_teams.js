var LG="1312181058833240064";
var P=__PROJ__;
var FLEX={RB:1,WR:1,TE:1};
function g(u){return fetch(u).then(function(r){
 return r.json();});}
function pj(id){return P[id]||null;}
function best(pool,slots){
 var used={},fill=[],i,j;
 for(i=0;i<slots.length;i++){
  var s=slots[i],ok,b=-1,bv=-1;
  ok=(s==="FLEX")?FLEX:null;
  for(j=0;j<pool.length;j++){
   if(used[j])continue;
   var q=pool[j];if(!q.d)continue;
   var m=(s==="FLEX")?!!ok[q.d.ps]:
    (q.d.ps===s||(s==="DEF"&&q.d.ps==="DST"));
   if(m&&q.d.ppg>bv){bv=q.d.ppg;b=j;}}
  if(b>=0){used[b]=1;fill.push(pool[b]);}
  else fill.push(null);}
 return fill;}
function sum(a){var t=0,i;
 for(i=0;i<a.length;i++)if(a[i]&&a[i].d)t+=a[i].d.ppg;
 return t;}
function row(sl,q,cls){
 if(!q)return '<tr><td class=sl>'+sl+
  '</td><td class=warn>empty</td><td class=r>--</td></tr>';
 var d=q.d;
 if(!d)return '<tr class="'+cls+'"><td class=sl>'+sl+
  '</td><td class=warn>'+q.id+' (not on board)'+
  '</td><td class=r>--</td></tr>';
 return '<tr class="'+cls+'"><td class=sl>'+sl+
  '</td><td><span class="pos '+d.ps+'">'+d.ps+
  '</span> '+d.nm+' <span style="color:#6e7783">'+d.tm+
  (d.by?' bye '+d.by:'')+'</span>'+
  (d.st?' <span class=warn>'+d.st+'</span>':'')+
  '</td><td class=r>'+d.ppg.toFixed(2)+'</td></tr>';}
function draw(L,R,U){
 var slots=L.roster_positions.filter(function(x){
  return x!=="BN"&&x!=="IR"&&x!=="TAXI";});
 var un={};U.forEach(function(u){un[u.user_id]=
  (u.metadata&&u.metadata.team_name)||u.display_name;});
 var h='';
 R.forEach(function(r){
  var st=(r.starters||[]).map(function(id){
   return {id:id,d:pj(id)};});
  var all=(r.players||[]).map(function(id){
   return {id:id,d:pj(id)};});
  var bn=all.filter(function(q){
   return (r.starters||[]).indexOf(q.id)<0;});
  var op=best(all,slots);
  var a=sum(st),b=sum(op);
  h+='<div class=tm><h2>'+(un[r.owner_id]||'Team '+
   r.roster_id)+'</h2><div class=ow>roster '+r.roster_id+
   ' &middot; '+all.length+' players</div>';
  h+='<div class=hd>Starting lineup</div><table>';
  st.forEach(function(q,i){h+=row(slots[i]||'?',q,'');});
  h+='</table>';
  h+='<div class=hd>Bench</div><table>';
  bn.forEach(function(q){h+=row('BN',q,'bn');});
  h+='</table>';
  h+='<div class=tot>started <b>'+a.toFixed(1)+
   '</b> ppg &middot; optimal <b>'+b.toFixed(1)+'</b>'+
   (b-a>0.05?' &middot; <span class=gain>+'+
    (b-a).toFixed(1)+' left on the bench</span>':
    ' &middot; lineup is optimal')+'</div></div>';});
 document.getElementById('t').innerHTML=h;
 document.getElementById('ts').textContent=
  new Date().toLocaleTimeString();}
function load(){
 Promise.all([g('https://api.sleeper.app/v1/league/'+LG),
  g('https://api.sleeper.app/v1/league/'+LG+'/rosters'),
  g('https://api.sleeper.app/v1/league/'+LG+'/users')])
 .then(function(x){draw(x[0],x[1],x[2]);})
 .catch(function(e){document.getElementById('t').innerHTML=
  '<div class=warn>could not reach Sleeper: '+e+'</div>';});}
load();setInterval(load,60000);
