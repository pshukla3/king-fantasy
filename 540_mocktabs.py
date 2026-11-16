F="478_mock.py"
s=open(F,encoding="utf-8").read()

def repl(s,name,new):
    k=s.index("function "+name+"(")
    j=k;d=0;st=False
    while j<len(s):
        c=s[j]
        if c=='{': d+=1;st=True
        elif c=='}':
            d-=1
            if st and d==0: j+=1;break
        j+=1
    return s[:k]+new+s[j:]

TABS = (
"function setFilt(i){\n"
" var P=[" + '"ALL","QB","RB","WR","TE","K","DST"' + "];\n"
" S.filter=P[i];drawTabs();renderList();}\n"
"function drawTabs(){\n"
" var P=[" + '"ALL","QB","RB","WR","TE","K","DST"' + "],h=" + '""' + ";\n"
" var c=need(S.slot);\n"
" var mine=S.picks.filter(function(p){return p.t==S.slot}).length;\n"
" for(var i=0;i<P.length;i++){\n"
"  var lab=P[i],sub;\n"
"  if(lab==" + '"ALL"' + ") sub=mine+" + '"/"' + "+S.rounds;\n"
"  else sub=(c[lab]||0)+" + '"/"' + "+(S.slots[lab]||0);\n"
"  h+=" + "'<button class=\"'" + "+(S.filter==P[i]?" + '"on"' + ":" + '""' + ")+\n"
"   " + "'\" onclick=\"setFilt('" + "+i+" + "')\">'" + "+lab+\n"
"   " + "'<small>'" + "+sub+" + "'</small></button>'" + ";}\n"
" document.getElementById(" + '"tabs"' + ").innerHTML=h;}"
)
s=repl(s,"drawTabs",TABS)
open(F,"w",encoding="utf-8").write(s)
import ast;ast.parse(s)
print("drawTabs rewritten without escapes")
