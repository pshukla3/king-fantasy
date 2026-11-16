import json, re, os
import pandas as pd
import fpts

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()]
POS = {}
for _, r in B.iterrows():
    k = norm(r["player_display_name"])
    if k:
        POS[k] = (str(r["position"]).strip()
                  if pd.notna(r.get("position")) else "")

CUR = fpts.nflweek()
TOT = {}
weeks_done = []
for w in range(1, CUR + 1):
    ev = fpts.week_events(w)
    fin = [e for e in ev if e["state"] == "post"]
    if not fin:
        continue
    weeks_done.append(w)
    for e in fin:
        s = fpts.get(fpts.BASE + "summary?event=" + e["id"])
        for nm, v in fpts.score_summary(s).items():
            k = norm(nm)
            r = TOT.setdefault(k, {"n": nm, "t": v["tm"],
                                   "p": 0.0, "g": 0})
            r["p"] += v["p"]
            r["g"] += 1
    print("  week %-2d %d final games" % (w, len(fin)))

rows = []
for k, r in TOT.items():
    if abs(r["p"]) < 0.05:
        continue
    ps = POS.get(k, "")
    ps = {"FB": "RB", "PK": "K"}.get(ps, ps)
    rows.append({"n": r["n"], "t": r["t"], "ps": ps,
                 "p": round(r["p"], 2), "g": r["g"],
                 "avg": round(r["p"] / max(1, r["g"]), 2)})
rows.sort(key=lambda x: -x["p"])

out = {"through": max(weeks_done) if weeks_done else 0,
       "weeks": weeks_done, "rows": rows[:200]}
json.dump(out, open("site/_season.json", "w"))
print("\nseason totals through week %d | %d players"
      % (out["through"], len(rows)))
for r in rows[:10]:
    print("  %-24s %-4s %-3s %6.1f  (%d g)"
          % (r["n"][:24], r["t"], r["ps"] or "?",
             r["p"], r["g"]))

JS = r'''(function(){
function esc(x){return String(x==null?"":x)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;");}
var POSN=["ALL","QB","RB","WR","TE","K"];
var D=null,SEL="ALL";
function tbl(){
 var z=(D.rows||[]).filter(function(x){
  return SEL==="ALL"||x.ps===SEL;}).slice(0,15);
 if(!z.length)return'<div class="lbcol">'
  +'<h5>No data yet</h5></div>';
 var o='<table class="sltab"><thead><tr><th></th>'
  +'<th>Player</th><th>Pos</th><th>G</th>'
  +'<th>Avg</th><th>Total</th></tr></thead><tbody>';
 z.forEach(function(x,i){
  o+='<tr><td class="sli">'+(i+1)+'</td>'
   +'<td class="sln">'+esc(x.n)+'</td>'
   +'<td class="slp">'+esc(x.ps||"-")+' '+esc(x.t)+'</td>'
   +'<td>'+x.g+'</td><td>'+x.avg.toFixed(1)+'</td>'
   +'<td class="slt">'+x.p.toFixed(1)+'</td></tr>';});
 return o+'</tbody></table>';}
function draw(){
 var h=document.getElementById("kfsl");
 if(!h){var hm=document.getElementById("home");
  if(!hm)return;
  h=document.createElement("div");h.id="kfsl";
  hm.appendChild(h);}
 if(!D||!D.rows||!D.rows.length){h.innerHTML="";return;}
 var b=POSN.map(function(p){
  return '<button class="slb'+(p===SEL?" on":"")
   +'" data-p="'+p+'">'+p+'</button>';}).join("");
 h.innerHTML='<h3 class="hsec">Season leaders '
  +'<em>through week '+D.through+'</em></h3>'
  +'<div class="slbar">'+b+'</div>'
  +'<div class="slwrap">'+tbl()+'</div>';
 Array.prototype.forEach.call(
  h.querySelectorAll(".slb"),function(x){
  x.addEventListener("click",function(){
   SEL=x.getAttribute("data-p");draw();});});}
function boot(){
 fetch("_season.json").then(function(r){
  return r.json();}).then(function(d){
  D=d;draw();}).catch(function(e){
  console.log("season leaders: "+e.message);});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",
  function(){setTimeout(boot,700);});}
else{setTimeout(boot,700);}})();'''
open("site/_season.js", "w").write(JS)
print("wrote site/_season.js (%d bytes)" % len(JS))

TAG = '<script src="_season.js"></script>'
H = open("vaporai.html").read()
n0 = len(H)
H = H.replace(TAG, "")
assert H.count("</script></body></html>") == 1
H = H.replace("</script></body></html>",
              "</script>" + TAG + "</body></html>", 1)
assert H.count(TAG) == 1
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav changed: %d" % nav
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d | nav %d" % (n0, len(H), nav))
