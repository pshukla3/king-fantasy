import re

# ---------- 1. drop the Team Box Lines block ----------
h = open("113_home.py").read()
if "Team Box Lines" in h:
    i = h.find('BX = \'<h3 class="hsec"')
    j = h.find("\n\n", h.find("Team Box Lines"))
    if i > 0 and j > i:
        h = h[:i] + 'BX = ""  # Team Box Lines removed\n' + h[j:]
        # neutralise any later use of BX
        h = re.sub(r'\+\s*BX\b', '+ ""', h)
        open("113_home.py", "w").write(h)
        print("113_home.py: Team Box Lines removed")
    else:
        print("113_home.py: block boundaries not found")
else:
    print("113_home.py: already removed")

# ---------- 2. Top Performers section ----------
CSS = """
.tpw{margin:18px 0 26px;background:var(--pnl,#0A1E33);
 border:1px solid var(--line,#1C4265);border-radius:14px;
 padding:16px 18px}
.tpw .hd{display:flex;align-items:center;gap:12px;
 flex-wrap:wrap;margin-bottom:12px}
.tpw h3{font-size:17px;font-weight:800;margin:0}
.tpw select{background:var(--pnl2,#102C47);color:inherit;
 border:1px solid var(--line,#1C4265);border-radius:8px;
 padding:6px 10px;font-size:13px;font-weight:600}
.tpf{display:flex;gap:6px;flex-wrap:wrap;margin-left:auto}
.tpf button{background:var(--pnl2,#102C47);
 border:1px solid var(--line,#1C4265);color:var(--dim,#93AFC6);
 padding:5px 13px;border-radius:18px;cursor:pointer;
 font-size:12px;font-weight:700}
.tpf button.on{background:var(--acc,#0080C6);color:#fff;
 border-color:var(--acc,#0080C6)}
.tpl{display:grid;gap:7px}
.tpr{display:grid;grid-template-columns:30px 42px 1fr auto auto;
 gap:12px;align-items:center;padding:8px 10px;border-radius:10px;
 background:rgba(255,255,255,.03)}
.tpr:nth-child(-n+3){background:rgba(0,128,198,.12)}
.tpr .rk{font-weight:800;color:var(--dim,#93AFC6);
 text-align:center}
.tpr img{width:40px;height:40px;border-radius:50%;
 object-fit:cover;background:rgba(255,255,255,.06)}
.tpr .nm{font-weight:700;font-size:14px}
.tpr .mt{font-size:11.5px;color:var(--dim,#93AFC6);
 margin-top:1px}
.tpr .pts{font-size:19px;font-weight:800;text-align:right}
.tpr .vs{font-size:11.5px;text-align:right;min-width:74px}
.vs .up{color:#3ddc84}.vs .dn{color:#ff6b7a}
"""

JS = """
(function(){
 var POS='ALL',WK=null,D=null;
 function esc(s){return String(s==null?'':s)
  .replace(/&/g,'&amp;').replace(/</g,'&lt;');}
 function line(r){
  if(r.pos==='QB')return r.py+' yd, '+r.pt+' TD'
   +(r.ry?', '+r.ry+' ru':'');
  if(r.pos==='K')return r.fm+'/'+r.fa+' FG';
  var a=[];
  if(r.re)a.push(r.re+' rec, '+r.cy+' yd');
  if(r.ry)a.push(r.ry+' ru yd');
  var td=r.ct+r.rt;
  if(td)a.push(td+' TD');
  return a.join(' \\u00b7 ')||'\\u2013';
 }
 function draw(){
  var host=document.getElementById('tpwl');
  if(!host||!D)return;
  var rows=(D.by_week[String(WK)]||[])
   .filter(function(r){return POS==='ALL'||r.pos===POS})
   .slice(0,15);
  var h='';
  rows.forEach(function(r,i){
   var vs='';
   if(r.proj!=null){
    var d=r.p-r.proj;
    vs='<div class="vs"><span class="'+(d>=0?'up':'dn')+'">'
     +(d>=0?'+':'')+d.toFixed(1)+'</span><br>'
     +'<span style="opacity:.6">proj '+r.proj.toFixed(1)
     +'</span></div>';
   }else{vs='<div class="vs" style="opacity:.4">no proj</div>';}
   h+='<div class="tpr"><div class="rk">'+(i+1)+'</div>'
    +(r.img?'<img src="'+esc(r.img)+'">':'<div></div>')
    +'<div data-pid="'+esc(r.pid)+'"><div class="nm">'
    +esc(r.n)+'</div><div class="mt">'+r.pos+' \\u00b7 '
    +esc(r.tm)+' \\u00b7 '+line(r)+'</div></div>'
    +'<div class="pts">'+r.p.toFixed(1)+'</div>'+vs+'</div>';
  });
  host.innerHTML=h||'<div class="mt">No players.</div>';
 }
 fetch('_topwk.json?v='+Date.now())
  .then(function(r){return r.json()})
  .then(function(j){
   D=j;WK=j.last;
   var sel=document.getElementById('tpwk');
   if(sel){
    sel.innerHTML=j.weeks.slice().reverse().map(function(w){
     return '<option value="'+w+'">Week '+w+'</option>';}).join('');
    sel.value=String(WK);
    sel.onchange=function(){WK=+sel.value;draw();};
   }
   var f=document.getElementById('tpf');
   if(f){
    ['ALL','QB','RB','WR','TE','K'].forEach(function(p){
     var b=document.createElement('button');
     b.textContent=p;b.className=(p==='ALL'?'on':'');
     b.onclick=function(){
      POS=p;
      Array.prototype.forEach.call(f.children,function(c){
       c.className=(c===b?'on':'');});
      draw();};
     f.appendChild(b);});
   }
   draw();
  }).catch(function(e){
   var host=document.getElementById('tpwl');
   if(host)host.innerHTML='<div class="mt">unavailable: '+e+'</div>';
  });
})();
"""

BLOCK = ('<div class="tpw"><div class="hd">'
         '<h3>Top Fantasy Performers</h3>'
         '<select id="tpwk"></select>'
         '<div class="tpf" id="tpf"></div></div>'
         '<div class="tpl" id="tpwl"></div></div>'
         '<style id="tpwcss">' + CSS + '</style>'
         '<script id="tpwjs">' + JS + '</script>')

s = open("vaporai.html").read()
s = re.sub(r'<div class="tpw">.*?<script id="tpwjs">.*?</script>',
           "", s, flags=re.S)
# the tag is <section class="on" id="home"> -- attributes
# can precede the id, so do not anchor on position
m = re.search(r'(<section[^>]*\bid="home"[^>]*>)', s)
assert m, "home section not found"
s = s[:m.end()] + BLOCK + s[m.end():]
open("vaporai.html", "w").write(s)
print("home: Top Performers inserted (%d bytes)" % len(BLOCK))
