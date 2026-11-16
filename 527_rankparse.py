import re,os,sys
SRC="ranks/raw10.txt"
OUT="ranks/wk10.txt"
KEEP=39
PAT=re.compile(
 r'^\s*(\d+)\s*[\.\)]\s*(.*?)(QB|RB|WR|TE|DST|K)\s*(\d+)\s*$')
PLAIN=re.compile(r'^\s*(\d+)\s*[\.\)]\s*(.+?)\s*$')
NOISE={"TIER","FPTS","TEAM","PLAYED","SNAP%","DD","EE","FF",
       "GG","HH","II","JJ","KK","LL","MM","NN","OO","PP"}

got={};dup=[]
for ln in open(SRC,encoding="utf-8"):
    s=ln.strip()
    if not s or s.upper() in NOISE: continue
    if re.match(r'^[+-]\d+$',s): continue
    m=PAT.match(s)
    if m:
        rk=int(m.group(1));nm=m.group(2).strip();pos=m.group(3)
    else:
        m=PLAIN.match(s)
        if not m: continue
        rk=int(m.group(1));nm=m.group(2).strip();pos=None
        if nm.upper() in NOISE or len(nm)<3: continue
    if not re.search(r'[A-Za-z]{2}',nm): continue
    if rk in got and got[rk][0]!=nm: dup.append((rk,got[rk][0],nm))
    got[rk]=(nm,pos)

names={}
for rk,(nm,pos) in got.items():
    names.setdefault(nm.lower(),[]).append(rk)
repeat=[(n,v) for n,v in names.items() if len(v)>1]

old=[]
if os.path.exists(OUT):
    old=[l.rstrip("\n") for l in open(OUT,encoding="utf-8")][:KEEP]
new=[]
for rk in sorted(got):
    if rk<=len(old): continue
    nm,pos=got[rk]
    new.append(nm+((" "+pos) if pos else ""))
open(OUT,"w",encoding="utf-8").write(
    "\n".join(old+new)+"\n")

ks=sorted(got)
if not ks:
    raise SystemExit("no ranked lines found in %s -- "
      "is the list actually in there? head it and look"%SRC)
print("parsed %d ranked lines (%d..%d)"%(len(got),ks[0],ks[-1]))
gaps=[r for r in range(ks[0],ks[-1]+1) if r not in got]
print("kept %d existing + %d new = %d total"%(
    len(old),len(new),len(old)+len(new)))
print("GAPS (%d):"%len(gaps),gaps[:30])
print("RANK COLLISIONS (%d):"%len(dup))
for d in dup[:10]: print("  ",d)
print("REPEATED NAMES (%d):"%len(repeat))
for n,v in repeat[:10]: print("  ",n,v)
