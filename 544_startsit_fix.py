import re
F="436_startsit.py"
s=open(F,encoding="utf-8").read()
ok=[]

HELP = """function kfCur(){var A=Date.UTC(2026,8,8);
 return Math.max(1,Math.min(18,
  Math.floor((Date.now()-A)/604800000)+1));}
function wkE(r){var w=(r&&r.wk)||[],c=kfCur();
 for(var i=0;i<w.length;i++)
  if(Number(w[i].w)===c)return w[i];
 return w[0]||null;}
function wkP(r){var e=wkE(r);
 if(!e)return (r.live==null?null:r.live);
 if(e.o==="BYE"||e.out)return 0;
 return (e.m==null?(r.live==null?null:r.live):e.m);}
function wkO(r){var e=wkE(r);
 if(!e)return "-";
 if(e.o==="BYE")return "BYE";
 return (e.h?"vs ":"@ ")+e.o;}
function wkS(r){var e=wkE(r);
 if(e&&e.o==="BYE")return "BYE - cannot start";
 if(e&&e.out)return "OUT - cannot start";
 return r.inj||"Active";}
function compare("""
if "function kfCur" not in s:
    if "function compare(" in s:
        s=s.replace("function compare(",HELP,1); ok.append("helpers")
    else: ok.append("FAIL helpers anchor")

A1=""" var best=null;
 PICK.forEach(function(r){
  if(r.live!=null&&(best==null||r.live>best.live))best=r;});"""
B1=""" var best=null,bv=-1e9;
 PICK.forEach(function(r){
  var v=wkP(r);
  if(v!=null&&v>bv){bv=v;best=r;}});"""
if A1 in s: s=s.replace(A1,B1,1); ok.append("verdict")
else: ok.append("FAIL verdict anchor")

A2=''' h+=rowOf("Projected this week",
   PICK.map(function(r){return r.live;}),n1,true);'''
B2=''' h+=rowOf("Projected this week",
   PICK.map(wkP),n1,true);
 h+=rowOf("Opponent",
   PICK.map(wkO),function(v){return esc(String(v));},false);
 h+=rowOf("Season ppg",
   PICK.map(function(r){return r.live;}),n1,true);'''
if A2 in s: s=s.replace(A2,B2,1); ok.append("proj row")
else: ok.append("FAIL proj row anchor")

A3=''' h+=rowOf("Status",
   PICK.map(function(r){return r.inj||"Active";}),
   function(v){return esc(v);},false);'''
B3=''' h+=rowOf("Status",
   PICK.map(wkS),
   function(v){return esc(String(v));},false);'''
if A3 in s: s=s.replace(A3,B3,1); ok.append("status row")
else: ok.append("FAIL status anchor")

A4="""  var gap=best.live-Math.max.apply(null,
   oth.map(function(r){
    return r.live==null?-99:r.live;}));"""
B4="""  var gap=wkP(best)-Math.max.apply(null,
   oth.map(function(r){
    var v=wkP(r);return v==null?-99:v;}));"""
if A4 in s: s=s.replace(A4,B4,1); ok.append("gap text")
else: ok.append("FAIL gap anchor")

i=s.find(" if(DR){")
if i>=0:
    j=s.find("{",i); d=0; k=j
    while k<len(s):
        if s[k]=="{": d+=1
        elif s[k]=="}":
            d-=1
            if d==0: k+=1; break
        k+=1
    s=s[:i]+s[k:]; ok.append("dead DR rows removed")
else: ok.append("DR block not found")

open(F,"w",encoding="utf-8").write(s)
import ast; ast.parse(s)
for x in ok: print(" ",x)
print("\nany failures:", any(x.startswith("FAIL") for x in ok))
