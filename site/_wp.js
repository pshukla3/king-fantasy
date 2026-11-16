var WP=null;
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
