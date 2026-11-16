import re

JS = r'''(function(){
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
})();'''

open("site/_connect.js", "w").write(JS)
print("wrote site/_connect.js (" + str(len(JS)) + " bytes)")

SEC = ('<section id="lgsync"><div class="pg">'
       '<h2>Sync a League</h2>'
       '<p class="sub">Connect a league from Sleeper, '
       'ESPN or Yahoo. Stored in your browser only.</p>'
       '<div class="kfform">'
       '<select id="kfpf">'
       '<option value="sleeper">Sleeper</option>'
       '<option value="espn">ESPN</option>'
       '<option value="yahoo">Yahoo</option>'
       '</select>'
       '<input id="kfid" placeholder="League ID, league '
       'URL, or Sleeper username">'
       '<button id="kfgo">Connect</button>'
       '</div><div id="kfmsg" class="kfm"></div>'
       '<div id="kflist"></div>'
       '<div id="kfprev"></div>'
       '</div></section>')

CSS = ('<style>'
       '.kfform{display:flex;gap:8px;flex-wrap:wrap;'
       'margin:14px 0}'
       '.kfform select,.kfform input{padding:9px 11px;'
       'border-radius:8px;border:1px solid #333;'
       'background:#111;color:#eee;font-size:14px}'
       '.kfform input{flex:1;min-width:230px}'
       '.kfform button{padding:9px 18px;border-radius:8px;'
       'border:0;background:#c9a227;color:#111;'
       'font-weight:700;cursor:pointer}'
       '.kfm{min-height:18px;font-size:13px;margin:6px 0}'
       '.kfm.ok{color:#7fd67f}.kfm.bad{color:#e57373}'
       '.kfrow{display:flex;align-items:center;gap:8px;'
       'padding:9px 11px;border:1px solid #2a2a2a;'
       'border-radius:8px;margin:6px 0;flex-wrap:wrap}'
       '.kfrow.on{border-color:#c9a227}'
       '.kfpill{font-size:10px;text-transform:uppercase;'
       'letter-spacing:.5px;padding:2px 7px;'
       'border-radius:99px;background:#2a2a2a;color:#bbb}'
       '.kfsub{color:#888;font-size:12px}'
       '.kfbtns{margin-left:auto;display:flex;gap:6px}'
       '.kfact{color:#c9a227;font-size:11px;'
       'font-weight:700;align-self:center}'
       '.kfrow button{padding:4px 11px;border-radius:6px;'
       'border:1px solid #444;background:transparent;'
       'color:#ccc;cursor:pointer;font-size:12px}'
       '.kft{width:100%;border-collapse:collapse;'
       'margin-top:10px;font-size:13px}'
       '.kft th,.kft td{padding:7px 9px;text-align:left;'
       'border-bottom:1px solid #222}'
       '.kft th{color:#888;font-size:11px;'
       'text-transform:uppercase;letter-spacing:.5px}'
       '.kfh{margin:18px 0 4px;font-size:16px}'
       '</style>')

H = open("vaporai.html").read()
n0 = len(H)

H = H.replace(SEC, "").replace(CSS, "")
TAG = '<script src="_connect.js"></script>'
H = H.replace(TAG, "")

NB = '<button data-ic="\u21c4" data-t="lgsync">Sync</button>'
H = H.replace(NB, "")

A = '<button data-ic="\u21c4" data-t="trades">Trades</button>'
assert H.count(A) == 1, "trades nav anchor"
H = H.replace(A, NB + A, 1)

B = '<section id="lgodds">'
assert H.count(B) == 1, "lgodds section anchor"
H = H.replace(B, SEC + B, 1)

C = "</script></body></html>"
assert H.count(C) == 1, "tail anchor"
H = H.replace(C, "</script>" + CSS + TAG + "</body></html>", 1)
# CSS must precede TAG so the tail still ends in
# </script></body></html> -- 114_theme.py needs it.
assert H.count(C) == 1, "tail anchor destroyed"

nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav " + str(nav)
assert H.count(SEC) == 1 and H.count(TAG) == 1
open("vaporai.html", "w").write(H)
print("vaporai.html " + str(n0) + " -> " + str(len(H)))
print("nav tabs: " + str(nav))
