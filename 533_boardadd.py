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
B="site/_board.json"
b=json.load(open(B))
rows=b["rows"] if isinstance(b,dict) and "rows" in b else b
RK=json.load(open("ranks/wk%s.json"%W))["rows"]
C=json.load(open("site/_ids.json"))["canon"]
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
sch=nfl.load_schedules(seasons=[2026])
SC={}
for g in sch.iter_rows(named=True):
    w=g.get("week");h=g.get("home_team");a=g.get("away_team")
    if not w or not h or not a: continue
    SC.setdefault(h,{})[w]=(a,1)
    SC.setdefault(a,{})[w]=(h,0)

REP={};MX={}
for p in ("QB","RB","WR","TE"):
    d=sorted((r.get("live") or 0)-(r.get("vorp") or 0)
             for r in rows if r.get("pos")==p
             and (r.get("live") or 0)>0
             and r.get("vorp") is not None)
    REP[p]=d[len(d)//2] if d else 0.0
    MX[p]=max([r.get("vorp") or 0 for r in rows
               if r.get("pos")==p] or [1]) or 1

def team(t):
    t=(t or "").upper(); t=LONG.get(t,t)
    return t if t in SC else None

added=[];skip=[]
for x in RK:
    pid=x["pid"];k=nk(x["n"]);pos=x["pos"]
    if pid in bypid: continue
    if [q for q in bynm.get(k,[]) if q.get("pos")==pos]: continue
    if bynm.get(k): continue
    if pos not in ("QB","RB","WR","TE"): continue
    p=PR.get(pid) or PN.get(k)
    if not p or (p.get("gp") or 0)<1:
        skip.append((x["rank"],x["n"],"no 2026 snaps"));continue
    tm=team(p.get("tm")) or team((C.get(pid) or {}).get("tm"))
    if not tm:
        skip.append((x["rank"],x["n"],"no team/schedule"));continue
    ppg=float(p["ppg"]);bye=None;wk=[];gl=0
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
    val=max(1,min(100,int(round(100*vorp/MX[pos]))))
    sid=(C.get(pid) or {}).get("sid")
    r={"rk":9999,"pid":pid,"n":x["n"],"pos":pos,"tm":tm,
       "logo":tm.lower(),"posrk":99,"tier":10,"bye":bye,
       "sos":0,"risk":0.06,"games":p["gp"],"gm":p["gp"],
       "floor":round(ppg*0.55,2),"base":round(ppg,2),
       "live":round(ppg,2),"ceil":round(ppg*1.65,2),
       "vorp":vorp,"uvorp":vorp,"val":val,"uval":val,
       "urk":9999,"inj":"Active","gleft":gl,"miss":0,
       "ros":round(ppg*gl,1),"rosv":round(vorp*gl,2),
       "wk":wk,"img":("https://sleepercdn.com/content/nfl/"
         "players/%s.jpg"%sid) if sid else ""}
    rows.append(r);added.append((x["rank"],x["n"],pos,tm,ppg,gl,bye))

print("current week %d | added %d | skipped %d"%(
    CUR,len(added),len(skip)))
print("\n== ADDED ==")
for a in sorted(added):
    print("  #%-4d %-22s %-3s %-4s ppg %5.2f  gleft %d  bye %s"%a)
print("\n== SKIPPED ==")
for s in sorted(skip): print("  #%-4d %-22s %s"%s)
if WRITE:
    json.dump(b,open(B,"w"),separators=(",",":"))
    print("\nWROTE %s (%d rows)"%(B,len(rows)))
else:
    print("\n(dry run -- add --write to apply)")
