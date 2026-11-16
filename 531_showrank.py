import json,sys,csv
sys.path.insert(0,".")
from namekey import nk
B=json.load(open("site/_board.json"))
rows=B["rows"] if isinstance(B,dict) and "rows" in B else B
RK=json.load(open("ranks/wk10.json"))["rows"]
PR={}
for x in json.load(open("site/_prod.json"))["rows"]:
    PR[nk(x["n"])]=x
bypid={r["pid"]:r for r in rows if r.get("pid")}
bynm={}
for r in rows: bynm.setdefault(nk(r.get("n")),r)

out=[]
for x in RK:
    r=bypid.get(x["pid"]) or bynm.get(nk(x["n"]))
    p=PR.get(nk(x["n"]))
    out.append([x["rank"],x["n"],x["pos"],
      (r.get("tm") if r else "-"),
      (r.get("live") if r else None),
      (p["ppg"] if p else None),(p["gp"] if p else 0),
      (r.get("inj") if r else "ABSENT")])
ks=sorted([r for r in rows if r.get("pos")=="K"
           and (r.get("live") or 0)>0],
          key=lambda r:-(r.get("live") or 0))
n=len(out)
for i,r in enumerate(ks):
    out.append([n+i+1,r.get("n"),"K",r.get("tm"),
                r.get("live"),None,0,r.get("inj")])

w=csv.writer(open("ranks/merged_wk10.csv","w",newline=""))
w.writerow(["rank","player","pos","tm","proj","actual_ppg","g","status"])
for o in out: w.writerow(o)
print("wrote ranks/merged_wk10.csv  (%d rows)\n"%len(out))
print("%-4s %-24s %-3s %-4s %6s %6s %3s %s"%(
  "#","player","pos","tm","proj","act","g","status"))
for o in out:
    print("%-4d %-24s %-3s %-4s %6s %6s %3d %s"%(
      o[0],str(o[1])[:24],o[2],str(o[3])[:4],
      ("%.2f"%o[4]) if o[4] is not None else "  -",
      ("%.2f"%o[5]) if o[5] is not None else "  -",
      o[6],o[7]))
