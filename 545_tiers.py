import json,re
MULT=2.2
CAP={"QB":40,"RB":70,"WR":90,"TE":45,"K":32,"DST":32}
B=json.load(open("site/_board.json"))
rows=B["rows"] if isinstance(B,dict) and "rows" in B else B

def tier_of(vals):
    if len(vals)<2: return [0]*len(vals)
    gaps=[vals[i]-vals[i+1] for i in range(len(vals)-1)]
    srt=sorted(g for g in gaps if g>=0)
    med=srt[len(srt)//2] if srt else 0.0
    if med<=0: med=0.01
    out=[];t=0
    for g in gaps:
        out.append(t)
        if g>MULT*med: t+=1
    out.append(t)
    return out

def esc(x):
    return (str(x).replace("&","&amp;").replace("<","&lt;")
            .replace(">","&gt;"))

html=[]
for pos in ("QB","RB","WR","TE","K","DST"):
    ps=[r for r in rows if (r.get("pos")==pos or (pos=="DST" and r.get("pos")=="DEF"))
        and (r.get("live") or 0)>0]
    ps.sort(key=lambda r:-(r.get("live") or 0))
    ps=ps[:CAP.get(pos,60)]
    if not ps: continue
    vals=[round(float(r.get("live") or 0),2) for r in ps]
    ts=tier_of(vals)
    groups=[]
    for r,v,t in zip(ps,vals,ts):
        if not groups or groups[-1][0]!=t:
            groups.append([t,[],v,v])
        groups[-1][1].append(r.get("n"))
        groups[-1][2]=min(groups[-1][2],v)
        groups[-1][3]=max(groups[-1][3],v)
    h=['<h3>%s &mdash; %d tiers</h3><table class="tf">'
       '<tr><th>Tier</th><th>Players</th><th>ppg</th></tr>'
       %(pos,len(groups))]
    for i,(t,names,lo,hi) in enumerate(groups,1):
        h.append('<tr><td class="tg">T%d</td><td>%s</td>'
                 '<td>%.1f&ndash;%.1f</td></tr>'
                 %(i," &middot; ".join(esc(n) for n in names),lo,hi))
    h.append('</table>')
    html.append("".join(h))
NEW="".join(html)

F="vaporai.html"
s=open(F,encoding="utf-8").read()
pat=re.compile(r'<h3>[^<]*tiers</h3>\s*<table class="tf">[\s\S]*?</table>')
ms=list(pat.finditer(s))
if not ms:
    raise SystemExit("no tier blocks found in %s"%F)
a=ms[0].start(); b=ms[-1].end()
old=s[a:b]
s=s[:a]+NEW+s[b:]
open(F,"w",encoding="utf-8").write(s)
print("replaced %d tier blocks (%d -> %d bytes)"%(
    len(ms),len(old),len(NEW)))
for pos in ("QB","RB","WR","TE","K","DST"):
    m=re.search(r'<h3>%s &mdash; (\d+) tiers</h3>'%pos,NEW)
    print("  %-3s %s tiers"%(pos,m.group(1) if m else "-"))
