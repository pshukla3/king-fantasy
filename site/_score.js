
// Exact league scoring. Sleeper publishes stat keys under
// the same names as scoring settings, so a player's score
// is simply the dot product of the two. No hardcoded PPR
// anywhere: distance-banded field goals, points-allowed
// and yards-allowed tiers, first downs and bonuses all
// fall out of this automatically for ANY league.
(function(){
if(window.KFscoreReady)return;
window.KFscoreReady=1;

var SET=null,WAIT=[];

var SKIP={pts_ppr:1,pts_std:1,pts_half_ppr:1,gp:1,
 gms_active:1,tm_def_snp:1,tm_off_snp:1,tm_st_snp:1};

function ready(fn){
 if(SET)fn(SET);else WAIT.push(fn);
}

fetch("_scoring.json").then(function(r){return r.json();})
 .then(function(d){
  SET=d||{};
  WAIT.forEach(function(f){f(SET);});WAIT=[];
 }).catch(function(){
  SET={};WAIT.forEach(function(f){f(SET);});WAIT=[];
 });

// points for one stat line
function score(st){
 if(!SET||!st)return 0;
 var t=0;
 for(var k in st){
  if(SKIP[k])continue;
  var w=SET[k];
  if(w)t+=w*st[k];
 }
 return t;
}

// itemised breakdown, biggest contribution first
function explain(st){
 var out=[];
 if(!SET||!st)return out;
 for(var k in st){
  if(SKIP[k])continue;
  var w=SET[k];
  if(w)out.push({k:k,v:st[k],w:w,p:w*st[k]});
 }
 out.sort(function(a,b){
  return Math.abs(b.p)-Math.abs(a.p);});
 return out;
}

var LABEL={
 pass_yd:"Passing yards",pass_td:"Passing TD",
 pass_int:"Interception",pass_2pt:"Passing 2PT",
 rush_yd:"Rushing yards",rush_td:"Rushing TD",
 rush_2pt:"Rushing 2PT",rec:"Reception",
 rec_yd:"Receiving yards",rec_td:"Receiving TD",
 rec_2pt:"Receiving 2PT",fum_lost:"Fumble lost",
 fum_rec:"Fumble recovery",fum_rec_td:"Fumble rec TD",
 fgm_0_19:"FG 0-19",fgm_20_29:"FG 20-29",
 fgm_30_39:"FG 30-39",fgm_40_49:"FG 40-49",
 fgm_50p:"FG 50+",fgmiss:"FG missed",
 xpm:"Extra point",xpmiss:"XP missed",
 def_td:"Defensive TD",st_td:"Special teams TD",
 def_st_td:"Def/ST TD",sack:"Sack",int:"Interception",
 ff:"Forced fumble",safe:"Safety",
 blk_kick:"Blocked kick",
 def_st_ff:"ST forced fumble",
 def_st_fum_rec:"ST fumble recovery",
 st_ff:"ST forced fumble",st_fum_rec:"ST fumble rec",
 pts_allow_0:"Shutout",pts_allow_1_6:"Allowed 1-6",
 pts_allow_7_13:"Allowed 7-13",
 pts_allow_14_20:"Allowed 14-20",
 pts_allow_21_27:"Allowed 21-27",
 pts_allow_28_34:"Allowed 28-34",
 pts_allow_35p:"Allowed 35+",
 yds_allow_0_100:"Under 100 yds",
 yds_allow_100_199:"100-199 yds",
 yds_allow_200_299:"200-299 yds",
 yds_allow_300_349:"300-349 yds",
 yds_allow_350_399:"350-399 yds",
 yds_allow_400_449:"400-449 yds",
 yds_allow_450_499:"450-499 yds",
 yds_allow_500_549:"500-549 yds",
 yds_allow_550p:"550+ yds"
};

window.KFscore={
 ready:ready,
 score:score,
 explain:explain,
 label:function(k){return LABEL[k]||k;},
 settings:function(){return SET||{};}
};
})();
