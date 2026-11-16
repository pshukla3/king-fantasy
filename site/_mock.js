var POOL=__DATA__;
var CFG={nt:12,slot:6,rd:16,sc:"g",snake:true,
 adv:false,clock:0};
var SLOTS=["QB","RB","RB","WR","WR","TE","FLEX",
 "FLEX","K","DEF"];
var FLEX={RB:1,WR:1,TE:1};
var MAX={QB:2,RB:6,WR:7,TE:2,K:1,DEF:1};
var avail=[],ros=[],pk=0,log=[],tmr=null,left=0;
function q(p){return p.p==="DST"?"DEF":p.p;}
function pts(p){return p[CFG.sc];}
function ln(n){
 var a=String(n).replace(/[.,]/g,"").split(" ");
 while(a.length>1&&/^(jr|sr|ii|iii|iv|v)$/i
  .test(a[a.length-1]))a.pop();
 return a[a.length-1];}
function onclk(i){
 var r=Math.floor(i/CFG.nt),j=i%CFG.nt;
 return (CFG.snake&&r%2===1)?CFG.nt-1-j:j;}
function cnt(t,z){var c=0,i;
 for(i=0;i<ros[t].length;i++)
  if(q(ros[t][i])===z)c++;
 return c;}
function reset(){
 avail=POOL.slice(0);pk=0;log=[];ros=[];
 for(var i=0;i<CFG.nt;i++)ros.push([]);
 avail.sort(function(a,b){return a.a-b.a;});}
function ai(t){
 var rd=Math.floor(pk/CFG.nt)+1,c=[],i;
 for(i=0;i<avail.length;i++){
  var z=q(avail[i]);
  if((z==="K"||z==="DEF")&&rd<CFG.rd-3)continue;
  if(cnt(t,z)>=(MAX[z]||6))continue;
  c.push(avail[i]);
  if(c.length>=(CFG.adv?10:6))break;}
 if(!c.length)c=avail.slice(0,3);
 if(CFG.adv)c.sort(function(a,b){
  return (b.v-a.v);});
 var k=Math.min(CFG.adv?3:4,c.length);
 var j=Math.floor(Math.pow(Math.random(),
  CFG.adv?2.4:1.8)*k);
 return c[j];}
function take(t,p){
 var i=avail.indexOf(p);
 if(i<0)return;
 avail.splice(i,1);ros[t].push(p);
 log.push({t:t,p:p,pk:pk+1,
  rd:Math.floor(pk/CFG.nt)+1});
 pk++;}
function stop(){if(tmr){clearInterval(tmr);tmr=null;}}
function tick(){
 left--;
 var e=document.getElementById("ck");
 if(e)e.textContent=left>0?left+"s":"";
 if(left<=0){stop();
  var c=avail.slice(0).sort(function(a,b){
   return b.v-a.v;});
  if(c.length)pick(c[0].id);}}
function run(){
 stop();
 while(pk<CFG.nt*CFG.rd&&onclk(pk)!==CFG.slot-1)
  take(onclk(pk),ai(onclk(pk)));
 draw();
 if(CFG.clock>0&&pk<CFG.nt*CFG.rd){
  left=CFG.clock;tmr=setInterval(tick,1000);}}
function pick(id){
 if(onclk(pk)!==CFG.slot-1)return;
 var i,p=null;
 for(i=0;i<avail.length;i++)
  if(avail[i].id===id)p=avail[i];
 if(!p)return;
 take(CFG.slot-1,p);run();}
function best(pool){
 var used={},f=[],i,j;
 for(i=0;i<SLOTS.length;i++){
  var s=SLOTS[i],b=-1,bv=-1;
  for(j=0;j<pool.length;j++){
   if(used[j])continue;
   var z=q(pool[j]);
   var m=(s==="FLEX")?!!FLEX[z]:(z===s);
   if(m&&pts(pool[j])>bv){bv=pts(pool[j]);b=j;}}
  if(b>=0){used[b]=1;f.push(pool[b]);}
  else f.push(null);}
 return f;}
function tot(f){var t=0,i;
 for(i=0;i<f.length;i++)if(f[i])t+=pts(f[i]);
 return t;}
function E(s){return String(s).replace(/&/g,"&amp;")
 .replace(/</g,"&lt;");}
function chip(z){return '<span class="pos '+z+'">'+z
 +'</span>';}
