import json,os,re,sys
sys.path.insert(0,".")
from namekey import nk
try:
    from namekey import TEAMFIX
except Exception:
    TEAMFIX={}
ALIAS=dict(TEAMFIX)
ALIAS.update({"LAR":"LA","LVR":"LV","JAC":"JAX",
  "WSH":"WAS","KCC":"KC","SFO":"SF","GNB":"GB",
  "TAM":"TB","NWE":"NE","NOR":"NO","ARZ":"ARI"})

W=sys.argv[1] if len(sys.argv)>1 else "10"
SRC="ranks/wk%s.txt"%W
OUT="ranks/wk%s.json"%W
os.makedirs("ranks",exist_ok=True)
if not os.path.exists(SRC):
    open(SRC,"a").close()
    sys.exit("made empty %s -- put your list there"%SRC)

C=json.load(open("site/_ids.json"))["canon"]
PMAP={"PK":"K","DEF":"DST","D/ST":"DST","DST":"DST"}
def gp(v):
    u=(v.get("pos") or "").upper()
    return PMAP.get(u,u)

TEAMS=set();IDX={}
for pid,v in C.items():
    if v.get("tm"):TEAMS.add(str(v["tm"]).upper())
    IDX.setdefault(nk(v.get("n") or ""),[]).append(pid)
POS=set(["QB","RB","WR","TE","K","PK","DST","DEF","D/ST"])

def parse(ln):
    s=ln.strip()
    if not s or s.startswith("#"):return None
    s=s.replace("\t"," ")
    s=re.sub(r"^\d+[\.\)]?\s*","",s)
    s=re.sub(r"[(),]"," ",s)
    s=re.sub(r"\s+-\s+"," ",s)
    t=s.split();pos=tm=None
    while t:
        u=t[-1].upper()
        if u in POS and pos is None:
            pos=PMAP.get(u,u);t.pop();continue
        ua=ALIAS.get(u,u)
        if ua in TEAMS and tm is None:
            tm=ua;t.pop();continue
        break
    if not t:return None
    return (" ".join(t),pos,tm)

NAMEFIX={"chig okonkwo":"Chigoziem Okonkwo",
  "zonovan knight":"Bam Knight",
  "hollywood brown":"Marquise Brown",
  "theo wease":"Theo Wease Jr",
  "marvin harrison":"Marvin Harrison Jr"}
PINTEAM={"kyle williams":"NEP",
  "isaiah williams":"NYJ"}
SEEN=set()
rows=[];bad=[];amb=[]
for ln in open(SRC,encoding="utf-8"):
    p=parse(ln)
    if not p:continue
    nm,pos,tm=p
    _k=nk(nm)
    if _k in NAMEFIX: nm=NAMEFIX[_k]
    if not tm and nk(nm) in PINTEAM:
        tm=PINTEAM[nk(nm)]
    c=list(IDX.get(nk(nm),[]))
    if not c:
        bad.append(nm);continue
    if pos:
        f=[x for x in c if gp(C[x])==pos]
        if f:c=f
    if tm:
        f=[x for x in c if (C[x].get("tm") or "").upper()==tm]
        if f:c=f
    if len(c)>1:
        amb.append(nm+" -> "+", ".join(
            "%s/%s/%s"%(C[x]["n"],gp(C[x]),C[x].get("tm")) for x in c))
    if c[0] in SEEN:
        amb.append(nm+" -> DUPLICATE, skipped")
        continue
    SEEN.add(c[0])
    v=C[c[0]]
    rows.append({"rank":len(rows)+1,"pid":c[0],"n":v["n"],
                 "pos":gp(v),"tm":v.get("tm")})

pc={}
for r in rows:
    pc[r["pos"]]=pc.get(r["pos"],0)+1
    r["posrk"]=pc[r["pos"]]

json.dump({"week":int(W),"n":len(rows),"rows":rows},
          open(OUT,"w"),separators=(",",":"))
print("matched %d players -> %s"%(len(rows),OUT))
print("by position:",dict(sorted(pc.items())))
print("\nUNMATCHED (%d):"%len(bad))
for b in bad[:40]:print("  ",b)
print("\nAMBIGUOUS (%d):"%len(amb))
for a in amb[:20]:print("  ",a)
