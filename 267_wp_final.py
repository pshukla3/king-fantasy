import json

W = json.load(open("site/_wp.json"))
ot = W.get("ot", {})
ot.pop("up 1-3", None)
fp = ot.get("first_poss_tied", {})
W["ot"] = ot
W["active"] = {"pregame": "pregame", "ingame": "mkt2",
               "ot_first_poss": fp.get("p"),
               "ot_ci": fp.get("ci")}
W["notes"] = {
    "pregame": "logistic on the closing line, 3018"
               " games, worst bucket gap 0.031",
    "ingame": "12 features incl spread x time, walk"
              "-forward 0.4599 over 5 seasons",
    "ot": "empirical, %s games, wide CI - show as a"
          " range" % fp.get("n"),
    "espn_sign": "ESPN spread is NEGATIVE when home is"
                 " favored; ours is positive. negate."}
json.dump(W, open("site/_wp.json", "w"), indent=1)
print("site/_wp.json finalised")
for k, v in W["active"].items():
    print("  %-16s %s" % (k, v))

JS = """var WP=null;
function wpInit(j){WP=j;}
function _sg(z){return 1/(1+Math.exp(
 -Math.max(-30,Math.min(30,z))));}
function wpSpread(espn,posIsHome){
 var homePos=-espn;
 return posIsHome?homePos:-homePos;}
function wpPre(sp){
 var p=WP.pregame;
 return _sg(p.intercept+p.coef*sp);}
function wpFeat(o){
 var t=Math.max(1,o.t||1),sp=o.sp||0;
 return {sd_t:(o.sd||0)/Math.sqrt(t/60+1),
  expt:Math.exp(-4*t/3600),
  score_differential:o.sd||0,t:t,
  half:t<=1800?t:t-1800,
  down:o.down||1,ydstogo:o.dist||10,
  yardline_100:(o.y2e==null?50:o.y2e),
  to_diff:0,is4:(o.down===4?1:0),
  spread_pos:sp,sp_t:sp*(t/3600)};}
function wpLive(o){
 var m=WP.mkt2,z=m.intercept,f=wpFeat(o),i;
 for(i=0;i<m.feat.length;i++)
  z+=((f[m.feat[i]]-m.mean[i])/m.scale[i])*m.coef[i];
 return _sg(z);}
function wpOT(){
 var a=WP.active;
 return {p:a.ot_first_poss,ci:a.ot_ci};}
function wpAny(s){
 if(s.phase==='pre')return wpPre(s.sp||0);
 if(s.phase==='ot')return wpOT().p;
 return wpLive(s);}
"""
open("site/_wp.js", "w").write(JS)
print("\nwrote site/_wp.js (%d bytes)" % len(JS))
print("  wpSpread() is the ONLY place the ESPN sign")
print("  flip lives - everything else calls through it")
