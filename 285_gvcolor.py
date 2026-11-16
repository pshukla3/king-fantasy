s = open("site/_game.js").read()
n0 = len(s)
R = []

def rep(a, b, why):
    global s
    assert a in s, "MISSING: " + why
    s = s.replace(a, b, 1)
    R.append(why)

rep('function curve(pts){',
    'function curve(pts,col){', "curve signature")
rep("+'<path d=\"'+d+'\" fill=\"none\" stroke=\"#8ab4f8\" '",
    "+'<path d=\"'+d+'\" fill=\"none\" stroke=\"'"
    "+(col||\"#8ab4f8\")+'\" '", "curve stroke color")

rep('function field(y,dir,ha,aa){',
    'function field(y,dir,ha,aa,hc,ac){', "field signature")
rep("+'<rect x=\"0\" y=\"0\" width=\"10\" height=\"53.3\" "
    "fill=\"#16241a\"/>'",
    "+'<rect x=\"0\" y=\"0\" width=\"10\" height=\"53.3\" "
    "fill=\"'+(ac||\"#16241a\")+'\" opacity=\".55\"/>'",
    "away endzone color")
rep("+'<rect x=\"110\" y=\"0\" width=\"10\" height=\"53.3\" "
    "fill=\"#16241a\"/>'",
    "+'<rect x=\"110\" y=\"0\" width=\"10\" height=\"53.3\" "
    "fill=\"'+(hc||\"#16241a\")+'\" opacity=\".55\"/>'",
    "home endzone color")

rep(' var sp=0,hasSp=false,st="",series=[],ply=[];',
    ' var sp=0,hasSp=false,st="",series=[],ply=[];\n'
    ' var ac="#7a7d82",hc="#8ab4f8",hist="";',
    "color vars")

rep(' live=(((evt.status||{}).type||{}).state==="in");}',
    ' live=(((evt.status||{}).type||{}).state==="in");\n'
    '  var cp=(c.competitors||[]);\n'
    '  for(var ci=0;ci<cp.length;ci++){\n'
    '   var tm=(cp[ci].team||{});\n'
    '   var cl=tm.color?("#"+tm.color):null;\n'
    '   if(!cl)continue;\n'
    '   if(cp[ci].homeAway==="home"){hc=cl;}else{ac=cl;}}}',
    "extract team colors")

rep("+field(y,posHome?1:-1,h,a)",
    "+field(y,posHome?1:-1,h,a,hc,ac)", "field call")
rep("+curve(series)", "+curve(series,hc)", "curve call")

rep("+'<div class=\"gvbar\"><div style=\"width:'\n"
    "  +(100*hw).toFixed(1)+'%\"></div></div>'",
    "+'<div class=\"gvbar\"><i style=\"width:'"
    "+(100*aw).toFixed(1)+'%;background:'+ac+'\"></i>'"
    "+'<i style=\"width:'+(100*hw).toFixed(1)"
    "+'%;background:'+hc+'\"></i></div>'",
    "two-tone probability bar")

HF = '''
function histBlock(sm,a,h){
 var lf=sm&&sm.lastFiveGames;
 if(!lf||!lf.teams)return "";
 var out="",i,k;
 for(i=0;i<lf.teams.length;i++){
  var t=lf.teams[i],ab=nz(((t.team||{}).abbreviation)||"");
  var ev2=(t.events||[]).slice(0,5),rows="";
  for(k=0;k<ev2.length;k++){
   var g=ev2[k];
   rows+='<div class="gvrp"><b>'+esc(g.opponent&&
    g.opponent.abbreviation?((g.atVs||"")+" "+
    g.opponent.abbreviation):"-")+'</b><span>'
    +esc((g.gameResult||"")+" "+(g.score||""))
    +'</span></div>';}
  if(rows)out+='<h4>'+esc(ab)+' last 5</h4>'+rows;}
 return out;}
'''
a = "function shell(){"
assert a in s, "shell anchor"
s = s.replace(a, HF + a, 1)
R.append("history block")

rep("+(roster?'<h4>Fantasy players</h4>'+roster:\"\")",
    "+hist+(roster?'<h4>Fantasy players</h4>'+roster:\"\")",
    "history into panel")
rep(" var roster=\"\";",
    " hist=histBlock(sm,a,h);\n var roster=\"\";",
    "history call")

open("site/_game.js", "w").write(s)
print("_game.js %d -> %d bytes" % (n0, len(s)))
for x in R:
    print("  ok  %s" % x)
