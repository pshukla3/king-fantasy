import json
import nflreadpy as nfl
import polars as pl

SEA=2026
d=nfl.load_player_stats(seasons=[SEA])
if "season_type" in d.columns:
    d=d.filter(pl.col("season_type")=="REG")
d=d.filter(pl.col("fantasy_points_ppr").is_not_null())
act=(pl.col("fantasy_points_ppr")!=0)
for c in ("targets","carries","attempts","fg_att","pat_att"):
    if c in d.columns:
        act=act|(pl.col(c).fill_null(0)>0)
d=d.filter(act)

g=(d.group_by(["player_id","player_display_name","position"])
   .agg([pl.col("fantasy_points_ppr").sum().alias("tot"),
         pl.len().alias("gp"),
         pl.col("team").last().alias("tm"),
         pl.col("week").max().alias("lastwk")])
   .with_columns((pl.col("tot")/pl.col("gp")).alias("ppg")))

PM={"PK":"K","FB":"RB"}
rows=[]
for r in g.iter_rows(named=True):
    p=PM.get((r["position"] or "").upper(),
             (r["position"] or "").upper())
    if p not in ("QB","RB","WR","TE","K"): continue
    rows.append({"pid":r["player_id"],"n":r["player_display_name"],
      "pos":p,"tm":r["tm"],"tot":round(r["tot"],2),
      "gp":int(r["gp"]),"ppg":round(r["ppg"],2),
      "lastwk":int(r["lastwk"])})

for key,lab in (("tot","trk"),("ppg","prk")):
    by={}
    for x in sorted(rows,key=lambda z:-z[key]):
        by[x["pos"]]=by.get(x["pos"],0)+1
        x[lab]=by[x["pos"]]
for i,x in enumerate(sorted(rows,key=lambda z:-z["tot"]),1):
    x["ovr"]=i

json.dump({"season":SEA,"n":len(rows),"rows":rows},
          open("site/_prod.json","w"),separators=(",",":"))
print("wrote site/_prod.json players=%d"%len(rows))
print("through week",int(d["week"].max()))
for pos in ("QB","RB","WR","TE","K"):
    s=sorted([x for x in rows if x["pos"]==pos],
             key=lambda z:-z["tot"])
    print("\n== %s top 8 by total =="%pos)
    for x in s[:8]:
        print("  %-24s %6.1f tot  %5.2f ppg  %d g"%(
          x["n"],x["tot"],x["ppg"],x["gp"]))
CHK=("Trey McBride","Josh Allen","Bucky Irving",
     "Justin Jefferson","Jahmyr Gibbs","Puka Nacua",
     "Malik Nabers","James Cook","Jaxon Smith-Njigba")
print("\n== spot check vs board ==")
for x in sorted(rows,key=lambda z:-z["tot"]):
    if x["n"] in CHK:
        print("  %-22s %5.2f ppg  %6.1f tot  %d g  %s%d"%(
          x["n"],x["ppg"],x["tot"],x["gp"],x["pos"],x["trk"]))
