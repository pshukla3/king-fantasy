import sys
F="478_mock.py"
s=open(F,encoding="utf-8").read()

def repl(s,name,new):
    k=s.index("function "+name+"(")
    j=k;d=0;st=False
    while j<len(s):
        c=s[j]
        if c=='{': d+=1;st=True
        elif c=='}':
            d-=1
            if st and d==0: j+=1;break
        j+=1
    return s[:k]+new+s[j:]

GRID='''function drawGrid(){
 var h='<table class="g"><thead><tr><th class="rh"></th>';
 for(var t=1;t<=S.teams;t++)
  h+='<th'+(t==S.slot?' class="meh"':'')+'>'+
   (t==S.slot?"YOU":
    NAMES[(t-1)%NAMES.length].split(" ")[0])+'</th>';
 h+='</tr></thead><tbody>';
 for(var r=0;r<S.rounds;r++){
  var rv=revR(r);
  h+='<tr><th class="rh">'+(r+1)+'</th>';
  for(var c=0;c<S.teams;c++){
   var pir=rv?(S.teams-c):(c+1);
   var idx=r*S.teams+(rv?(S.teams-1-c):c);
   var t=ORD[idx],pk=S.picks[idx],cl="c";
   if(t==S.slot)cl+=" me";
   if(idx==S.pick)cl+=" on";
   if(pk){cl+=" f p-"+pk.pl.pos;if(pk.reach)cl+=" rch"}
   var lastp=rv?(c===0):(c===S.teams-1);
   var ar=lastp?"\\u2193":(rv?"\\u2190":"\\u2192");
   h+='<td class="'+cl+'"><em>'+(r+1)+'.'+pir+'</em>';
   if(pk)h+='<b>'+pk.pl.n+'</b><i>'+pk.pl.pos+
    ' \\u00b7 '+pk.pl.tm+'</i>';
   h+='<s class="ar">'+ar+'</s></td>';}
  h+='</tr>';}
 document.getElementById("grid").innerHTML=h+'</tbody></table>';}'''

TABS='''function drawTabs(){
 var P=["ALL","QB","RB","WR","TE","K","DST"],h="";
 var c=need(S.slot);
 var mine=S.picks.filter(function(p){return p.t==S.slot}).length;
 for(var i=0;i<P.length;i++){
  var lab=P[i],sub;
  if(lab=="ALL") sub=mine+"/"+S.rounds;
  else sub=(c[lab]||0)+"/"+(S.slots[lab]||0);
  h+='<button class="'+(S.filter==P[i]?"on":"")+
   '" onclick="S.filter=\\''+P[i]+
   '\\';drawTabs();renderList()">'+lab+
   '<small>'+sub+'</small></button>';}
 document.getElementById("tabs").innerHTML=h;}'''

LIST='''function renderList(){
 var q=(document.getElementById("q").value||"").toLowerCase();
 var me=(ORD[S.pick]==S.slot);
 function v(x){return (x==null||isNaN(x))?0:x;}
 var h='<table class="pl"><thead>'+
  '<tr class="grp"><th colspan="4"></th>'+
  '<th colspan="2">PROJ</th><th colspan="3">RUSHING</th>'+
  '<th colspan="3">RECEIVING</th>'+
  '<th colspan="3">PASSING</th><th></th></tr>'+
  '<tr class="hd2"><th>RK</th><th class="pn">PLAYER</th>'+
  '<th>ADP</th><th>BYE</th><th>PTS</th><th>AVG</th>'+
  '<th>ATT</th><th>YDS</th><th>TD</th>'+
  '<th>TAR</th><th>YDS</th><th>TD</th>'+
  '<th>ATT</th><th>YDS</th><th>TD</th><th></th></tr>'+
  '</thead><tbody>';
 var n=0;
 for(var i=0;i<S.pool.length&&n<90;i++){
  var p=S.pool[i];
  if(p.taken)continue;
  if(S.filter!="ALL"&&p.pos!=S.filter)continue;
  if(q&&p.n.toLowerCase().indexOf(q)<0)continue;
  n++;
  var t=(SL&&p.pid&&SL[p.pid])||{};
  h+='<tr><td class="rk">'+p.adp+'</td>'+
   '<td class="pn"><b>'+p.n+'</b><i><span class="pg '+
   p.pos+'">'+p.pos+'</span> '+p.tm+'</i></td>'+
   '<td>'+p.adp+'</td><td>'+(p.bye||"-")+'</td>'+
   '<td class="hi">'+(t.pts!=null?t.pts:p.ppg.toFixed(1))+
   '</td><td>'+(t.avg!=null?t.avg:p.ppg.toFixed(1))+'</td>'+
   '<td>'+v(t.car)+'</td><td>'+v(t.ryd)+'</td>'+
   '<td>'+v(t.rtd)+'</td><td>'+v(t.tar)+'</td>'+
   '<td>'+v(t.recyd)+'</td><td>'+v(t.rectd)+'</td>'+
   '<td>'+v(t.patt)+'</td><td>'+v(t.pyd)+'</td>'+
   '<td>'+v(t.ptd)+'</td>'+
   '<td><button onclick="userPick('+i+')"'+
   (me?"":" disabled")+'>Draft</button></td></tr>';}
 document.getElementById("plist").innerHTML=
  h+'</tbody></table>';}'''

POOL='''function loadPool(){
 return Promise.all([
  fetch("_board.json?v="+Date.now())
   .then(function(r){return r.json()}),
  fetch("_statline.json?v="+Date.now())
   .then(function(r){return r.json()})
   .catch(function(){return {}})
 ]).then(function(a){
  var b=a[0]; SL=a[1]||{};
  var rows=(b.rows||b).filter(function(r){
   return r.n&&r.pos&&(r.live!=null)});
  rows.forEach(function(r){r._adp=adpFor(r)});
  rows.sort(function(a,c){return a._adp-c._adp});
  S.pool=rows.map(function(r,i){
   return {n:r.n,pos:r.pos,tm:r.tm||"",bye:r.bye||"",
    img:r.img||"",ppg:r.live||0,adp:i+1,pid:r.pid||"",
    rk:r.rk||i+1,taken:0}});
  return S.pool});}'''

for nm,new in (("drawGrid",GRID),("drawTabs",TABS),
               ("renderList",LIST),("loadPool",POOL)):
    s=repl(s,nm,new)
if "var SL=null;" not in s:
    s=s.replace("function adpFor(p){","var SL=null;\nfunction adpFor(p){",1)
open(F,"w",encoding="utf-8").write(s)
import ast;ast.parse(s)
print("mock JS relayout written; SL present:", "var SL=null;" in s)
