import re

JS = r"""
// Rebuild the top scorebar for the CURRENT week, in the
// browser. The cards baked in at build time freeze at
// whatever week the last deploy saw; this rolls over on
// its own every Tuesday with no deploy.
(function(){
var API="https://site.api.espn.com/apis/site/v2/sports/"
 +"football/nfl/scoreboard?seasontype=2&dates=2026&week=";
var E2N={"LAR":"LA","WSH":"WAS","JAC":"JAX","AZ":"ARI"};

function wk(){
 var A=Date.UTC(2026,8,8);
 var d=Math.floor((Date.now()-A)/604800000)+1;
 return Math.max(1,Math.min(18,d));
}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}

function card(g,week){
 var c=((g.competitions||[])[0])||{};
 var cs=c.competitors||[];
 var away=null,home=null;
 cs.forEach(function(x){
  if(x.homeAway==="away")away=x;else home=x;});
 if(!away||!home)return "";
 function ab(x){
  return ((x.team||{}).abbreviation)||"";}
 function sc(x){
  return (x.score==null)?"":String(x.score);}
 var st=((g.status||{}).type)||{};
 var meta;
 if(st.state==="post")meta="Week "+week+" \u00b7 FINAL";
 else if(st.state==="in")
  meta="Week "+week+" \u00b7 "+(st.shortDetail||"LIVE");
 else{
  var d=new Date(g.date);
  meta="Week "+week+" \u00b7 "+(isNaN(d)?"":
   d.toLocaleDateString(undefined,{weekday:"short"})
   +" "+d.toLocaleTimeString(undefined,{hour:"numeric",
   minute:"2-digit"}));
 }
 var av=Number(away.score||0),hv=Number(home.score||0);
 var done=(st.state==="post");
 function row(x,winner){
  var a=ab(x);
  return '<div class="sbrow"><img src="'
   +'https://a.espncdn.com/i/teamlogos/nfl/500/'
   +esc(a.toLowerCase())+'.png" alt="'+esc(a)+'">'
   +'<span class="ab">'+esc(a)+'</span>'
   +'<span class="vv'+(winner?" win":" ")+'">'
   +esc(sc(x)||"\u2013")+'</span></div>';
 }
 return '<div class="sbc'
  +(st.state==="in"?" livegame":"")+'">'
  +row(away,done&&av>hv)
  +row(home,done&&hv>av)
  +'<div class="sbmeta">'+meta+'</div></div>';
}

function build(){
 var box=document.querySelector(".sbin");
 if(!box){setTimeout(build,400);return;}
 var week=wk();
 fetch(API+week).then(function(r){return r.json();})
  .then(function(d){
   var ev=d.events||[];
   if(!ev.length)return;
   ev.sort(function(a,b){
    return new Date(a.date)-new Date(b.date);});
   var h="";
   ev.forEach(function(g){h+=card(g,week);});
   if(!h)return;
   box.innerHTML=h;
   console.log("scorebar rebuilt: week "+week+", "
    +ev.length+" games");
   // re-attach the game-detail click handlers, which
   // were bound to the cards we just replaced
   if(window.KFgameBoot){
    try{window.KFgameBoot();}catch(e){
     console.log("gamewire: "+e.message);}
   }
  }).catch(function(e){
   console.log("scorebar rebuild failed: "+e.message);});
}

if(document.readyState==="loading")
 document.addEventListener("DOMContentLoaded",function(){
  setTimeout(build,120);});
else setTimeout(build,120);
})();
"""
open("site/_sb.js", "w").write(JS)
print("wrote site/_sb.js (%d KB)" % (len(JS) // 1024))

# --- expose _game.js boot so we can re-wire clicks -----
G = open("site/_game.js").read()
if "KFgameBoot" not in G:
    i = G.rfind("})();")
    assert i > 0, "no IIFE tail in _game.js"
    G = G[:i] + "window.KFgameBoot=boot;\n" + G[i:]
    open("site/_game.js", "w").write(G)
    print("_game.js: boot exposed as window.KFgameBoot")
else:
    print("_game.js: KFgameBoot already exposed")

# --- load _sb.js after _live.js and _game.js ----------
H = open("vaporai.html").read()
TAG = '<script src="_sb.js"></script>'
H = H.replace(TAG, "")
C = "</script></body></html>"
assert H.count(C) == 1, "tail anchor"
H = H.replace(C, "</script>" + TAG + "</body></html>", 1)
assert H.count(C) == 1 and H.count(TAG) == 1
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav %d" % nav
open("vaporai.html", "w").write(H)
print("_sb.js wired | nav %d" % nav)
