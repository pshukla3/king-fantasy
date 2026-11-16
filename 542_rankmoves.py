import json,sys
sys.path.insert(0,".")
from namekey import nk
import nflreadpy as nfl, polars as pl
WK=10
d=nfl.load_player_stats(seasons=[2026])
if "season_type" in d.columns:
    d=d.filter(pl.col("season_type")=="REG")
w=d.filter(pl.col("week")==WK)
A={}
for r in w.iter_rows(named=True):
    p=(r.get("position") or "").upper()
    if p not in ("QB","RB","WR","TE"): continue
    A[nk(r.get("player_display_name"))]={
      "n":r.get("player_display_name"),"pos":p,"tm":r.get("team"),
      "p":float(r.get("fantasy_points_ppr") or 0),
      "opp":float(r.get("targets") or 0)+float(r.get("carries") or 0)
            +float(r.get("attempts") or 0)}
OPP={}
for x in json.load(open("site/_opp.json"))["rows"]:
    OPP[nk(x["n"])]=x
SNAP=json.load(open("site/_wkproj.json")).get(str(WK),{})
B=json.load(open("site/_board.json"))
rows=B["rows"] if isinstance(B,dict) and "rows" in B else B
RK={nk(r.get("n")):r for r in rows}
out=[]
for k,a in A.items():
    pr=SNAP.get(k); r=RK.get(k)
    if pr is None or r is None: continue
    o=OPP.get(k,{})
    base=(o.get("tgt",0)+o.get("car",0))
    if a["pos"]=="QB": base=max(base,20.0)
    ratio=(a["opp"]/base) if base>0.5 else 1.0
    diff=a["p"]-float(pr)
    if ratio<0.45: tag="INJURY/OUT - hold"
    elif diff>8 and ratio>1.15: tag="REAL RISE"
    elif diff>8: tag="noise spike"
    elif diff<-8 and ratio>0.8: tag="REAL FALL"
    elif diff<-8: tag="low usage - hold"
    else: tag=""
    out.append((diff,a["n"],a["pos"],a["tm"],float(pr),a["p"],
                r.get("rk"),ratio,a["opp"],str(r.get("inj")),tag))
def show(t,rs):
    print("\n== %s =="%t)
    print("%-22s %-3s %5s %6s %6s %5s %5s %-11s %s"%(
      "player","pos","rank","proj","act","opp","vs avg","status","read"))
    for z in rs:
        print("%-22s %-3s %5s %6.1f %6.1f %5.0f %5.2fx %-11s %s"%(
          z[1][:22],z[2],str(z[6]),z[4],z[5],z[8],z[7],z[9][:11],z[10]))
rise=[z for z in out if z[10]=="REAL RISE"]
fall=[z for z in out if z[10]=="REAL FALL"]
hold=[z for z in out if z[10].startswith("INJURY")]
noise=[z for z in out if z[10]=="noise spike"]
rise.sort(key=lambda z:-z[0]); fall.sort(key=lambda z:z[0])
hold.sort(key=lambda z:z[0]); noise.sort(key=lambda z:-z[0])
show("REAL RISES  (beat it on real workload)",rise[:15])
show("REAL FALLS  (played, underperformed)",fall[:15])
show("INJURY / OUT  (do not downgrade)",hold[:15])
show("NOISE SPIKES  (ignore)",noise[:10])
