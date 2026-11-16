import json,sys
sys.path.insert(0,".")
from namekey import nk
import glob as _g, re as _re
def _latest():
    _w=[int(_re.search(r"wk(\d+)\.json",f).group(1))
        for f in _g.glob("ranks/wk*.json")]
    return str(max(_w)) if _w else "11"
A=[a for a in sys.argv[1:] if a.isdigit()]
W=A[0] if A else _latest()
WRITE="--write" in sys.argv
B="site/_board.json"
b=json.load(open(B))
rows=b["rows"] if isinstance(b,dict) and "rows" in b else b
RK=json.load(open("ranks/wk%s.json"%W))["rows"]

bypid={r["pid"]:r for r in rows if r.get("pid")}
bynm={}
for r in rows: bynm.setdefault(nk(r.get("n")),[]).append(r)
for r in rows: r.pop("_m",None)

miss=[];byname=0
for x in RK:
    r=bypid.get(x["pid"])
    if r is None:
        c=[q for q in bynm.get(nk(x["n"]),[])
           if q.get("pos")==x["pos"]] or bynm.get(nk(x["n"]),[])
        if c: r=c[0];byname+=1
    if r is None:
        miss.append((x["rank"],x["n"],x["pos"]));continue
    r["_m"]=x["rank"]

def dead(r):
    return (r.get("out_season") or (r.get("gleft") or 0)<=0
            or (r.get("live") or 0)<=0)

VF=("live","floor","ceil","base","vorp","uvorp","val","uval")
before={id(r):(r.get("rk"),r.get("live")) for r in rows}
frozen=[]
for p in ("QB","RB","WR","TE"):
    mine=sorted([r for r in rows if r.get("pos")==p
                 and r.get("_m")],key=lambda r:r["_m"])
    live=[r for r in mine if not dead(r)]
    for r in mine:
        if dead(r):
            frozen.append((r["_m"],r.get("n"),r.get("inj")))
            for f in VF:
                if f in r: r[f]=0.0
            r["ros"]=0.0; r["rosv"]=-1e9
    if not live: continue
    pool={f:sorted([(r.get(f) or 0.0) for r in live],
                   reverse=True) for f in VF}
    for i,r in enumerate(live):
        old=r.get("live") or 0.0
        for f in VF: r[f]=round(pool[f][i],2)
        new=r["live"]
        if old>0 and abs(new-old)>1e-9:
            k=new/old
            for w in (r.get("wk") or []):
                if w.get("o")=="BYE" or w.get("out"): continue
                if "m" in w: w["m"]=round(w["m"]*k,2)
        t=0.0
        for w in (r.get("wk") or []):
            if w.get("o")=="BYE" or w.get("out"): continue
            t+=w.get("m") or 0.0
        r["ros"]=round(t,1)
        r["rosv"]=round(r["vorp"]*(r.get("gleft") or 0),2)

rankd=sorted([r for r in rows if r.get("_m")],
             key=lambda r:r["_m"])
rid={id(r) for r in rankd}
ks=sorted([r for r in rows if id(r) not in rid
           and r.get("pos")=="K"],
          key=lambda r:-(r.get("live") or 0))
kid={id(r) for r in ks}
rest=sorted([r for r in rows if id(r) not in rid
             and id(r) not in kid],
            key=lambda r:(r.get("rk") or 9999))
pc={}
for i,r in enumerate(rankd+ks+rest,1):
    r["rk"]=i; q=r.get("pos") or "?"
    pc[q]=pc.get(q,0)+1; r["posrk"]=pc[q]
    r["tier"]=min(20,1+(pc[q]-1)//5)
order=rankd+ks+rest
for r in rows: r.pop("_m",None)

print("week %s | ranked %d | matched-by-name %d | "
      "absent %d | frozen %d"%(W,len(RK),byname,len(miss),len(frozen)))
print("kickers at rk %d-%d"%(len(rankd)+1,len(rankd)+len(ks)))
print("\n== ABSENT FROM BOARD ==")
for a in miss: print("  #%-4d %-24s %s"%a)
print("\n%-4s %-24s %-4s %7s %7s %6s"%(
  "new","player","pos","ppg","was","oldrk"))
for r in order[:40]:
    o=before[id(r)]
    print("%-4d %-24s %-4s %7.2f %7.2f %6s"%(
      r["rk"],(r.get("n") or "")[:24],r.get("pos"),
      r.get("live") or 0,(o[1] or 0),o[0]))
if WRITE:
    json.dump(b,open(B,"w"),separators=(",",":"))
    print("\nWROTE %s"%B)
else:
    print("\n(dry run -- add --write to apply)")
