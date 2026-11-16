p = "112_ui_v4.py"
s = open(p).read()

CSS = """#cardov{display:none;position:fixed;top:0;left:0;
right:0;bottom:0;background:#000000cc;z-index:100;
align-items:center;justify-content:center;padding:20px}
#cardbx{background:var(--bg);width:100%;max-width:1180px;
height:90vh;border:1px solid var(--line);border-radius:14px;
overflow:hidden;position:relative}
#cardfr{width:100%;height:100%;border:0}
#cardx{position:absolute;top:10px;right:12px;z-index:2;
background:var(--panel2);color:var(--text);
border:1px solid var(--line);border-radius:8px;
padding:6px 12px;cursor:pointer;font-size:13px}
.pn{color:var(--sky);cursor:pointer;text-decoration:none;
border-bottom:1px dotted var(--line)}
.pn:hover{border-bottom-color:var(--sky)}
"""
anc = "*{box-sizing:border-box}"
assert anc in s, "css anchor missing"
if "#cardov" not in s:
    s = s.replace(anc, CSS + anc, 1)
    print("card overlay css added")

JS = """
window.openCard=function(id){
 if(!id)return;
 var o=document.getElementById('cardov');
 if(!o){
  o=document.createElement('div');o.id='cardov';
  o.innerHTML='<div id="cardbx">'
   +'<button id="cardx">close</button>'
   +'<iframe id="cardfr" src=""></iframe></div>';
  document.body.appendChild(o);
  o.addEventListener('click',function(ev){
   if(ev.target===o||ev.target.id==='cardx'){
    o.style.display='none';
    document.getElementById('cardfr').src='';}});
  document.addEventListener('keydown',function(ev){
   if(ev.key==='Escape')o.style.display='none';});}
 document.getElementById('cardfr').src=
  'player.html#id='+encodeURIComponent(id);
 o.style.display='flex';};
function pl(id,nm){
 if(!id)return E(nm);
 return '<a class="pn" href="#" onclick="openCard(\\''
  +id+'\\');return false">'+E(nm)+'</a>';}
"""
a2 = 'console.log("king fantasy ready")'
assert a2 in s, "console anchor missing"
if "window.openCard" not in s:
    s = s.replace(a2, JS + "\n" + a2, 1)
    print("openCard + pl helper added")

old = "'>'+E(x.nm)+"
n = s.count(old)
if n:
    s = s.replace(old, "'>'+pl(x.id,x.nm)+")
    print("made %d name cells clickable (board + my team)" % n)
else:
    print("name cells already clickable")
open(p, "w").write(s)

OC = """function oc(id){
 if(!id)return;
 try{if(window.top&&window.top.openCard){
  window.top.openCard(id);return;}}catch(e){}
 window.open('player.html#id='+encodeURIComponent(id),
  '_blank');}
"""
CL = (".pn{color:#56c2ff;cursor:pointer;"
      "border-bottom:1px dotted #2a2e36}\n")

q = "150_league_page.py"
t = open(q).read()
o1 = "<td><b>${p.name}</b></td>"
n1 = ("<td><b class=pn onclick=\"oc('${p.pid||''}')\">"
      "${p.name}</b></td>")
if o1 in t:
    t = t.replace(o1, n1, 1)
    print("150: roster names clickable")
o2 = "<b>${s.name}</b>"
n2 = "<b class=pn onclick=\"oc('${s.pid||''}')\">${s.name}</b>"
if o2 in t:
    t = t.replace(o2, n2, 1)
    print("150: matchup starters clickable")
if "function oc(" not in t:
    m = t.find("function render(")
    if m < 0:
        m = t.find("render();")
    t = t[:m] + OC + t[m:]
    print("150: oc() injected")
if ".pn{color" not in t:
    t = t.replace('CSS = """', 'CSS = """' + CL, 1)
open(q, "w").write(t)

r = "158_trade_page.py"
u = open(r).read()
o3 = "p.pos+'</span> '+p.name+'</span>"
n3 = ("p.pos+'</span> '+p.name"
      "+' <span class=pn onclick=\"event.stopPropagation();"
      "oc(\\''+(p.pid||'')+'\\')\">card</span>'+'</span>")
if o3 in u and "oc(" not in u:
    u = u.replace(o3, n3, 1)
    print("158: card link added to trade rows")
if "function oc(" not in u:
    m = u.find("function draw(")
    if m < 0:
        m = u.find("function plist(")
    u = u[:m] + OC + u[m:]
    print("158: oc() injected")
if ".pn{color" not in u:
    u = u.replace('CSS = """', 'CSS = """' + CL, 1)
open(r, "w").write(u)

import subprocess
for f in (p, q, r):
    c = subprocess.run(["python3", "-m", "py_compile", f],
                       capture_output=True, text=True)
    print("  %-22s %s" % (f, c.stderr.strip() or "compiles"))
