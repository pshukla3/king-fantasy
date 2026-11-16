p = "112_ui_v4.py"
s = open(p).read()

JS = """
window.openCard=function(id){
 if(!id)return;
 var o=document.getElementById("cardov");
 if(!o){
  o=document.createElement("div");
  o.id="cardov";
  o.innerHTML='<div id="cardbx">'
   +'<button id="cardx">close</button>'
   +'<iframe id="cardfr" src=""></iframe></div>';
  document.body.appendChild(o);
  o.addEventListener("click",function(ev){
   if(ev.target===o||ev.target.id==="cardx"){
    o.style.display="none";
    document.getElementById("cardfr").src="";}});}
 document.getElementById("cardfr").src=
  "player.html#id="+encodeURIComponent(id);
 o.style.display="flex";};
document.addEventListener("click",function(ev){
 var t=ev.target;
 while(t&&t.getAttribute){
  var v=t.getAttribute("data-pid");
  if(v){window.openCard(v);return;}
  t=t.parentNode;}});
"""

CSS = """#cardov{display:none;position:fixed;top:0;left:0;
right:0;bottom:0;background:#000000cc;z-index:100;
align-items:center;justify-content:center;padding:20px}
#cardbx{background:var(--bg);width:100%;max-width:1180px;
height:90vh;border:1px solid var(--line);
border-radius:14px;overflow:hidden;position:relative}
#cardfr{width:100%;height:100%;border:0}
#cardx{position:absolute;top:10px;right:12px;z-index:2;
background:var(--panel2);color:var(--text);
border:1px solid var(--line);border-radius:8px;
padding:6px 12px;cursor:pointer;font-size:13px}
td[data-pid]{cursor:pointer}
td[data-pid]:hover{color:var(--sky)}
"""

a1 = "*{box-sizing:border-box}"
assert a1 in s, "css anchor missing"
if "#cardov" not in s:
    s = s.replace(a1, CSS + a1, 1)
    print("overlay css added")

a2 = 'console.log("king fantasy ready")'
assert a2 in s, "console anchor missing"
if "window.openCard" not in s:
    s = s.replace(a2, JS + "\n" + a2, 1)
    print("openCard + delegated listener added")

old = "(x.st?' class=\"hurt\"':'')+'>'+E(x.nm)+"
new = ("(x.st?' class=\"hurt\"':'')"
       "+' data-pid=\"'+(x.id||'')+'\">'+E(x.nm)+")
n = s.count(old)
if n:
    s = s.replace(old, new)
    print("added data-pid to %d name cells" % n)
else:
    print("name cell anchor NOT FOUND - nothing wired")
open(p, "w").write(s)
