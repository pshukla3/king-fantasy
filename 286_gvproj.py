import re

s = open("site/_game.js").read()
n0 = len(s)

def ctx(pat):
    m = re.search(pat, s)
    if m:
        return s[max(0, m.start() - 80):m.end() + 80]
    return "<no match>"

m = re.search(r"var SCH\s*=[^;]*;", s)
if not m:
    print("globals line not found. grep 'SCH':")
    for ln in s.split("\n"):
        if "SCH" in ln:
            print("   " + ln[:90])
    raise SystemExit(1)
print("globals: %s" % m.group(0))
if "PJ" not in m.group(0):
    s = s[:m.start()] + m.group(0).replace(
        "BUSY=false;", "PJ=null,BUSY=false;") + s[m.end():]
    print("  -> PJ added")

m = re.search(r'J\("_pmap\.json"\)[^\n]*\n[^\n]*'
              r'\.catch\(function\(\)\{\}\)', s)
if not m:
    print("boot fetch not found. grep '_pmap':")
    for ln in s.split("\n"):
        if "_pmap" in ln:
            print("   " + ln[:90])
    raise SystemExit(1)
if "_proj.json" not in s:
    s = (s[:m.end()] + ',\n  J("_proj.json").then('
         'function(d){PJ=d;}).catch(function(){})'
         + s[m.end():])
    print("boot: _proj.json fetch added")

m = re.search(r'\svar roster="";', s)
assert m, "roster start not found"
st = m.start()
m2 = re.search(r"show\('<div class=\"gvhd\"><b>'\+esc\(a\)"
               r"\+' @ '\+esc\(h\)\+'</b>'", s)
if not m2:
    print("render show() not found. grep 'gvhd':")
    for ln in s.split("\n"):
        if "gvhd" in ln:
            print("   " + ln[:90])
    raise SystemExit(1)
en = m2.start()
print("roster block: %d bytes -> replacing" % (en - st))

NEW = '''
 var roster="";
 if(PJ){var arr=[],id,q;
  for(id in PJ){q=PJ[id];
   if(!q||!q.tm)continue;
   var tm=nz(q.tm);
   if(tm===a||tm===h){arr.push(q);}}
  arr.sort(function(x,y){
   return (y.ppg||0)-(x.ppg||0);});
  arr=arr.slice(0,18);
  for(var ri=0;ri<arr.length;ri++){q=arr[ri];
   roster+='<div class="gvrp"><b>'+esc(q.nm)
   +'</b><span>'+esc(q.ps+" "+nz(q.tm))+' &middot; '
   +(q.ppg||0).toFixed(1)+'</span></div>';}}
 '''
s = s[:st] + NEW + s[en:]

s = s.replace("'<h4>Fantasy players</h4>'",
              "'<h4>Projected ppg</h4>'", 1)

open("site/_game.js", "w").write(s)
print("_game.js %d -> %d bytes" % (n0, len(s)))
print("PJ wired: %s | _proj fetch: %s"
      % ("PJ=null" in s, "_proj.json" in s))
