import json,os
import nflreadpy as nfl
import polars as pl

SEA=2026
d=nfl.load_player_stats(seasons=[SEA])
if "season_type" in d.columns:
    d=d.filter(pl.col("season_type")=="REG")
NUM=["targets","receptions","carries","receiving_yards",
 "rushing_yards","receiving_air_yards","target_share",
 "air_yards_share","wopr","receiving_first_downs",
 "rushing_first_downs","receiving_20","rushing_20",
 "fantasy_points_ppr"]
NUM=[c for c in NUM if c in d.columns]
d=d.with_columns([pl.col(c).cast(pl.Float64).fill_null(0.0)
                  for c in NUM])
tw=d.group_by(["team","week"]).agg(
    pl.col("carries").sum().alias("tc"))
d=d.join(tw,on=["team","week"],how="left")
d=d.with_columns(
  (pl.col("carries")/pl.when(pl.col("tc")>0)
   .then(pl.col("tc")).otherwise(1)).alias("rsh"))
d=d.filter((pl.col("fantasy_points_ppr")!=0)
  |(pl.col("targets")>0)|(pl.col("carries")>0))

g=(d.group_by(["player_id","player_display_name","position"])
  .agg([pl.len().alias("gp"),
    pl.col("team").last().alias("tm"),
    pl.col("fantasy_points_ppr").mean().alias("ppg"),
    pl.col("targets").mean().alias("tgt"),
    pl.col("receptions").mean().alias("rec"),
    pl.col("carries").mean().alias("car"),
    pl.col("target_share").mean().alias("tsh"),
    pl.col("air_yards_share").mean().alias("aysh"),
    pl.col("wopr").mean().alias("wopr"),
    pl.col("rsh").mean().alias("rsh"),
    pl.col("receiving_air_yards").mean().alias("ay"),
    (pl.col("receiving_20")+pl.col("rushing_20"))
      .mean().alias("expl"),
    (pl.col("receiving_first_downs")
     +pl.col("rushing_first_downs")).mean().alias("fd")]))

rows=[]
for r in g.iter_rows(named=True):
    p=(r["position"] or "").upper()
    if p not in ("QB","RB","WR","TE"): continue
    o={"pid":r["player_id"],"n":r["player_display_name"],
       "pos":p,"tm":r["tm"],"gp":int(r["gp"])}
    for k in ("ppg","tgt","rec","car","tsh","aysh","wopr",
              "rsh","ay","expl","fd"):
        o[k]=round(float(r[k] or 0),3)
    o["tch"]=round(o["car"]+o["rec"],2)
    rows.append(o)
json.dump({"season":SEA,"rows":rows},
          open("site/_opp.json","w"),separators=(",",":"))
print("wrote site/_opp.json  players=%d"%len(rows))

RK="ranks/wk10.json"
if os.path.exists(RK):
    rk=json.load(open(RK))["rows"]
    by={x["pid"]:x for x in rows}
    print("\n%-3s %-23s %-4s %4s %5s %5s %5s %5s %5s %5s"%(
      "#","player","pos","ppg","tgt","rec","car","tsh%","rsh%","wopr"))
    for x in rk[:40]:
        o=by.get(x["pid"])
        if not o:
            print("%-3d %-23s %-4s   (no 2026 snaps)"%(
              x["rank"],x["n"],x["pos"]));continue
        print("%-3d %-23s %-4s %4.1f %5.1f %5.1f %5.1f %5.1f %5.1f %5.2f"%(
          x["rank"],x["n"][:23],o["pos"],o["ppg"],o["tgt"],
          o["rec"],o["car"],o["tsh"]*100,o["rsh"]*100,o["wopr"]))
