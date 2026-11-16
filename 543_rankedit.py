import sys,os,shutil
sys.path.insert(0,".")
from namekey import nk
SRC="ranks/wk11.txt"; DST="ranks/wk12.txt"
if not os.path.exists(DST):
    shutil.copy(SRC,DST); print("created %s from %s"%(DST,SRC))
L=[x.rstrip("\n") for x in open(DST,encoding="utf-8") if x.strip()]
POS={"QB","RB","WR","TE","K","DST"}
def namepart(l):
    t=l.split()
    while t and (t[-1].upper() in POS or
                 (len(t[-1])<=3 and t[-1].isupper())):
        t.pop()
    return nk(" ".join(t))
IDX={}
for i,l in enumerate(L): IDX.setdefault(namepart(l),i)

MOVES=[("Emmett Johnson",48),
       ("George Pickens",28),
       ("Isaiah Likely",32),
       ("Cam Skattebo",44),
       ("Javonte Williams",24),
       ("Kyren Williams",30),
       ("Tetairoa McMillan",45)]

print("\n%-24s %5s    %5s"%("player","from","to"))
for name,newrank in MOVES:
    k=nk(name); i=-1
    for j,l in enumerate(L):
        if namepart(l)==k: i=j; break
    if i<0:
        print("%-24s NOT FOUND"%name); continue
    line=L.pop(i)
    t=min(max(0,newrank-1),len(L))
    L.insert(t,line)
    print("%-24s %5d -> %5d"%(name,i+1,t+1))
open(DST,"w",encoding="utf-8").write("\n".join(L)+"\n")
print("\n%s now %d lines"%(DST,len(L)))
print("\ntop 50 after edits:")
for i,l in enumerate(L[:50],1):
    print("  %3d %s"%(i,l))
