import json

D = json.load(open("league_data.json"))
assert "rosters" in D, "run 152_rosters.py first"
CSS = open("site/_league.css").read() + """
.two{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.pl{display:flex;justify-content:space-between;
padding:9px 11px;border-radius:3px;cursor:pointer;
font-size:14px;border:1px solid transparent}
.pl:hover{background:#1c1d1f}
.pl.on{background:#232427;border-color:#d6dded}
.pl .r{color:#72757e}
.res{background:#141416;border-radius:3px;
padding:22px;margin-top:20px}
.big{font-size:34px;font-weight:700}
.lbl{color:#72757e;font-size:13px;
text-transform:uppercase;letter-spacing:.5px}
.vd{padding:16px;border-radius:3px;margin-top:16px;
font-size:16px;line-height:1.5}
.good{background:#202123;border-left:4px solid #d6dded}
.bad{background:#1c1d1f;border-left:4px solid #ecf3ff}
.mid{background:#1c1d1f;border-left:4px solid #72757e}
.wk{display:grid;grid-template-columns:repeat(7,1fr);
gap:8px;margin-top:14px}
.wc{background:#1c1d1f;border-radius:3px;padding:9px;
text-align:center;font-size:13px}
.wc b{display:block;font-size:15px;margin-top:3px}
"""

JS = """
const D=__DATA__;
const SL=["QB","RB","RB","WR","WR","TE","FLEX","FLEX",
"K","DEF"];
const FX=["RB","WR","TE"];
const R={};D.rosters.forEach(t=>{R[t.roster_id]=t;});
let sA=new Set(),sB=new Set();
function ps(p){return p.pos=="DST"?"DEF":p.pos;}
function lineup(pool,wk){
 const av=pool.filter(p=>!wk||p.bye!=wk);
 const u=new Set();let tot=0;const holes=[];
 for(const s of SL){
  const ok=(s=="FLEX")?FX:[s];
  let bi=-1,bv=-1;
  for(let i=0;i<av.length;i++){
   if(u.has(i))continue;
   if(ok.indexOf(ps(av[i]))<0)continue;
   if(av[i].ppg>bv){bv=av[i].ppg;bi=i;}}
  if(bi<0){holes.push(s);continue;}
  u.add(bi);tot+=bv;}
 return [tot,holes];}
function opts(el,def){
 D.rosters.forEach(t=>{
  const o=document.createElement('option');
  o.value=t.roster_id;o.textContent=t.name;
  if(t.roster_id==def)o.selected=true;
  el.appendChild(o);});}
function tog(w,i){
 const s=(w=='la')?sA:sB;
 if(s.has(i))s.delete(i);else s.add(i);draw();}
function plist(t,sel,el){
 let h='';
 t.players.forEach((p,i)=>{
  const on=sel.has(i)?'on':'';
  h+='<div class="pl '+on+'" onclick="tog(\\''+el+
  '\\','+i+')"><span><span class="pos '+ps(p)+'">'+
  p.pos+'</span> '+p.name+'</span><span class=r>'+
  p.ppg.toFixed(2)+'</span></div>';});
 document.getElementById(el).innerHTML=h;}
function oc(id){
 if(!id)return;
 try{if(window.top&&window.top.openCard){
  window.top.openCard(id);return;}}catch(e){}
 window.open('player.html#id='+encodeURIComponent(id),
  '_blank');}
function draw(){
 const a=R[document.getElementById('ta').value];
 const b=R[document.getElementById('tb').value];
 plist(a,sA,'la');plist(b,sB,'lb');
 const ga=[],gb=[];
 sA.forEach(i=>ga.push(a.players[i]));
 sB.forEach(i=>gb.push(b.players[i]));
 const na=a.players.filter((p,i)=>!sA.has(i)).concat(gb);
 const nb=b.players.filter((p,i)=>!sB.has(i)).concat(ga);
 const a0=lineup(a.players)[0],b0=lineup(b.players)[0];
 const ra=lineup(na),rb=lineup(nb);
 const a1=ra[0],b1=rb[0],ha=ra[1];
 const da=a1-a0,db=b1-b0;
 let wks='';
 for(let w=1;w<=14;w++){
  const x=lineup(a.players,w)[0],y=lineup(na,w)[0];
  const d=y-x;
  const c=(d>0.05)?'g':((d<-0.05)?'r2':'');
  wks+='<div class=wc>wk '+w+'<b class="'+c+'">'+
  (d>0?'+':'')+d.toFixed(1)+'</b></div>';}
 let cls='mid',msg='Even. No real edge either way.';
 if(da>0.5&&db>0.5){cls='good';
  msg='Both sides gain. Should clear easily.';}
 else if(da>0.5){cls='good';
  msg='You gain '+da.toFixed(2)+' ppg, they lose '+
  (-db).toFixed(2)+'. Expect pushback.';}
 else if(da<-0.5){cls='bad';
  msg='You lose '+(-da).toFixed(2)+' ppg. Decline.';}
 if(ha.length)msg+=' WARNING: no '+ha.join('/')+
 ' in your lineup after this.';
 let h='<div class=two><div><div class=lbl>'+a.name+
 '</div><div class=big>'+a0.toFixed(1)+' &rarr; <span '+
 'class="'+(da>0?'g':'r2')+'">'+a1.toFixed(1)+
 '</span></div><div class=lbl>'+(da>0?'+':'')+
 da.toFixed(2)+' per week &middot; '+(da*14).toFixed(0)+
 ' over 14</div></div><div><div class=lbl>'+b.name+
 '</div><div class=big>'+b0.toFixed(1)+' &rarr; <span '+
 'class="'+(db>0?'g':'r2')+'">'+b1.toFixed(1)+
 '</span></div><div class=lbl>'+(db>0?'+':'')+
 db.toFixed(2)+' per week</div></div></div>'+
 '<div class="vd '+cls+'">'+msg+'</div>'+
 '<div class=lbl style="margin-top:18px">your week by '+
 'week change</div><div class=wk>'+wks+'</div>';
 document.getElementById('res').innerHTML=h;}
opts(document.getElementById('ta'),D.my_roster_id);
let other=D.rosters[0].roster_id;
D.rosters.forEach(t=>{
 if(t.roster_id!=D.my_roster_id&&other==D.my_roster_id)
  other=t.roster_id;});
if(other==D.my_roster_id)other=D.rosters[1].roster_id;
opts(document.getElementById('tb'),other);
draw();
"""

