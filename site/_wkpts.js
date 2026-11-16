
// Projected before a week, final after it. Actuals come
// from Sleeper stats scored with the league's own rules;
// projections come from _wkproj.json, which is frozen at
// write time so a rebuild can never rewrite what we
// claimed to predict.
(function(){
if(window.KFwkReady)return;
window.KFwkReady=1;

var PROJ=null,ACT={},LOADING={};

function norm(s){return String(s||"").toLowerCase()
 .replace(/[^a-z ]/g,"").replace(/\s+/g," ").trim().replace(/ (jr|sr|iii|ii|iv|v)$/,"");}

function cur(){
 var A=Date.UTC(2026,8,8);
 var d=Math.floor((Date.now()-A)/604800000)+1;
 return Math.max(1,Math.min(18,d));
}
function isFinal(wk){return Number(wk)<cur();}

function key(p){
 var pos=String(p.pos||"");
 if(pos==="DEF"||pos==="DST")return String(p.tm||p.pid||"");
 return p.k||norm(p.n);
}

function loadProj(){
 if(PROJ)return Promise.resolve(PROJ);
 return fetch("_wkproj.json")
  .then(function(r){return r.json();})
  .then(function(d){PROJ=d||{};return PROJ;})
  .catch(function(){PROJ={};return PROJ;});
}

function loadAct(wk){
 wk=String(wk);
 if(ACT[wk])return Promise.resolve(ACT[wk]);
 if(LOADING[wk])return LOADING[wk];
 LOADING[wk]=fetch("https://api.sleeper.app/v1/stats/nfl/"
   +"regular/2026/"+wk)
  .then(function(r){return r.json();})
  .then(function(d){
   var m={};
   return new Promise(function(res){
    KFscore.ready(function(){
     fetch("_pmap.json").then(function(r){return r.json();})
      .then(function(pm){
       Object.keys(d||{}).forEach(function(pid){
        var info=pm[pid]||{};
        var pts=KFscore.score(d[pid]);
        var kk;
        if(/^TEAM_/.test(pid))return;
        if(info.p==="DEF"||info.p==="DST")
         kk=String(info.t||pid);
        else kk=norm(info.n||"");
        if(kk)m[kk]=pts;
       });
       ACT[wk]=m;res(m);
      }).catch(function(){ACT[wk]=m;res(m);});
    });
   });
  }).catch(function(){ACT[wk]={};return ACT[wk];});
 return LOADING[wk];
}

function load(wk){
 var jobs=[loadProj()];
 if(isFinal(wk)||Number(wk)===cur())jobs.push(loadAct(wk));
 return Promise.all(jobs);
}

// actual points, only for a week that has finished
function actual(p,wk){
 if(!isFinal(wk))return null;
 var m=ACT[String(wk)];
 if(!m)return null;
 var v=m[key(p)];
 return (v==null)?null:v;
}
// what we projected before that week kicked off
function frozen(p,wk){
 if(!PROJ)return null;
 var m=PROJ[String(wk)];
 if(!m)return null;
 var v=m[key(p)];
 return (v==null)?null:v;
}

window.KFwk={cur:cur,isFinal:isFinal,load:load,
 actual:actual,frozen:frozen,key:key};
})();