function draw(){
 var i,j,h,done=pk>=CFG.nt*CFG.rd;
 var rd=Math.floor(pk/CFG.nt)+1;
 var cur=done?-1:onclk(pk);
 document.getElementById("st").innerHTML=done
  ?"<b>draft complete</b>"
  :"round <b>"+rd+"</b> &middot; pick <b>"+(pk+1)
   +"</b>/"+(CFG.nt*CFG.rd)+" &middot; "
   +(cur===CFG.slot-1
     ?"<b class=you>YOU ARE ON THE CLOCK</b>"
     :"team "+(cur+1))
   +" <span id=ck class=ck></span>";
 var grid={};
 for(i=0;i<log.length;i++)
  grid[(log[i].rd-1)+"-"+log[i].t]=log[i].p;
 h="<tr><th></th>";
 for(j=0;j<CFG.nt;j++)
  h+="<th"+(j===CFG.slot-1?" class=mine":"")+">"
   +(j===CFG.slot-1?"YOU":"T"+(j+1))+"</th>";
 h+="</tr>";
 for(i=0;i<CFG.rd;i++){
  h+="<tr><th class=rw>"+(i+1)+"</th>";
  for(j=0;j<CFG.nt;j++){
   var p=grid[i+"-"+j];
   var n=i*CFG.nt+(CFG.snake&&i%2===1
    ?CFG.nt-1-j:j);
   var on=(n===pk&&!done);
   h+="<td class='cl"+(j===CFG.slot-1?" mine":"")
    +(on?" on":"")+"'"+(on?" id=cur":"")+">"
    +(p?chip(q(p))+"<span class=nm>"+E(ln(p.n))
      +"</span><span class=tt>"+E(p.t)+"</span>"
      :"<span class=pn>"+(n+1)+"</span>")+"</td>";}
  h+="</tr>";}
 document.getElementById("bd").innerHTML=h;
 var ce=document.getElementById("cur");
 if(ce&&ce.scrollIntoView)
  ce.scrollIntoView({block:"center"});
 var f=best(ros[CFG.slot-1]);
 h="";
 for(i=0;i<f.length;i++)
  h+="<tr><td class=sl>"+SLOTS[i]+"</td><td>"
   +(f[i]?chip(q(f[i]))+" "+E(f[i].n)
     :"<i class=pn>empty</i>")+"</td><td class=r>"
   +(f[i]?pts(f[i]).toFixed(2):"--")+"</td></tr>";
 document.getElementById("me").innerHTML=h;
 document.getElementById("mt").textContent=
  tot(f).toFixed(1);
 var sc=[];
 for(i=0;i<CFG.nt;i++)
  sc.push({i:i,v:tot(best(ros[i]))});
 sc.sort(function(a,b){return b.v-a.v;});
 h="";
 for(i=0;i<sc.length;i++)
  h+="<tr><td>"+(i+1)+"</td><td>"
   +(sc[i].i===CFG.slot-1?"<b class=you>YOU</b>"
     :"team "+(sc[i].i+1))+"</td><td class=r>"
   +sc[i].v.toFixed(1)+"</td></tr>";
 document.getElementById("gr").innerHTML=h;
 var fl=document.getElementById("f").value;
 var s=document.getElementById("s").value
  .toLowerCase();
 var yours=cur===CFG.slot-1;
 h="";
 for(i=0;i<avail.length&&i<300;i++){
  var a=avail[i];
  if(fl&&q(a)!==fl)continue;
  if(s&&(a.n+" "+a.t).toLowerCase().indexOf(s)<0)
   continue;
  h+="<tr><td class=pn>"+a.r+"</td><td>"+chip(q(a))
   +" <b>"+E(a.n)+"</b> <span class=pn>"+E(a.t)
   +"</span></td><td class=r>"+a.b+"</td>"
   +"<td class=r>"+pts(a).toFixed(2)+"</td>"
   +"<td class=r>"+a.v.toFixed(2)+"</td>"
   +"<td class=r>"+a.a+"</td><td class=r>"
   +"<button "+(yours?"":"disabled ")
   +"onclick=\"pick('"+a.id+"')\">draft</button>"
   +"</td></tr>";}
 document.getElementById("av").innerHTML=h;}
function readCfg(){
 var g=function(x){
  return document.getElementById(x);};
 CFG.nt=parseInt(g("nt").value,10);
 CFG.snake=g("dt").value==="snake";
 CFG.adv=g("op").value==="adv";
 CFG.sc=g("sc").value;
 CFG.clock=parseInt(g("pc").value,10);
 var s=g("sl");
 s.innerHTML="";
 for(var i=1;i<=CFG.nt;i++)
  s.innerHTML+="<option>"+i+"</option>";
 if(CFG.slot>CFG.nt)CFG.slot=CFG.nt;
 s.value=CFG.slot;}
function start(){
 readCfg();
 CFG.slot=parseInt(
  document.getElementById("sl").value,10);
 reset();run();}
["nt","dt","op","sc","pc"].forEach(function(x){
 document.getElementById(x)
  .addEventListener("change",function(){
   readCfg();draw();});});
document.getElementById("s")
 .addEventListener("input",draw);
document.getElementById("f")
 .addEventListener("change",draw);
document.getElementById("go")
 .addEventListener("click",start);
document.getElementById("rnd")
 .addEventListener("click",function(){
  CFG.slot=1+Math.floor(Math.random()*CFG.nt);
  document.getElementById("sl").value=CFG.slot;});
readCfg();start();
