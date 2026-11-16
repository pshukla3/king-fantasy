import json,sys,datetime
sys.path.insert(0,".")
from namekey import nk
import nflreadpy as nfl
WRITE="--write" in sys.argv
A=datetime.datetime(2026,9,8,tzinfo=datetime.timezone.utc)
NOW=datetime.datetime.now(datetime.timezone.utc)
CUR=max(1,min(18,(NOW-A).days//7+1))
b=json.load(open("site/_board.json"))
rows=b["rows"] if isinstance(b,dict) and "rows" in b else b
SNAP=json.load(open("site/_wkproj.json"))
cols=nfl.load_schedules(seasons=[2026]).columns
locked=set();open_=set()
for g in nfl.load_schedules(seasons=[2026]).iter_rows(named=True):
    if g.get("week")!=CUR: continue
    d=str(g.get("gameday") or "");t=str(g.get("gametime") or "")
    ko=None
    try:
        ko=datetime.datetime.strptime(d+" "+(t or "20:00"),
            "%Y-%m-%d %H:%M").replace(
            tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
    except Exception: pass
    done = (ko is not None and ko<=NOW)
    for tm in (g.get("home_team"),g.get("away_team")):
        (locked if done else open_).add(tm)
print("week %d | schedule cols have gametime: %s"%(
    CUR,"gametime" in cols))
print("teams already kicked off: %d  %s"%(
    len(locked),sorted(locked)))
print("teams not yet played: %d"%len(open_))
m=SNAP.get(str(CUR)) or {}
upd=0;skip=0
for r in rows:
    if r.get("pos") in (None,"K","DST","DEF"): continue
    tm=r.get("tm")
    if tm in locked: skip+=1; continue
    w=[x for x in (r.get("wk") or []) if x.get("w")==CUR]
    if not w: continue
    k=nk(r.get("n"))
    if not k: continue
    m[k]=round(float(w[0].get("m") or 0),2); upd+=1
SNAP[str(CUR)]=m
print("\nwould update %d players | %d locked (kept frozen)"%(
    upd,skip))
for n in ("jaxon smithnjigba","trey mcbride","brock bowers"):
    print("   %-22s -> %s"%(n,m.get(n)))
if WRITE:
    bad=[k for k in SNAP if not str(k).isdigit()]
    if bad: raise SystemExit("REFUSING: non-week keys %s"%bad[:5])
    json.dump(SNAP,open("site/_wkproj.json","w"),
              separators=(",",":"))
    print("WROTE site/_wkproj.json")
else:
    print("(dry run -- add --write)")
