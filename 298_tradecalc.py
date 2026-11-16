import json
import re
import pandas as pd

B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()].copy()
VC = "value" if "value" in B.columns else "vorp"
B[VC] = pd.to_numeric(B[VC], errors="coerce").fillna(0)
lo = B[VC].min()
rng = (B[VC].max() - lo) or 1.0
P = []
for _, r in B.iterrows():
    v = int(round(10000.0 * (r[VC] - lo) / rng))
    P.append({"i": str(r.get("player_id", "")),
              "n": str(r["player_display_name"]),
              "p": str(r["position"]),
              "t": str(r.get("team", "")),
              "v": max(1, v),
              "r": int(r["rank"]) if r.get("rank") == r.get("rank")
                   else 999,
              "g": round(float(r["points"]), 1)
                   if r["points"] == r["points"] else 0.0})
P.sort(key=lambda x: -x["v"])
json.dump(P, open("site/_tc.json", "w"))
print("wrote site/_tc.json (%d players)" % len(P))
print("  top: %s" % [(x["n"], x["v"]) for x in P[:3]])

JS = r'''(function(){
var P=[],A=[],Bs=[];
function q(i){return document.getElementById(i);}
function esc(s){return String(s).replace(/[&<>"]/g,
 function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",
 '"':"&quot;"}[c];});}
function tot(L){var s=0;L.forEach(function(x){s+=x.v;});
 return s;}
function chips(L,side){
 return L.map(function(x,i){
  return '<div class="tcchip" data-s="'+side+'" data-i="'+i+
  '"><b>'+esc(x.n)+'</b><span>'+esc(x.p)+
  (x.t?" "+esc(x.t):"")+' &middot; '+x.g+' ppg</span>'+
  '<u>'+x.v.toLocaleString()+'</u><em>&times;</em></div>';
 }).join("")||'<div class="tcempty">no players yet</div>';}
function equal(){
 var d=tot(A)-tot(Bs),ab=Math.abs(d);
 if(ab<200||!P.length)return "";
 var side=d>0?"Team Two":"Team One";
 var c=P.filter(function(x){
  return Math.abs(x.v-ab)<ab*0.28;})
  .sort(function(a,b){
   return Math.abs(a.v-ab)-Math.abs(b.v-ab);})
  .slice(0,6);
 if(!c.length)return "";
 return '<div class="tceq"><h4>Players that would even '
 +'this out for '+side+'</h4>'
 +c.map(function(x){return '<div class="tcrow"><b>'
  +esc(x.n)+'</b><span>'+esc(x.p)+'</span><u>'
  +x.v.toLocaleString()+'</u></div>';}).join("")+'</div>';}
function draw(){
 var ta=tot(A),tb=tot(Bs),d=ta-tb;
 q("tcA").innerHTML=chips(A,"A");
 q("tcB").innerHTML=chips(Bs,"B");
 q("tcVA").textContent=ta.toLocaleString();
 q("tcVB").textContent=tb.toLocaleString();
 var v=q("tcV");
 if(!A.length||!Bs.length){
  v.className="tcv";
  v.textContent="Add players to both sides to get started";}
 else if(Math.abs(d)<Math.max(300,0.04*Math.max(ta,tb))){
  v.className="tcv even";
  v.textContent="Even trade \u2014 within noise";}
 else{
  v.className="tcv "+(d>0?"a":"b");
  v.textContent=(d>0?"Team One":"Team Two")
   +" wins by "+Math.abs(d).toLocaleString()
   +" ("+(100*Math.abs(d)/Math.max(ta,tb)).toFixed(0)+"%)";}
 q("tcEq").innerHTML=equal();}
function sug(inp,box,side){
 var s=inp.value.trim().toLowerCase();
 if(s.length<2){box.innerHTML="";return;}
 var r=P.filter(function(x){
  return x.n.toLowerCase().indexOf(s)>=0;}).slice(0,8);
 box.innerHTML=r.map(function(x){
  return '<div class="tcsug" data-n="'+esc(x.n)
  +'" data-side="'+side+'"><b>'+esc(x.n)+'</b><span>'
  +esc(x.p)+(x.t?" "+esc(x.t):"")+'</span><u>'
  +x.v.toLocaleString()+'</u></div>';}).join("");}
function boot(){
 var host=q("tcwrap");
 if(!host)return;
 fetch("_tc.json").then(function(r){return r.json();})
 .then(function(d){P=d;draw();});
 ["A","B"].forEach(function(s){
  var i=q("tcI"+s),b=q("tcS"+s);
  i.addEventListener("input",function(){sug(i,b,s);});
  i.addEventListener("blur",function(){
   setTimeout(function(){b.innerHTML="";},180);});});
 host.addEventListener("mousedown",function(e){
  var t=e.target.closest?e.target.closest(".tcsug"):null;
  if(t){var n=t.getAttribute("data-n"),
   s=t.getAttribute("data-side");
   var pl=P.filter(function(x){return x.n===n;})[0];
   if(pl){(s==="A"?A:Bs).push(pl);
    q("tcI"+s).value="";q("tcS"+s).innerHTML="";draw();}
   return;}
  var c=e.target.closest?e.target.closest(".tcchip"):null;
  if(c){var si=c.getAttribute("data-s"),
   ix=parseInt(c.getAttribute("data-i"),10);
   (si==="A"?A:Bs).splice(ix,1);draw();}});
 q("tcClr").addEventListener("click",function(){
  A=[];Bs=[];draw();});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",boot);}
else{boot();}})();'''
open("site/_tc.js", "w").write(JS)
print("wrote site/_tc.js (%d bytes)" % len(JS))

