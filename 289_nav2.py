import json
import re

GROUPS = [
 {"k": "home", "ic": "\u2302", "lb": "Home",
  "it": [["Dashboard", "home"]]},
 {"k": "lg", "ic": "\u2691", "lb": "My League",
  "it": [["Matchup", "lgh_mu"], ["My Team", "lgh_tm"], ["Waivers", "lgh_wv"], ["League Games", "lgh_gm"], ["Standings", "lgh_st"], ["Scores", "scores"], ["Power & Odds", "lgodds"], ["Sync League", "lgsync"]]},
 {"k": "dr", "ic": "\u25c8", "lb": "Draft",
  "it": [["Mock Draft", "mock"], ["Model vs ADP", "dmodel"]]},
 {"k": "rk", "ic": "\u25a4", "lb": "Rankings",
  "it": [["Overall", "rank"], ["Tiers", "rtiers"], ["Points Leaders", "rpts"], ["Boom / Bust", "rboom"], ["Schedule", "rsos"]]},
 {"k": "ss", "ic": "\u2696", "lb": "Start / Sit",
  "it": [["Start / Sit", "tstart"]]},
 {"k": "tc", "ic": "\u21c4", "lb": "Trade Calculator",
  "it": [["Calculator", "trades"], ["Trade Finder", "tfind"]]},
 {"k": "rs", "ic": "\u25ce", "lb": "Research",
  "it": [["NFL Rosters", "rosters"], ["My Team", "calc"]]},
 {"k": "tl", "ic": "\u2605", "lb": "Tools",
  "it": [["Lineup Optimizer", "topt"], ["Accuracy Report", "acc"]]}
]
NEW = ["rpts", "lgodds", "lgpower", "dmodel", "rtiers", "rboom",
       "rsos", "tfind", "tstart", "topt", "acc",
       "tcalc"]

H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<style id="nav2css">.*?</style>', "", H,
           flags=re.S)
H = re.sub(r'<script id="nav2js">.*?</script>', "", H,
           flags=re.S)

m = re.search(r"<nav[^>]*>", H)
assert m, "no <nav>"
add = ""
for t in NEW:
    if 'data-t="%s"' % t not in H:
        add += '<button data-t="%s"></button>' % t
if add:
    H = H[:m.end()] + add + H[m.end():]
print("hidden nav buttons added: %d" % (add.count("<button")))

ms = re.search(r'<section[^>]*id="home"', H)
assert ms, "no home section"
secs = ""
for t in NEW:
    if 'id="%s"' % t not in H:
        secs += ('<section id="%s"><div class="soon">'
                 '<h3>%s</h3><p>Building this next.</p>'
                 '</div></section>' % (t, t))
if secs:
    H = H[:ms.start()] + secs + H[ms.start():]
print("placeholder sections added: %d"
      % secs.count("<section"))

CSS = '''<style id="nav2css">
nav{display:none!important}
#rail{position:fixed;left:0;top:0;bottom:0;width:92px;
background:#111827;border-right:1px solid var(--line);
display:flex;flex-direction:column;align-items:center;
gap:4px;padding:14px 6px;z-index:600;overflow-y:auto}
#rail .lg{width:44px;height:44px;border-radius:12px;
background:var(--grad);display:flex;align-items:center;
justify-content:center;margin-bottom:16px;flex:0 0 auto}
#rail .lg svg{width:26px;height:26px}
#rail button{display:flex;flex-direction:column;
align-items:center;gap:5px;width:100%;background:none;
border:0;color:var(--dm);padding:10px 2px;
border-radius:12px;cursor:pointer;font-size:10.5px;
font-weight:600;letter-spacing:.01em;
transition:background .15s,color .15s}
#rail button i{font-style:normal;font-size:19px;
width:38px;height:38px;border-radius:11px;
display:flex;align-items:center;justify-content:center;
background:#1f2937;transition:background .15s}
#rail button:hover{color:var(--tx)}
#rail button:hover i{background:#374151}
#rail button.on{color:#fff}
#rail button.on i{background:var(--grad);
box-shadow:0 4px 14px rgba(79,140,255,.35)}
#subbar{position:sticky;top:0;z-index:400;
display:flex;gap:4px;padding:12px 26px;
background:rgba(10,11,13,.93);
backdrop-filter:saturate(1.4) blur(8px);
border-bottom:1px solid var(--line);overflow-x:auto}
#subbar button{background:none;border:0;color:var(--dm);
padding:8px 15px;border-radius:9px;font-size:13px;
font-weight:600;cursor:pointer;white-space:nowrap;
transition:background .15s,color .15s}
#subbar button:hover{background:var(--pnl2);
color:var(--tx)}
#subbar button.on{background:var(--pnl2);color:#fff;
box-shadow:inset 0 -2px 0 var(--acc)}
body{padding-left:92px!important}
.soon{padding:60px 26px;color:var(--dm)}
.soon h3{color:var(--tx);font-size:20px;
text-transform:capitalize;margin:0 0 8px}
@media(max-width:760px){#rail{width:64px}
body{padding-left:64px!important}
#rail button{font-size:0;gap:0}}
</style>'''

JS = ('<script id="nav2js">(function(){var G='
      + json.dumps(GROUPS) + ';\n'
      'function mk(t,c){var e=document.createElement(t);'
      'if(c)e.className=c;return e;}\n'
      'var rail=mk("aside");rail.id="rail";\n'
      'var lg=mk("div","lg");lg.innerHTML=\'\';rail.appendChild(lg);\n'
      'var sub=mk("div");sub.id="subbar";\n'
      'function hit(t){var b=document.querySelector('
      '\'nav button[data-t="\'+t+\'"]\');if(b)b.click();}\n'
      'function drawSub(gi){sub.innerHTML="";'
      'G[gi].it.forEach(function(p,j){'
      'var b=mk("button");b.textContent=p[0];'
      'b.onclick=function(){'
      'Array.prototype.forEach.call(sub.children,'
      'function(x){x.className="";});b.className="on";'
      'hit(p[1]);};sub.appendChild(b);});'
      'if(sub.firstChild)sub.firstChild.click();'
      'sub.style.display=G[gi].it.length>1?"flex":"none";}\n'
      'G.forEach(function(g,i){var b=mk("button");'
      'b.innerHTML=\'<i>\'+g.ic+\'</i><span>\'+g.lb'
      '+\'</span>\';b.onclick=function(){'
      'Array.prototype.forEach.call(rail.children,'
      'function(x){if(x.tagName==="BUTTON")'
      'x.className="";});b.className="on";drawSub(i);};'
      'rail.appendChild(b);});\n'
      'document.body.insertBefore(rail,'
      'document.body.firstChild);\n'
      'var sb=document.querySelector(".scorebar");\n'
      'if(sb&&sb.parentNode){sb.parentNode.insertBefore('
      'sub,sb.nextSibling);}else{'
      'document.body.insertBefore(sub,rail.nextSibling);}\n'
      'var first=rail.querySelector("button");\n'
      'if(first)first.click();\n'
      'console.log("nav2 ready: "+G.length+" groups");'
      '})();</script>')

mb = re.search(r"<body[^>]*>", H)
assert mb, "no <body>"
H = H[:mb.end()] + CSS + H[mb.end():]
H = H.replace("</script></body></html>",
              "</script>" + JS + "</body></html>", 1)
assert H.count('id="nav2css"') == 1
assert H.count('id="nav2js"') == 1
assert "</script></body></html>" in H, "tail broken"
assert len(H) > n0 * 0.9
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
