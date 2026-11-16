import json,sys
sys.path.insert(0,".")
from namekey import nk
import nflreadpy as nfl, polars as pl
WK=10
d=nfl.load_player_stats(seasons=[2026])
if "season_type" in d.columns:
    d=d.filter(pl.col("season_type")=="REG")
d=d.filter(pl.col("week")==WK)
ACT={}
for r in d.iter_rows(named=True):
    p=(r.get("position") or "").upper()
    if p not in ("QB","RB","WR","TE"): continue
    ACT[nk(r.get("player_display_name"))]={
      "p":float(r.get("fantasy_points_ppr") or 0),
      "n":r.get("player_display_name"),"pos":p,
      "tm":r.get("team"),
      "tar":float(r.get("targets") or 0),
      "car":float(r.get("carries") or 0)}
SNAP=json.load(open("site/_wkproj.json")).get(str(WK),{})
B=json.load(open("site/_board.json"))
rows=B["rows"] if isinstance(B,dict) and "rows" in B else B
RK={nk(r.get("n")):r for r in rows}
PR={}
for x in json.load(open("site/_prod.json"))["rows"]:
    PR[nk(x["n"])]=x
out=[]
for k,a in ACT.items():
    pr=SNAP.get(k); r=RK.get(k)
    if pr is None or r is None: continue
    pp=PR.get(k,{})
    out.append((a["p"]-float(pr),a["n"],a["pos"],a["tm"],
                float(pr),a["p"],r.get("rk"),
                pp.get("ppg",0),a["tar"],a["car"]))
out.sort()
def show(t,rowsx):
    print("\n== %s =="%t)
    print("%-22s %-3s %-4s %6s %6s %6s %5s %5s %5s"%(
      "player","pos","tm","proj","actual","diff","rank","ppg","opp"))
    for z in rowsx:
        print("%-22s %-3s %-4s %6.1f %6.1f %+6.1f %5s %5.1f %5.0f"%(
          z[1][:22],z[2],str(z[3])[:4],z[4],z[5],z[0],
          str(z[6]),z[7],z[8]+z[9]))
show("BEAT THE PROJECTION MOST",out[-18:][::-1])
show("MISSED BY MOST",out[:18])
print("\nscored %d players | mean error %+.2f | mean abs %.2f"%(
  len(out),sum(z[0] for z in out)/len(out),
  sum(abs(z[0]) for z in out)/len(out)))
