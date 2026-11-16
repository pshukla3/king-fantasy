import json,sys
sys.path.insert(0,".")
from namekey import nk
import nflreadpy as nfl, polars as pl

FCT=(11.18-5.151)/8.094
SC={"py":0.04,"ptd":4.0,"int":-2.0,"ry":0.1,"rtd":6.0,
    "rec":1.0,"recy":0.1,"rectd":6.0}
B=json.load(open("site/_board.json"))
rows=B["rows"] if isinstance(B,dict) and "rows" in B else B
QP=json.load(open("qbparams.json"))
WP=json.load(open("wrparams.json"))
RP=json.load(open("rbparams.json"))

d=nfl.load_player_stats(seasons=[2026])
if "season_type" in d.columns:
    d=d.filter(pl.col("season_type")=="REG")
C=["carries","rushing_yards","rushing_tds","targets",
   "receptions","receiving_yards","receiving_tds","attempts",
   "passing_yards","passing_tds","passing_interceptions",
   "fantasy_points_ppr"]
C=[c for c in C if c in d.columns]
d=d.with_columns([pl.col(c).cast(pl.Float64).fill_null(0.0)
                  for c in C])
d=d.filter((pl.col("fantasy_points_ppr")!=0)|
           (pl.col("targets")>0)|(pl.col("carries")>0))
g=(d.group_by("player_id").agg(
   [pl.col(c).sum().alias(c) for c in C]+
   [pl.len().alias("gp"),
    pl.col("player_display_name").last().alias("nm")]))
ACT={}; ACTN={}
for r in g.iter_rows(named=True):
    ACT[r["player_id"]]=r
    ACTN.setdefault(nk(r["nm"]),r)

def pg(r):
    k=nk(r.get("n")); pos=r.get("pos")
    o={"car":0,"ry":0,"rtd":0,"tar":0,"rec":0,
       "recy":0,"rectd":0,"patt":0,"py":0,"ptd":0,"int":0}
    if pos=="QB" and k in QP:
        q=QP[k]
        o["patt"]=q.get("att",0)
        o["py"]=o["patt"]*q.get("ypa",0)
        o["ptd"]=o["patt"]*q.get("ptd",0)
        o["int"]=o["patt"]*q.get("int",0)
        o["car"]=q.get("car",0)
        o["ry"]=o["car"]*q.get("ypc",0)
        o["rtd"]=o["car"]*q.get("rtd",0)
    if pos=="RB" and k in RP:
        b=RP[k]
        o["car"]=b.get("cshare",0)*b.get("tmcar",0)
        o["ry"]=o["car"]*b.get("ypc",0)
        o["rtd"]=o["car"]*b.get("tdc",0)
    if k in WP and pos in ("WR","TE","RB"):
        w=WP[k]
        o["tar"]=w.get("tshare",0)*w.get("tmatt",0)
        o["rec"]=o["tar"]*w.get("crate",0)
        o["recy"]=o["rec"]*(w.get("adot",0)*FCT+w.get("yac",0))
        o["rectd"]=o["tar"]*w.get("tdt",0)
    return o

def pts(o):
    return (o["py"]*SC["py"]+o["ptd"]*SC["ptd"]
           +o["int"]*SC["int"]+o["ry"]*SC["ry"]
           +o["rtd"]*SC["rtd"]+o["rec"]*SC["rec"]
           +o["recy"]*SC["recy"]+o["rectd"]*SC["rectd"])

OUT={};chk=[]
def rates(a,gp):
    if not gp: return None
    r={"car":a.get("carries",0)/gp,
      "ry":a.get("rushing_yards",0)/gp,
      "rtd":a.get("rushing_tds",0)/gp,
      "tar":a.get("targets",0)/gp,
      "rec":a.get("receptions",0)/gp,
      "recy":a.get("receiving_yards",0)/gp,
      "rectd":a.get("receiving_tds",0)/gp,
      "patt":a.get("attempts",0)/gp,
      "py":a.get("passing_yards",0)/gp,
      "ptd":a.get("passing_tds",0)/gp,
      "int":a.get("passing_interceptions",0)/gp}
    w=gp/(gp+5.0)
    if r["car"]>0.3:
        o=r["rtd"]/r["car"]
        r["rtd"]=r["car"]*(w*o+(1-w)*0.030)
    if r["tar"]>0.3:
        o=r["rectd"]/r["tar"]
        r["rectd"]=r["tar"]*(w*o+(1-w)*0.045)
    if r["patt"]>1.0:
        o=r["ptd"]/r["patt"]
        r["ptd"]=r["patt"]*(w*o+(1-w)*0.045)
    return r

for r in rows:
    pos=r.get("pos")
    if pos not in ("QB","RB","WR","TE"): continue
    pid=r.get("pid"); k=nk(r.get("n"))
    a=ACT.get(pid) or ACTN.get(k) or {}
    gp=int(a.get("gp",0)); gl=int(r.get("gleft") or 0)
    lv=float(r.get("live") or 0)
    p=rates(a,gp) or pg(r)
    ip=pts(p)
    if ip>0 and lv>0: chk.append(lv/ip)
    sc=(lv/ip) if (ip>0 and lv>0) else 1.0
    sc=max(0.25,min(2.5,sc))
    T={"g":gp+gl,
       "car":round(a.get("carries",0)+p["car"]*gl*sc),
       "ryd":round(a.get("rushing_yards",0)+p["ry"]*gl*sc),
       "rtd":round(a.get("rushing_tds",0)+p["rtd"]*gl*sc,1),
       "tar":round(a.get("targets",0)+p["tar"]*gl*sc),
       "rec":round(a.get("receptions",0)+p["rec"]*gl*sc),
       "recyd":round(a.get("receiving_yards",0)+p["recy"]*gl*sc),
       "rectd":round(a.get("receiving_tds",0)+p["rectd"]*gl*sc,1),
       "patt":round(a.get("attempts",0)+p["patt"]*gl*sc),
       "pyd":round(a.get("passing_yards",0)+p["py"]*gl*sc),
       "ptd":round(a.get("passing_tds",0)+p["ptd"]*gl*sc,1),
       "int":round(a.get("passing_interceptions",0)
                   +p["int"]*gl*sc,1)}
    tp=round(a.get("fantasy_points_ppr",0)+lv*gl,1)
    T["pts"]=tp
    T["avg"]=round(tp/T["g"],1) if T["g"] else 0.0
    OUT[pid or k]=T
json.dump(OUT,open("site/_statline.json","w"),
          separators=(",",":"))
chk.sort()
print("wrote site/_statline.json  %d players"%len(OUT))
if chk:
    print("model-vs-components scale: median %.3f  "
          "p10 %.3f  p90 %.3f"%(chk[len(chk)//2],
          chk[len(chk)//10],chk[len(chk)*9//10]))
print("\n%-22s %3s %5s %5s %4s %4s %5s %4s %6s %5s"%(
  "player","g","car","ryd","rtd","tar","recyd","rtd","pts","avg"))
for n in ("Jahmyr Gibbs","Bijan Robinson","Ja'Marr Chase",
          "Jaxon Smith-Njigba","Josh Allen","Brock Bowers"):
    for r in rows:
        if r.get("n")==n:
            t=OUT.get(r.get("pid")) or {}
            if not t: break
            print("%-22s %3d %5d %5d %4.1f %4d %5d %4.1f %6.1f %5.1f"%(
              n,t["g"],t["car"],t["ryd"],t["rtd"],t["tar"],
              t["recyd"],t["rectd"],t["pts"],t["avg"]))
            break
