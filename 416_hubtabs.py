import json, re

L = open("site/league.html").read()

# Derive tabs from league.html, don't hardcode them.
TABS = re.findall(
    r'<div class="stab[^"]*" data-s="([^"]+)">([^<]+)</div>', L)
assert len(TABS) >= 4, "found %d stabs: %r" % (len(TABS), TABS)
print("hub tabs found: " + ", ".join(
    "%s=%s" % (s, n) for s, n in TABS))

# --- 1. league.html honours ?tab=xx -------------------
MARK = "/*TABPARAM*/"
L = re.sub(r"<script>" + re.escape(MARK) + r".*?</script>",
           "", L, flags=re.S)
PJS = ("<script>" + MARK + "(function(){"
       "var m=location.search.match(/[?&]tab=([a-z]+)/);"
       "if(!m)return;var n=0;"
       "function go(){n++;"
       "var b=document.querySelector("
       "'.stab[data-s=\"'+m[1]+'\"]');"
       "if(b&&b.onclick){b.onclick();"
       "var t=document.querySelector('.tabs');"
       "if(t)t.style.display='none';return;}"
       "if(n<40)setTimeout(go,100);}"
       "setTimeout(go,60);})();</script>")
assert L.count("</body>") == 1, "league.html body anchor"
L = L.replace("</body>", PJS + "</body>", 1)
open("site/league.html", "w").write(L)
print("league.html: ?tab= support added")

# --- 2. lazy iframe loader ----------------------------
LZ = ('(function(){function fix(){'
      'var f=document.querySelectorAll("iframe[data-src]");'
      'Array.prototype.forEach.call(f,function(x){'
      'var s=x.parentNode;'
      'while(s&&s.tagName!=="SECTION"){s=s.parentNode;}'
      'if(s&&s.className==="on"&&!x.getAttribute("src")){'
      'x.setAttribute("src",x.getAttribute("data-src"));}'
      '});}'
      'document.addEventListener("click",function(){'
      'setTimeout(fix,40);},true);'
      'setInterval(fix,600);setTimeout(fix,200);})();')
open("site/_lazyframe.js", "w").write(LZ)
print("wrote site/_lazyframe.js")

# --- 3. sections + hidden nav buttons -----------------
H = open("vaporai.html").read()
n0 = len(H)
STY = ('width:100%;height:2200px;border:0;'
       'background:transparent')

# strip any previous run
H = re.sub(r'<section id="lgh_[^"]+">.*?</section>', "",
           H, flags=re.S)
H = re.sub(r'<button data-t="lgh_[^"]+"></button>', "", H)
TAG = '<script src="_lazyframe.js"></script>'
H = H.replace(TAG, "")

# make the original league iframe lazy too
H = H.replace('<iframe src="league.html" style',
              '<iframe data-src="league.html" style', 1)

secs, btns = "", ""
for s, n in TABS:
    secs += ('<section id="lgh_%s"><iframe data-src='
             '"league.html?tab=%s" style="%s"></iframe>'
             '</section>' % (s, s, STY))
    btns += '<button data-t="lgh_%s"></button>' % s

A = '<button data-ic="\u21c4" data-t="trades">Trades</button>'
assert H.count(A) == 1, "trades nav anchor"
H = H.replace(A, btns + A, 1)

B = '<section id="lgodds">'
assert H.count(B) == 1, "lgodds anchor"
H = H.replace(B, secs + B, 1)

C = "</script></body></html>"
assert H.count(C) == 1, "tail anchor"
H = H.replace(C, "</script>" + TAG + "</body></html>", 1)
assert H.count(C) == 1, "tail anchor destroyed"

nav = len(re.findall(r'<button[^>]*data-t=', H))
print("nav buttons: %d" % nav)
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d" % (n0, len(H)))

# --- 4. rewrite the rail group ------------------------
P = open("289_nav2.py").read()
items = [[n, "lgh_" + s] for s, n in TABS]
items += [["Scores", "scores"],
          ["Power & Odds", "lgodds"],
          ["Sync League", "lgsync"]]
pat = re.compile(
    r'(\{"k":\s*"lg",.*?"it":\s*)\[\[.*?\]\](\s*\})', re.S)
m = pat.search(P)
assert m, "could not find the lg group in 289_nav2.py"
P = P[:m.start()] + m.group(1) + json.dumps(items) \
    + m.group(2) + P[m.end():]
open("289_nav2.py", "w").write(P)
print("rail group -> " + " | ".join(i[0] for i in items))
