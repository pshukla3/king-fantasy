import json,sys
sys.path.insert(0,".")
from namekey import nk
import nflreadpy as nfl
import glob as _g, re as _re
def _latest():
    _w=[int(_re.search(r"wk(\d+)\.json",f).group(1))
        for f in _g.glob("ranks/wk*.json")]
    return str(max(_w)) if _w else "11"
A=[a for a in sys.argv[1:] if a.isdigit()]
W=A[0] if A else _latest()
WRITE="--write" in sys.argv
b=json.load(open("site/_board.json"))
rows=b["rows"] if isinstance(b,dict) and "rows" in b else b
RK=json.load(open("ranks/wk%s.json"%W))["rows"]
PR={};PN={}
for x in json.load(open("site/_prod.json"))["rows"]:
    PR[x["pid"]]=x; PN.setdefault(nk(x["n"]),x)
bypid={r["pid"]:r for r in rows if r.get("pid")}
bynm={}
for r in rows: bynm.setdefault(nk(r.get("n")),[]).append(r)
CUR=None
for r in rows:
    w=r.get("wk") or []
    if w and w[0].get("w"): CUR=w[0]["w"];break
CUR=CUR or int(W); LAST=18
LONG={"SFO":"SF","GBP":"GB","NEP":"NE","NOS":"NO","TAM":"TB",
 "KCC":"KC","LVR":"LV","JAC":"JAX","ARZ":"ARI","BLT":"BAL",
 "CLV":"CLE","HST":"HOU","LAR":"LA","SD":"LAC","OAK":"LV"}
SC={}
for g in nfl.load_schedules(seasons=[2026]).iter_rows(named=True):
    w=g.get("week");h=g.get("home_team");a=g.get("away_team")
    if not w or not h or not a: continue
    SC.setdefault(h,{})[w]=(a,1); SC.setdefault(a,{})[w]=(h,0)
def team(t):
    t=(t or "").upper(); t=LONG.get(t,t)
    return t if t in SC else None
REP={};MX={}
for p in ("QB","RB","WR","TE"):
    d=sorted((r.get("live") or 0)-(r.get("vorp") or 0)
             for r in rows if r.get("pos")==p
             and (r.get("live") or 0)>0
             and r.get("vorp") is not None)
    REP[p]=d[len(d)//2] if d else 0.0
    MX[p]=max([r.get("vorp") or 0 for r in rows
               if r.get("pos")==p] or [1]) or 1

cand=[]
for x in RK:
    r=bypid.get(x["pid"])
    if r is None:
        c=[q for q in bynm.get(nk(x["n"]),[])
           if q.get("pos")==x["pos"]] or bynm.get(nk(x["n"]),[])
        r=c[0] if c else None
    if r is None: continue
    if (r.get("live") or 0)>0 and (r.get("gleft") or 0)>0: continue
    p=PR.get(x["pid"]) or PN.get(nk(x["n"]))
    if not p or (p.get("gp") or 0)<1: continue
    cand.append((x["rank"],x["n"],r,p))

print("current week %d | candidates %d\n"%(CUR,len(cand)))
print("%-5s %-22s %-13s %-4s %3s %6s %5s %s"%(
  "rank","player","status","tm","g","ppg","lastwk","action"))
done=0
for rk,n,r,p in sorted(cand,key=lambda z:z[0]):
    lw=int(p.get("lastwk") or 0)
    tm=team(p.get("tm")) or team(r.get("tm"))
    go = (lw>=CUR-1) and bool(tm)
    print("%-5d %-22s %-13s %-4s %3d %6.2f %5d %s"%(
      rk,n[:22],str(r.get("inj"))[:13],str(tm),p["gp"],
      p["ppg"],lw,"UNFREEZE" if go else "keep frozen"))
    if not go: continue
    done+=1
    ppg=float(p["ppg"]);pos=r.get("pos");bye=None;wk=[];gl=0
    for w in range(1,LAST+1):
        if w not in SC.get(tm,{}): bye=w
    for w in range(CUR,LAST+1):
        g=SC.get(tm,{}).get(w)
        if not g: wk.append({"w":w,"o":"BYE","m":0});continue
        wk.append({"w":w,"o":g[0],"h":g[1],"out":0,
          "m":round(ppg,2),"sd":round(ppg*0.35,2),
          "lo":round(ppg*0.55,1),"hi":round(ppg*1.65,1)})
        gl+=1
    vorp=round(ppg-REP.get(pos,0.0),2)
    val=max(1,min(100,int(round(100*vorp/MX.get(pos,1)))))
    r.update({"tm":tm,"logo":tm.lower(),"bye":bye,"wk":wk,
      "gleft":gl,"miss":0,"inj":"Active",
      "live":round(ppg,2),"base":round(ppg,2),
      "floor":round(ppg*0.55,2),"ceil":round(ppg*1.65,2),
      "vorp":vorp,"uvorp":vorp,"val":val,"uval":val,
      "ros":round(ppg*gl,1),"rosv":round(vorp*gl,2)})
    r.pop("out_season",None)
print("\nwould unfreeze %d"%done)
if WRITE:
    json.dump(b,open("site/_board.json","w"),separators=(",",":"))
    print("WROTE site/_board.json")
else:
    print("(dry run -- add --write to apply)")
