import re

JS = r'''(function(){
var L=null;
function esc(x){return String(x==null?"":x)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;");}
function bar(p){
 var c=p>=70?"g":(p>=40?"a":"r");
 return '<span class="cel '+c+'">'+p.toFixed(1)
  +'%</span>';}
function odds(){
 var h='<h2>Playoff Odds</h2><p class="sub">'
  +L.sims.toLocaleString()+' simulations of the remaining '
  +'schedule through week '+L.week+'. Each team\'s weekly '
  +'score is drawn around its best legal lineup for that '
  +'week - bye players excluded - with a spread of '
  +L.sd+' points, and its true level re-drawn each season '
  +'to reflect projection error.</p>'
  +'<table class="btb"><thead><tr><th>#</th><th>Team</th>'
  +'<th class="n">W-L</th><th class="n">PF</th>'
  +'<th class="n">Proj W</th><th class="n">Avg seed</th>'
  +'<th class="n">Playoffs</th></tr></thead><tbody>';
 L.rows.forEach(function(r,i){
  h+='<tr class="brw"><td class="bk">'+(i+1)+'</td>'
   +'<td class="bnm"><span><b>'+esc(r.team)+'</b></span>'
   +'</td><td class="n">'+r.w+'-'+r.l+'</td>'
   +'<td class="n">'+r.pf.toFixed(1)+'</td>'
   +'<td class="n">'+r.projw.toFixed(1)+'</td>'
   +'<td class="n">'+r.seed.toFixed(1)+'</td>'
   +'<td class="n">'+bar(r.playoff)+'</td></tr>';});
 return h+'</tbody></table>';}
function power(){
 var z=L.rows.slice().sort(function(a,b){
  return b.power-a.power;});
 var mx=z[0].power;
 var h='<h2>Power Rankings</h2><p class="sub">Projected '
  +'points from each team\'s best legal lineup, using '
  +'injury-adjusted projections. This is roster strength, '
  +'deliberately independent of record - two weeks of '
  +'results say less than the roster does.</p>'
  +'<table class="btb"><thead><tr><th>#</th><th>Team</th>'
  +'<th class="n">Lineup</th><th class="n">W-L</th>'
  +'<th class="n">vs best</th></tr></thead><tbody>';
 z.forEach(function(r,i){
  var d=r.power-mx;
  h+='<tr class="brw"><td class="bk">'+(i+1)+'</td>'
   +'<td class="bnm"><span><b>'+esc(r.team)+'</b></span>'
   +'</td><td class="n"><b>'+r.power.toFixed(1)+'</b></td>'
   +'<td class="n">'+r.w+'-'+r.l+'</td>'
   +'<td class="n">'+(d?d.toFixed(1):"-")+'</td></tr>';});
 return h+'</tbody></table>';}
function draw(){
 if(!L)return;
 var a=document.getElementById("lgodds");
 if(a&&!a.querySelector(".kfodds")){
  var d1=document.createElement("div");
  d1.className="kfodds";a.insertBefore(d1,a.firstChild);}
 if(a)a.querySelector(".kfodds").innerHTML=odds();
 var b=document.getElementById("lgpower");
 if(b&&!b.querySelector(".kfpow")){
  var d2=document.createElement("div");
  d2.className="kfpow";b.insertBefore(d2,b.firstChild);}
 if(b)b.querySelector(".kfpow").innerHTML=power();}
fetch("_league.json").then(function(r){return r.json();})
 .then(function(d){L=d;draw();})
 .catch(function(e){console.log("league: "+e.message);});
})();'''
open("site/_lgpages.js", "w").write(JS)
print("wrote site/_lgpages.js (" + str(len(JS)) + " bytes)")

TAG = '<script src="_lgpages.js"></script>'
H = open("vaporai.html").read()
n0 = len(H)
H = H.replace(TAG, "")
assert H.count("</script></body></html>") == 1
H = H.replace("</script></body></html>",
              "</script>" + TAG + "</body></html>", 1)
assert H.count(TAG) == 1
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav " + str(nav)
open("vaporai.html", "w").write(H)
print("vaporai.html " + str(n0) + " -> " + str(len(H)))