HTML = """<!doctype html><html><head><meta charset=utf-8>
<title>Trade Calculator</title><style>__CSS__</style>
</head><body><div class=wrap>
<h1>Trade Calculator</h1>
<div class=sub>click players on either side to build a
trade &middot; values are starting-lineup points per
week</div>
<div class=two>
<div class=card><div class=hd>
<select id=ta onchange=draw()></select></div>
<div id=la></div></div>
<div class=card><div class=hd>
<select id=tb onchange=draw()></select></div>
<div id=lb></div></div></div>
<div class=res id=res></div></div>
<script>__JS__</script></body></html>"""

out = (HTML.replace("__CSS__", CSS)
       .replace("__JS__", JS.replace("__DATA__",
                                     json.dumps(D))))
open("site/trade.html", "w").write(out)
print("wrote site/trade.html %d KB" % (len(out) // 1024))

p = "112_ui_v4.py"
s = open(p).read()
if 'src="trade.html"' in s:
    print("already wired")
else:
    a = '<section id="trades"></section>'
    if a not in s:
        print("skip inline wiring: no trades section in shell (iframe mode)")
        raise SystemExit(0)
    s = s.replace(a, '<section id="trades">'
                  '<iframe src="trade.html" '
                  'style="width:100%;height:1700px;'
                  'border:0"></iframe></section>', 1)
    open(p, "w").write(s)
    print("wired trade.html into Trades tab")
