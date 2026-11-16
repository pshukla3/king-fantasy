import re

JS = r'''(function(){
function boot(){
 var sb=document.querySelector(".scorebar");
 if(!sb){setTimeout(boot,250);return;}
 if(document.getElementById("kbrand"))return;
 var d=document.createElement("div");
 d.id="kbrand";
 d.innerHTML='<span class="kbtx"><b>KING</b><i>Fantasy</i></span>';
 sb.insertBefore(d,sb.firstChild);
 d.onclick=function(){
  var b=document.querySelector('nav button[data-t="home"]');
  if(b)b.click();};}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",boot);}
else{setTimeout(boot,200);}})();'''
open("site/_brand.js", "w").write(JS)
print("wrote site/_brand.js (%d bytes)" % len(JS))

CSS = '''<style id="brandcss">
.scorebar{display:flex!important;align-items:stretch}
.scorebar .sbin{flex:1 1 auto;min-width:0}
#kbrand{flex:0 0 auto;display:flex;align-items:center;
gap:11px;padding:0 20px;cursor:pointer;
border-right:1px solid rgba(165,172,175,.2);
transition:background .15s}
#kbrand:hover{background:rgba(105,190,40,.1)}
.kbmark{width:40px;height:40px;border-radius:12px;
background:#10b981;display:flex;align-items:center;
justify-content:center;flex:0 0 auto;
box-shadow:0 4px 14px rgba(105,190,40,.4)}
.kbmark svg{width:25px;height:25px}
.kbtx{display:flex;flex-direction:column;line-height:1.1}
.kbtx b{font-size:16px;font-weight:800;color:#fff;
letter-spacing:.04em}
.kbtx i{font-style:normal;font-size:12px;color:#10b981;
font-weight:600;letter-spacing:.02em}
@media(max-width:900px){
#kbrand{padding:0 12px;gap:8px}
.kbmark{width:32px;height:32px;border-radius:10px}
.kbmark svg{width:20px;height:20px}
.kbtx b{font-size:13px}
.kbtx i{font-size:10px}}
@media(max-width:520px){.kbtx{display:none}}
</style>'''

TAG = '<script src="_brand.js"></script>'
H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<style id="brandcss">.*?</style>', "", H, flags=re.S)
H = H.replace(TAG, "")
bl = list(re.finditer(r'<style id="[\w-]+">', H))
last = max(bl, key=lambda x: x.start())
j = H.index("</style>", last.start()) + 8
H = H[:j] + CSS + H[j:]
H = H.replace("</script></body></html>",
              "</script>" + TAG + "</body></html>", 1)
assert H.count('id="brandcss"') == 1
assert H.count(TAG) == 1
assert "</script></body></html>" in H, "tail broken"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav changed: %d" % nav
open("vaporai.html", "w").write(H)
print("brand block in | nav %d | %d -> %d bytes"
      % (nav, n0, len(H)))
