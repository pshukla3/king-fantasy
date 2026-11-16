import glob,re,sys
CSS=("body>div.wrap{max-width:none!important}"
     "body>.wrap{max-width:none!important}"
     ".kfw{max-width:none!important}"
     "#scores .wrap{max-width:none!important}")
M0="<!--KFLAY-->"; M1="<!--ENDKFLAY-->"
BLK=M0+'<style id="kflay">'+CSS+'</style>'+M1
DIV=re.compile(r'<div\b|</div>',re.I)

TBL=re.compile(r'<table\b|</table>',re.I)

def _baltbl(s,k):
    j=k+6; d=1
    while d>0:
        m=TBL.search(s,j)
        if not m: return -1
        if m.group(0).lower().startswith("</"): d-=1
        else: d+=1
        j=m.end()
    return j

def cut_standings(s):
    msg=[]
    h=re.search(r'<h3[^>]*class="hsec"[^>]*>\s*2026 Standings'
                r'\s*</h3>',s,re.I)
    if h:
        s=s[:h.start()]+s[h.end():]
        msg.append("heading")
    n=0
    while True:
        m=re.search(r'<table[^>]*class="[^"]*\bst\b[^"]*"[^>]*>',
                    s,re.I)
        if not m: break
        e=_baltbl(s,m.start())
        if e<0: msg.append("UNBALANCED table.st"); break
        s=s[:m.start()]+s[e:]
        n+=1
        if n>4: break
    if n: msg.append("%d table.st removed"%n)
    return s, (", ".join(msg) or "nothing found")

def _bal(s,k):
    j=k+4; d=1
    while d>0:
        m=DIV.search(s,j)
        if not m: return -1
        if m.group(0).lower().startswith("</"): d-=1
        else: d+=1
        j=m.end()
    return j

def _cuttag(s,rx,close):
    mm=re.search(rx,s,re.I)
    if not mm: return s,""
    k=s.lower().find(close,mm.end())
    if k<0: return s,""
    k+=len(close)
    return s[:mm.start()]+s[k:], s[mm.start():k]

def move_tpw(s):
    m=re.search(r'<div[^>]*class="[^"]*\btpw\b[^"]*"[^>]*>',s,re.I)
    if not m: return s,"tpw not found"
    e=_bal(s,m.start())
    if e<0: return s,"tpw unbalanced"
    tpw=s[m.start():e]; s=s[:m.start()]+s[e:]
    s,css=_cuttag(s,r'<style[^>]*id="tpwcss"[^>]*>',"</style>")
    s,js =_cuttag(s,r'<script[^>]*id="tpwjs"[^>]*>',"</script>")
    g=re.search(r'<div[^>]*class="[^"]*\bhgrid\b[^"]*"[^>]*>',
                s,re.I)
    if not g: return s,"hgrid not found"
    k=s.find("<div",g.end())
    if k<0: return s,"hgrid child missing"
    t=s.find(">",k)
    if t<0: return s,"bad child tag"
    t+=1
    s=s[:t]+css+tpw+js+s[t:]
    return s,"tpw moved into hgrid col 1 (%d bytes)"%len(tpw)

files=["vaporai.html"]+[f for f in sorted(glob.glob("site/*.html"))
                        if not f.endswith("index.html")]
for f in files:
    try: s=open(f,encoding="utf-8").read()
    except Exception: continue
    while M0 in s and M1 in s:
        a=s.index(M0); b=s.index(M1)+len(M1); s=s[:a]+s[b:]
    if "</head>" in s:
        s=s.replace("</head>",BLK+"</head>",1)
    if f=="vaporai.html":
        s,msg=cut_standings(s)
        print("  standings:",msg)
        s,msg2=move_tpw(s)
        print("  tpw:",msg2)
    open(f,"w",encoding="utf-8").write(s)
print("layout applied to %d files"%len(files))
s=open("vaporai.html",encoding="utf-8").read()
print("114 anchor intact:", "</script></body></html>" in s)
print("standings gone:", "2026 Standings" not in s)
