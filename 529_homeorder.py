import re,sys
F="vaporai.html"
s=open(F,encoding="utf-8").read()
DIV=re.compile(r'<div\b|</div>',re.I)

def divspan(s,m):
    j=m.end(); d=1
    while d>0:
        k=DIV.search(s,j)
        if not k: return None
        if k.group(0).lower().startswith('</'): d-=1
        else: d+=1
        j=k.end()
    return (m.start(),j)

def cutdiv(s,rx,lab):
    m=re.search(rx,s,re.I)
    if not m:
        print("  %-8s not present"%lab); return s,""
    sp=divspan(s,m)
    if not sp:
        print("  %-8s UNBALANCED"%lab); return s,""
    blk=s[sp[0]:sp[1]]
    print("  %-8s cut %d bytes"%(lab,len(blk)))
    return s[:sp[0]]+s[sp[1]:],blk

def cuttag(s,rx,close,lab):
    m=re.search(rx,s,re.I)
    if not m:
        print("  %-8s not present"%lab); return s,""
    e=s.lower().find(close,m.end())
    if e<0:
        print("  %-8s no close tag"%lab); return s,""
    e+=len(close); blk=s[m.start():e]
    print("  %-8s cut %d bytes"%(lab,len(blk)))
    return s[:m.start()]+s[e:],blk

print("removing stale sections:")
s,_=cutdiv(s,r'<div[^>]*id="kfsl"[^>]*>',"kfsl")
s,_=cutdiv(s,r'<div[^>]*id="kflb"[^>]*>',"kflb")
# --- kill leader scripts ---
for _f in ("_leaders.js","_season.js"):
    _rx=(r'<script[^>]*src="[^"]*'+re.escape(_f)+
         r'[^"]*"[^>]*>\s*</script>')
    _n=len(re.findall(_rx,s,re.I))
    s=re.sub(_rx,"",s,flags=re.I)
    print("  %-12s removed %d tag(s)"%(_f,_n))
print("lifting top performers:")
s,tpw=cutdiv(s,r'<div[^>]*class="[^"]*\btpw\b[^"]*"[^>]*>',"tpw")
s,css=cuttag(s,r'<style[^>]*id="tpwcss"[^>]*>',"</style>","tpwcss")
s,js =cuttag(s,r'<script[^>]*id="tpwjs"[^>]*>',"</script>","tpwjs")
if not tpw:
    sys.exit("tpw block missing -- nothing written")
m=re.search(r'<div[^>]*class="[^"]*\bhgrid\b[^"]*"[^>]*>',s,re.I)
if not m:
    sys.exit("hgrid anchor not found -- nothing written")
sp=divspan(s,m)
if not sp: sys.exit("hgrid unbalanced -- nothing written")
s=s[:sp[1]]+"\n"+css+"\n"+tpw+"\n"+js+"\n"+s[sp[1]:]
open(F,"w",encoding="utf-8").write(s)

pos=lambda t:s.find(t)
print("\nnew order inside #home:")
for lab,t in (("welc",'class="welc"'),("hero",'class="hero"'),
              ("hgrid",'class="hgrid"'),("tpw",'class="tpw"')):
    print("  %-6s @ %d"%(lab,pos(t)))
print("kfsl present:",'id="kfsl"' in s)
print("kflb present:",'id="kflb"' in s)
