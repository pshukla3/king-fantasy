import glob,sys
NEWORD='''function revR(r){
 if(S.pat=="linear")return false;
 if(S.pat=="3rr")return r==1||(r>=2&&r%2==0);
 return r%2==1;}
function order(){
 var o=[];
 for(var r=0;r<S.rounds;r++){
  var a=[];for(var t=1;t<=S.teams;t++)a.push(t);
  if(revR(r))a.reverse();
  o=o.concat(a);}
 return o;}'''
NEWGRID='''function drawGrid(){
 var h='<table class="g"><thead><tr><th class="rh"></th>';
 for(var t=1;t<=S.teams;t++)
  h+='<th'+(t==S.slot?' class="meh"':'')+'>'+
   (t==S.slot?"YOU":
    NAMES[(t-1)%NAMES.length].split(" ")[0])+'</th>';
 h+='</tr></thead><tbody>';
 for(var r=0;r<S.rounds;r++){
  var rv=revR(r);
  h+='<tr><th class="rh">'+(r+1)+'</th>';
  for(var c=0;c<S.teams;c++){
   var idx=r*S.teams+(rv?(S.teams-1-c):c);
   var t=ORD[idx],pk=S.picks[idx],cl="c";
   if(t==S.slot)cl+=" me";
   if(idx==S.pick)cl+=" on";
   if(pk){cl+=" f p-"+pk.pl.pos;if(pk.reach)cl+=" rch"}
   h+='<td class="'+cl+'"><em>'+(idx+1)+'</em>';
   if(pk)h+='<b>'+pk.pl.n+'</b><i>'+pk.pl.pos+
    ' \\u00b7 '+pk.pl.tm+'</i>';
   h+='</td>';}
  h+='</tr>';}
 document.getElementById("grid").innerHTML=h+'</tbody></table>';}'''

def block(s,i):
    d=0;st=False
    for j in range(i,len(s)):
        c=s[j]
        if c=='{': d+=1;st=True
        elif c=='}':
            d-=1
            if st and d==0: return j+1
    return -1

tgt=None
for f in sorted(glob.glob("*.py")):
    s=open(f,encoding="utf-8").read()
    if "function drawGrid(){" in s and "function order(){" in s:
        tgt=f;break
if not tgt:
    sys.exit("no generator holds drawGrid; is mock.html hand-written?")
s=open(tgt,encoding="utf-8").read()
for name,new in (("function order(){",NEWORD),
                 ("function drawGrid(){",NEWGRID)):
    if s.count(name)!=1:
        sys.exit("%s appears %dx in %s"%(name,s.count(name),tgt))
    i=s.index(name); j=block(s,i)
    s=s[:i]+new+s[j:]
open(tgt,"w",encoding="utf-8").write(s)
import ast; ast.parse(s)
print("patched %s (ast ok)"%tgt)
print("revR present:", "function revR" in s)
