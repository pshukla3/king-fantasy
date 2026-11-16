import json,sys
sys.path.insert(0,".")
from namekey import nk

B=json.load(open("site/_board.json"))
rows=B["rows"] if isinstance(B,dict) and "rows" in B else B
PR=json.load(open("site/_prod.json"))["rows"]
RK=json.load(open("ranks/wk10.json"))["rows"]

bypid={};byname={}
for r in rows:
    if r.get("pid"): bypid[r["pid"]]=r
    byname.setdefault(nk(r.get("n")),[]).append(r)
ppid={x["pid"]:x for x in PR}
pnm={}
for x in PR: pnm.setdefault(nk(x["n"]),x)

ok=[];pidm=[];fbad=[];fok=[];mprod=[];mno=[]
for x in RK:
    pid=x["pid"];k=nk(x["n"])
    r=bypid.get(pid);via="pid"
    if r is None:
        c=[q for q in byname.get(k,[]) if q.get("pos")==x["pos"]] \
          or byname.get(k,[])
        if c: r=c[0];via="name"
    p=ppid.get(pid) or pnm.get(k)
    tot=p["tot"] if p else 0.0; gp=p["gp"] if p else 0
    if r is None:
        (mprod if tot>0 else mno).append(
            (x["rank"],x["n"],x["pos"],gp,tot));continue
    if via=="name":
        pidm.append((x["rank"],x["n"],pid,r.get("pid")))
    if (r.get("live") or 0)<=0:
        (fbad if tot>0 else fok).append(
            (x["rank"],x["n"],x["pos"],r.get("inj"),
             r.get("tm"),gp,tot))
    else: ok.append(x["rank"])

print("RANKED %d"%len(RK))
print("  projecting fine ......... %d"%len(ok))
print("  id mismatch (on board) .. %d"%len(pidm))
print("  zeroed BUT producing .... %d"%len(fbad))
print("  zeroed correctly ........ %d"%len(fok))
print("  absent, has production .. %d"%len(mprod))
print("  absent, no snaps ........ %d"%len(mno))
print("\n== ID MISMATCH ==")
for a in pidm: print("  #%-4d %-24s %s -> %s"%a)
print("\n== ZEROED BUT PRODUCING ==")
for a in sorted(fbad): print("  #%-4d %-22s %-3s %-12s %-4s %dg %.1f"%a)
print("\n== ABSENT, HAS PRODUCTION ==")
for a in sorted(mprod): print("  #%-4d %-22s %-3s %dg %.1f"%a)

print("\n== PROJECTION SCAN (>=5 games, biggest misses) ==")
d=[]
for r in rows:
    lv=r.get("live") or 0
    if lv<=0: continue
    p=ppid.get(r.get("pid")) or pnm.get(nk(r.get("n")))
    if not p or p["gp"]<5: continue
    d.append((lv-p["ppg"],r.get("n"),r.get("pos"),
              lv,p["ppg"],p["gp"],r.get("rk")))
d.sort()
print("  -- model TOO LOW --")
for a in d[:12]:
    print("   %-22s %-3s proj %5.2f  actual %5.2f  %+6.2f  rk%s"%(
      a[1][:22],a[2],a[3],a[4],a[0],a[6]))
print("  -- model TOO HIGH --")
for a in d[-12:][::-1]:
    print("   %-22s %-3s proj %5.2f  actual %5.2f  %+6.2f  rk%s"%(
      a[1][:22],a[2],a[3],a[4],a[0],a[6]))
print("\n  n=%d  mean err %+.3f  mean abs %.3f"%(
    len(d),sum(z[0] for z in d)/len(d),
    sum(abs(z[0]) for z in d)/len(d)))
