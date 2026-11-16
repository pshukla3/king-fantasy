import re

CSS = '''<style id="landcss">
#land{display:none;position:fixed;inset:0;z-index:9800;
background:radial-gradient(900px 520px at 20% -10%,
rgba(255,255,255,.07),transparent 60%),#0a0a0c;
align-items:center;justify-content:center;
padding:40px 22px;overflow-y:auto}
#land.on{display:flex}
.lwrap{max-width:760px;width:100%;text-align:center}
.llogo{width:66px;height:66px;border-radius:18px;
background:#fff;display:flex;align-items:center;
justify-content:center;margin:0 auto 26px}
.llogo svg{width:40px;height:40px}
.lwrap h1{font-size:46px;line-height:1.08;margin:0 0 16px;
color:#fff;letter-spacing:-.025em;font-weight:800}
.lwrap h1 em{font-style:normal;color:#8b8d94}
.lwrap p.lsub{font-size:17px;line-height:1.6;color:#8b8d94;
margin:0 auto 30px;max-width:520px}
.lbtns{display:flex;gap:12px;justify-content:center;
flex-wrap:wrap;margin-bottom:14px}
.lbtns button{border:0;border-radius:11px;padding:15px 30px;
font-size:15px;font-weight:700;cursor:pointer;color:#fff;
transition:transform .12s,filter .12s}
.lbtns button:hover{transform:translateY(-1px);
filter:brightness(1.1)}
.lskip{background:none;border:0;color:#8b8d94;
font-size:13px;cursor:pointer;text-decoration:underline;
padding:8px}
.lskip:hover{color:#f2f3f5}
.lfeat{display:grid;grid-template-columns:repeat(3,1fr);
gap:14px;margin-top:40px;text-align:left}
.lfeat div{background:rgba(19,19,22,.72);
border:1px solid rgba(255,255,255,.09);border-radius:13px;
padding:17px}
.lfeat h4{margin:0 0 6px;font-size:13px;color:#f2f3f5}
.lfeat p{margin:0;font-size:12px;line-height:1.55;
color:#8b8d94}
.lnote{margin-top:26px;font-size:11px;color:#5f6368}
@media(max-width:760px){
.lwrap h1{font-size:31px}
.lwrap p.lsub{font-size:15px}
.lfeat{grid-template-columns:1fr}
.lbtns button{width:100%}}
</style>'''

HTML = ('<div id="land"><div class="lwrap">'
        '<div class="llogo"><svg viewBox="0 0 34 34" '
        'fill="none"><ellipse cx="17.5" cy="20" rx="11" '
        'ry="7.4" transform="rotate(-32 17.5 20)" '
        'fill="#0a0a0c"/><path d="M12.6 24.4 22.4 15.6" '
        'stroke="#fff" stroke-width="1.5" '
        'stroke-linecap="round"/><circle cx="25.4" cy="9.6" '
        'r="3.1" fill="#0a0a0c"/><circle cx="29.4" cy="5.4" '
        'r="1.8" fill="#0a0a0c"/><circle cx="31.8" cy="2.4" '
        'r="1" fill="#0a0a0c"/></svg></div>'
        '<h1>Fantasy football,<br><em>with the math shown.</em>'
        '</h1>'
        '<p class="lsub">Projections, trade values and live '
        'win probability &mdash; built on eleven seasons of '
        'play-by-play, and published alongside their own '
        'measured error rates.</p>'
        '<div class="lbtns">'
        '<button class="btn-blue" id="lsign">'
        'Sign in with email</button>'
        '<button class="btn-green" id="lgo">'
        'Sync Your League</button>'
        '</div>'
        '<button class="lskip" id="lmock">'
        'or try a mock draft</button>'
        '<button class="lskip" id="lskip">or just look '
        'around</button>'
        '<div class="lfeat">'
        '<div><h4>Trade Finder</h4><p>Scores every swap twice '
        '&mdash; your gain by our model, theirs by market '
        'consensus. Only mutual wins surface.</p></div>'
        '<div><h4>Live Win Probability</h4><p>Beats ESPN '
        '0.4147 to 0.4383 log loss on 9,802 plays. Every '
        'play shows what it did to the odds.</p></div>'
        '<div><h4>Accuracy Report</h4><p>Our error rates, '
        'published in full &mdash; including the models we '
        'built, tested and threw away.</p></div>'
        '</div>'
        '<p class="lnote">No account needed. Your league '
        'stays on Sleeper.</p>'
        '</div></div><!--/land-->')

JS = ('<script id="landjs">(function(){'
      'function go(t){var b=document.querySelector('
      '\'nav button[data-t="\'+t+\'"]\');if(b)b.click();}'
      'function hide(){var e=document.getElementById("land");'
      'if(e)e.className="";'
      '}'
            'function wire(){'
      'var g=document.getElementById("lgo");'
      'if(g)g.onclick=function(){hide();go("league");};'
      'var m=document.getElementById("lmock");'
      'if(m)m.onclick=function(){hide();go("mock");};'
      'var s=document.getElementById("lskip");'
      'if(s)s.onclick=hide;'
      'var si=document.getElementById("lsign");'
      'if(si)si.onclick=function(){'
      'if(window.kfSignIn)window.kfSignIn();'
      'else alert("still loading, try again");};}'
      'function boot(){'
      'var e=document.getElementById("land");if(!e)return;'
      'var t=0;'
      'function chk(){'
      'if(window.__kfAuthed===true){e.className="";return;}'
      'if(window.__kfAuthed===false||t>16){'
      'e.className="on";wire();return;}'
      't++;setTimeout(chk,110);}'
      'chk();}'
'if(document.readyState==="loading"){'
      'document.addEventListener("DOMContentLoaded",boot);}'
      'else{boot();}})();</script>')

H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<style id="landcss">.*?</style>', "", H, flags=re.S)
H = re.sub(r'<div id="land">.*?<!--/land-->', "", H,
           count=1, flags=re.S)
H = re.sub(r'<script id="landjs">.*?</script>', "", H,
           flags=re.S)

mb = re.search(r"<body[^>]*>", H)
assert mb, "no body"
H = H[:mb.end()] + HTML + H[mb.end():]

bl = list(re.finditer(r'<style id="[\w-]+">', H))
last = max(bl, key=lambda x: x.start())
j = H.index("</style>", last.start()) + 8
H = H[:j] + CSS + H[j:]

H = H.replace("</script></body></html>",
              "</script>" + JS + "</body></html>", 1)

assert H.count('id="landcss"') == 1
assert H.count('id="landjs"') == 1
assert H.count('id="land"') == 1, "land div count"
assert H.count("<!--/land-->") == 1, "land marker"
assert "</script></body></html>" in H, "tail broken"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav buttons changed: %d" % nav
open("vaporai.html", "w").write(H)
print("landing page in | nav buttons %d" % nav)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
