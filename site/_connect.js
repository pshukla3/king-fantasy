(function(){
var LS="kf_leagues", AC="kf_active";
function j(r){return r.json();}
function ld(){try{return JSON.parse(
 localStorage.getItem(LS)||"[]");}catch(e){return [];}}
function sv(a){try{localStorage.setItem(LS,
 JSON.stringify(a));}catch(e){}}
function act(){try{return localStorage.getItem(AC)||"";}
 catch(e){return "";}}
function setact(k){try{localStorage.setItem(AC,k);}
 catch(e){}}
function esc(s){return String(s==null?"":s)
 .replace(/&/g,"&amp;").replace(/</g,"&lt;")
 .replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function key(o){return o.pf+":"+o.id;}

function sleeper(id){
 var B="https://api.sleeper.app/v1/league/"+
  encodeURIComponent(id);
 return Promise.all([fetch(B).then(j),
  fetch(B+"/rosters").then(j),
  fetch(B+"/users").then(j)]).then(function(r){
  var L=r[0],R=r[1],U=r[2];
  if(!L||!L.league_id)throw new Error("league not found");
  var un={};
  (U||[]).forEach(function(u){
   un[u.user_id]=(u.metadata&&u.metadata.team_name)||
    u.display_name||"Team";});
  var T=(R||[]).map(function(x){
   var s=x.settings||{};
   return {id:x.roster_id,
    name:un[x.owner_id]||("Team "+x.roster_id),
    w:s.wins||0,l:s.losses||0,
    pf:(s.fpts||0)+((s.fpts_decimal||0)/100),
    pa:(s.fpts_against||0)+
       ((s.fpts_against_decimal||0)/100),
    n:(x.players||[]).length};});
  T.sort(function(a,b){return b.w-a.w||b.pf-a.pf;});
  return {pf:"sleeper",id:String(id),
   name:L.name||"League",season:String(L.season||""),
   slots:L.roster_positions||[],teams:T};});
}

function espn(id,yr){
 var u="/.netlify/functions/espn?league="+
  encodeURIComponent(id)+"&year="+(yr||"2026")+
  "&views=mTeam,mSettings";
 return fetch(u).then(j).then(function(d){
  if(d.error)throw new Error(d.hint||d.error);
  var st=d.settings||{};
  var T=(d.teams||[]).map(function(t){
   var r=(t.record&&t.record.overall)||{};
   var nm=t.name||((t.location||"")+" "+
    (t.nickname||"")).trim();
   return {id:t.id,name:nm||("Team "+t.id),
    w:r.wins||0,l:r.losses||0,
    pf:r.pointsFor||0,pa:r.pointsAgainst||0,
    n:((t.roster&&t.roster.entries)||[]).length};});
  T.sort(function(a,b){return b.w-a.w||b.pf-a.pf;});
  return {pf:"espn",id:String(id),
   name:st.name||"ESPN League",
   season:String(d.seasonId||yr||""),slots:[],teams:T};});
}

function yahoo(){
 return Promise.reject(new Error(
  "Yahoo needs OAuth. Register a developer app, then "+
  "set YAHOO_CLIENT_ID and YAHOO_CLIENT_SECRET in "+
  "Netlify. Not wired up yet."));
}

function slusr(name){
 var U="https://api.sleeper.app/v1/user/";
 return fetch(U+encodeURIComponent(name)).then(j)
  .then(function(u){
   if(!u||!u.user_id)throw new Error("no such user");
   return fetch(U+u.user_id+"/leagues/nfl/2026")
    .then(j);});
}

function load(pf,id){
 if(pf==="sleeper")return sleeper(id);
 if(pf==="espn")return espn(id);
 return yahoo();
}

function msg(t,bad){
 var e=document.getElementById("kfmsg");
 if(!e)return;
 e.className=bad?"kfm bad":"kfm ok";
 e.innerHTML=esc(t);
}

function add(o){
 var a=ld(),k=key(o),f=false;
 for(var i=0;i<a.length;i++){
  if(key(a[i])===k){a[i]=o;f=true;}}
 if(!f)a.push(o);
 sv(a);setact(k);draw();
}

function rm(k){
 var a=ld().filter(function(x){return key(x)!==k;});
 sv(a);
 if(act()===k)setact(a.length?key(a[0]):"");
 draw();
}

function preview(o){
 if(!o||!o.teams||!o.teams.length)return "";
 var h='<h3 class="kfh">'+esc(o.name)+
  ' <span class="kfpill">'+esc(o.pf)+'</span>'+
  ' <span class="kfsub">'+o.teams.length+
  ' teams'+(o.season?" &middot; "+esc(o.season):"")+
  '</span></h3>';
 h+='<table class="kft"><tr><th>#</th><th>Team</th>'+
  '<th>W-L</th><th>PF</th><th>PA</th>'+
  '<th>Players</th></tr>';
 o.teams.forEach(function(t,i){
  h+='<tr><td>'+(i+1)+'</td><td>'+esc(t.name)+
   '</td><td>'+t.w+'-'+t.l+'</td><td>'+
   t.pf.toFixed(1)+'</td><td>'+t.pa.toFixed(1)+
   '</td><td>'+t.n+'</td></tr>';});
 return h+'</table>';
}

function draw(){
 var box=document.getElementById("kflist");
 if(!box)return;
 var a=ld(),k=act();
 if(!a.length){
  box.innerHTML='<p class="kfsub">No leagues '+
   'connected yet. Add one above.</p>';
 }else{
  var h='';
  a.forEach(function(o){
   var kk=key(o),on=kk===k;
   h+='<div class="kfrow'+(on?" on":"")+'">'+
    '<span class="kfpill">'+esc(o.pf)+'</span> '+
    '<b>'+esc(o.name)+'</b> '+
    '<span class="kfsub">'+o.teams.length+
    ' teams</span>'+
    '<span class="kfbtns">'+
    (on?'<span class="kfact">ACTIVE</span>':
     '<button data-k="'+esc(kk)+'" '+
     'class="kfuse">Use</button>')+
    '<button data-k="'+esc(kk)+'" '+
    'class="kfrm">Remove</button></span></div>';});
  box.innerHTML=h;
 }
 var p=document.getElementById("kfprev");
 if(p){
  var cur=null;
  a.forEach(function(o){if(key(o)===k)cur=o;});
  p.innerHTML=cur?preview(cur):"";
 }
}

function mount(){
 var s=document.getElementById("lgsync");
 if(!s)return;
 s.addEventListener("click",function(e){
  var t=e.target;
  if(t.classList.contains("kfrm")){
   rm(t.getAttribute("data-k"));return;}
  if(t.classList.contains("kfuse")){
   setact(t.getAttribute("data-k"));draw();return;}
  if(t.id==="kfgo"){
   var pf=document.getElementById("kfpf").value;
   var v=(document.getElementById("kfid").value||"")
    .trim();
   if(!v){msg("Enter a league ID.",1);return;}
   msg("Loading\u2026");
   var m=v.match(/(\d{6,})/);
   var id=m?m[1]:v;
   if(pf==="sleeper"&&!/^\d{6,}$/.test(id)){
    slusr(v).then(function(ls){
     if(!ls||!ls.length)
      throw new Error("no 2026 leagues for that user");
     msg("Found "+ls.length+" league(s). Loading "+
      (ls[0].name||"first")+"\u2026");
     return sleeper(ls[0].league_id);})
     .then(function(o){add(o);
      msg("Connected: "+o.name);})
     .catch(function(er){msg(er.message,1);});
    return;
   }
   load(pf,id).then(function(o){
    add(o);msg("Connected: "+o.name);})
    .catch(function(er){msg(er.message,1);});
  }
 });
 draw();
}
if(document.readyState!=="loading")mount();
else document.addEventListener("DOMContentLoaded",mount);
})();