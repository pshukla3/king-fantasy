import re,sys,os
W=[a for a in sys.argv[1:] if a.isdigit()]
W=W[0] if W else "11"
SRC="ranks/raw%s.txt"%W; OUT="ranks/wk%s.txt"%W
if not os.path.exists(SRC): sys.exit("missing %s"%SRC)
L=[x.strip() for x in open(SRC,encoding="utf-8")]
RANK=re.compile(r'^\d+$')
MOVE=re.compile(r'^[+-]\d+$')
POSN=re.compile(r'^(QB|RB|WR|TE|K|DST)\s*\d+$',re.I)
got={};dup=[];i=0
while i+2 < len(L):
    if RANK.match(L[i]):
        j=i+1
        while j<len(L) and (not L[j] or MOVE.match(L[j])):
            j+=1
        if j+1<len(L) and L[j] and POSN.match(L[j+1]):
            rk=int(L[i]); nm=L[j]
            pos=POSN.match(L[j+1]).group(1).upper()
            if rk in got and got[rk][0]!=nm:
                dup.append((rk,got[rk][0],nm))
            got[rk]=(nm,pos); i=j+2; continue
    i+=1
if not got: sys.exit("parsed nothing")
ks=sorted(got)
gaps=[r for r in range(1,ks[-1]+1) if r not in got]
open(OUT,"w",encoding="utf-8").write(
  "\n".join("%s %s"%(got[r][0],got[r][1]) for r in ks)+"\n")
print("parsed %d (%d..%d)"%(len(got),ks[0],ks[-1]))
print("GAPS (%d): %s"%(len(gaps),gaps[:40]))
print("COLLISIONS (%d): %s"%(len(dup),dup[:6]))
