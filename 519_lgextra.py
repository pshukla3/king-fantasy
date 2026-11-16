import json, re

CSS = """
.lx{margin-top:22px;background:var(--pnl,#0A1E33);
 border:1px solid var(--line,#1C4265);border-radius:14px;
 padding:18px}
.lx h3{font-size:16px;font-weight:800;margin:0 0 4px}
.lx .sub{color:var(--dim,#93AFC6);font-size:12.5px;
 margin-bottom:12px}
.lx table{width:100%;border-collapse:collapse;font-size:13px}
.lx th{font-size:10px;letter-spacing:.8px;font-weight:700;
 text-transform:uppercase;color:var(--dim,#93AFC6);
 padding:7px 6px;text-align:right;
 border-bottom:1px solid var(--line,#1C4265)}
.lx th.l,.lx td.l{text-align:left}
.lx td{padding:8px 6px;text-align:right;
 border-bottom:1px solid rgba(255,255,255,.05)}
.lx td.l b{font-weight:700}
.up{color:#3ddc84}.dn{color:#ff5d6c}
.sm{display:flex;gap:2px}
.sm i{flex:1;height:22px;border-radius:3px;
 font-style:normal;font-size:9px;line-height:22px;
 text-align:center;color:#fff}
.pbar{position:relative;background:rgba(255,255,255,.06);
 border-radius:5px;height:20px;overflow:hidden}
.pbar i{position:absolute;left:0;top:0;bottom:0;
 background:var(--acc,#0080C6);opacity:.55}
.pbar span{position:relative;font-size:11px;
 line-height:20px;padding-left:7px}
"""

JS = """
(function(){
 function pct(x){return (100*x).toFixed(1)+'%';}
 function shade(p){
  if(p<=0.005)return 'rgba(255,255,255,.04)';
  var a=Math.min(.92,.12+p*2.6);
  return 'rgba(0,128,198,'+a.toFixed(3)+')';}
 fetch('_lgsim.json?v='+Date.now())
  .then(function(r){return r.json()})
  .then(function(J){
   var R=J.rows,n=R.length,host=document.getElementById('lxw');
   if(!host)return;
   var h='';

   h+='<div class="lx"><h3>Luck &amp; schedule</h3>'
    +'<div class="sub">All-play is your record if you had '
    +'played every team every week. The gap is schedule '
    +'luck, and it does not carry forward.</div>'
    +'<table><tr><th class="l">Team</th><th>Rec</th>'
    +'<th>All-play</th><th>Luck</th><th>PF</th>'
    +'<th>Rest-of-year</th></tr>';
   R.slice().sort(function(a,b){return b.luck-a.luck})
    .forEach(function(t){
     h+='<tr><td class="l"><b>'+t.name+'</b></td>'
      +'<td>'+t.rec+'</td><td>'+(t.allplay||'-')+'</td>'
      +'<td class="'+(t.luck>0?'up':(t.luck<0?'dn':''))+'">'
      +(t.luck>0?'+':'')+t.luck.toFixed(1)+'</td>'
      +'<td>'+t.pf.toFixed(1)+'</td>'
      +'<td>'+t.ros.toFixed(0)+'</td></tr>';});
   h+='</table></div>';

   h+='<div class="lx"><h3>Where everyone finishes</h3>'
    +'<div class="sub">'+J.sims.toLocaleString()
    +' simulated seasons from today\\'s records and rosters. '
    +'Each cell is the chance of finishing in that spot.'
    +'</div><table><tr><th class="l">Team</th>'
    +'<th>Proj W</th>';
   for(var i=1;i<=n;i++)h+='<th>'+i+'</th>';
   h+='<th>Playoff</th><th>Title</th><th>Last</th></tr>';
   R.slice().sort(function(a,b){return b.proj_w-a.proj_w})
    .forEach(function(t){
     h+='<tr><td class="l"><b>'+t.name+'</b></td>'
      +'<td>'+t.proj_w.toFixed(1)+'</td>';
     t.seed_pct.forEach(function(p){
      h+='<td style="background:'+shade(p)+';font-size:11px">'
       +(p>=0.005?Math.round(100*p):'')+'</td>';});
     h+='<td>'+pct(t.po)+'</td><td>'+pct(t.title)+'</td>'
      +'<td class="'+(t.last>.2?'dn':'')+'">'+pct(t.last)
      +'</td></tr>';});
   h+='</table></div>';
   host.innerHTML=h;
  }).catch(function(e){
   var host=document.getElementById('lxw');
   if(host)host.innerHTML='<div class="lx sub">season '
    +'outlook unavailable: '+e+'</div>';});
})();
"""

p = "site/power.html"
s = open(p).read()
if "lxw" in s:
    s = re.sub(r'<div id="lxw">.*?</div>\s*<style id="lxcss">.*?</style>'
               r'\s*<script id="lxjs">.*?</script>', "", s, flags=re.S)
BLOCK = ('<div id="lxw"></div>'
         '<style id="lxcss">' + CSS + '</style>'
         '<script id="lxjs">' + JS + '</script>')
if "</body>" in s:
    s = s.replace("</body>", BLOCK + "</body>", 1)
else:
    s = s + BLOCK
open(p, "w").write(s)
print("power.html +%d bytes (luck + seed matrix)" % len(BLOCK))