HTML = ('<section id="tcalc"><div class="pg" id="tcwrap">'
        '<h2>Trade Calculator</h2>'
        '<p class="sub">Values are our own projections '
        'converted to a 0&ndash;10,000 scale, not consensus '
        'ADP. Search a player, add him to either side, and '
        'the verdict updates live.</p>'
        '<div class="tcset">'
        '<label>League size<select id="tcT">'
        '<option>8</option><option selected>10'
        '</option><option>12</option>'
        '<option>14</option></select></label>'
        '<label>PPR<select id="tcP">'
        '<option value="1" selected>Full</option>'
        '<option value="0.5">Half</option>'
        '<option value="0">Standard</option>'
        '</select></label>'
        '<label>TE premium<select id="tcE">'
        '<option value="0" selected>Off</option>'
        '<option value="0.5">+0.5</option>'
        '<option value="1">+1.0</option>'
        '</select></label>'
        '<label class="tcsw"><input type="checkbox" '
        'id="tcF">Superflex</label>'
        '</div>'
        '<div class="tcgrid">'
        '<div class="tcside"><h3>You give</h3>'
        '<div class="tcin"><input id="tcIA" '
        'placeholder="Search for player" autocomplete="off">'
        '<div class="tcsugbox" id="tcSA"></div></div>'
        '<div id="tcA"></div>'
        '<div class="tctot">Total value'
        '<b id="tcVA">0</b></div></div>'
        '<div class="tcside"><h3>You get</h3>'
        '<div class="tcin"><input id="tcIB" '
        'placeholder="Search for player" autocomplete="off">'
        '<div class="tcsugbox" id="tcSB"></div></div>'
        '<div id="tcB"></div>'
        '<div class="tctot">Total value'
        '<b id="tcVB">0</b></div></div></div>'
        '<div class="tcv" id="tcV">Add players to both '
        'sides to get started</div>'
        '<button class="tcclr" id="tcClr">clear both '
        'sides</button>'
        '<div id="tcEq"></div>'
        '</div></section>')

H = open("vaporai.html").read()
n0 = len(H)
m = re.search(r'<section id="tcalc"[^>]*>', H)
assert m, "no tcalc section"
rx = re.compile(r"</?section\b", re.I)
d, k = 0, m.start()
while True:
    mm = rx.search(H, k)
    if H[mm.start():mm.start() + 2] == "</":
        d -= 1
        if d == 0:
            en = H.index(">", mm.start()) + 1
            break
    else:
        d += 1
    k = mm.end()
H = H[:m.start()] + HTML + H[en:]
TAG = '<script src="_tc.js"></script>'
H = H.replace(TAG, "")
mb = re.search(r"<body[^>]*>", H)
H = H[:mb.end()] + TAG + H[mb.end():]
assert H.count(TAG) == 1
assert "</script></body></html>" in H, "tail broken"
open("vaporai.html", "w").write(H)
print("trades section rebuilt | %d -> %d bytes" % (n0, len(H)))
