(function(){
var SB_URL="https://lnehxpyttfnsmotgaefo.supabase.co";
var SB_KEY="sb_publishable_ub7g0UZcRabItXx9376T9w_jX_6vA_U";

var sb=null,USER=null;
function q(i){return document.getElementById(i);}
function esc(s){return String(s==null?"":s).replace(
 /[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",
 ">":"&gt;",'"':"&quot;"}[c];});}
function client(){
 if(sb)return sb;
 if(!window.supabase||!window.supabase.createClient)return null;
 sb=window.supabase.createClient(SB_URL,SB_KEY);
 return sb;}
function chip(){
 var bar=q("subbar");
 if(!bar){setTimeout(chip,300);return;}
 var old=q("acct");
 if(old)old.parentNode.removeChild(old);
 var d=document.createElement("div");
 d.id="acct";
 d.innerHTML=USER
  ?'<button id="acctBtn" class="acctb on">'
   +esc((USER.email||"").split("@")[0])+'</button>'
  :'<button id="acctBtn" class="acctb">Sign in</button>';
 bar.appendChild(d);
 q("acctBtn").onclick=function(){
  if(USER){prefs();}else{signin();}};
 railOut();}
function railOut(){
 var rail=q("rail");
 if(!rail){setTimeout(railOut,300);return;}
 var old=q("railOut");
 if(old)old.parentNode.removeChild(old);
 if(!USER)return;
 var b=document.createElement("button");
 b.id="railOut";b.className="railout";
 b.innerHTML='<i>\u23FB</i><span>Sign out</span>';
 var lg=rail.querySelector(".lg");
 if(lg&&lg.nextSibling){rail.insertBefore(b,lg.nextSibling);}
 else{rail.appendChild(b);}
 b.onclick=function(){
  var c=client();
  if(c)c.auth.signOut().then(function(){location.reload();});};}
function railOut(){
 var rail=q("rail");
 if(!rail){setTimeout(railOut,300);return;}
 var old=q("railOut");
 if(old)old.parentNode.removeChild(old);
 if(!USER)return;
 var b=document.createElement("button");
 b.id="railOut";b.className="railout";
 b.innerHTML='<i>\u23FB</i><span>Sign out</span>';
 var lg=rail.querySelector(".lg");
 if(lg&&lg.nextSibling){rail.insertBefore(b,lg.nextSibling);}
 else{rail.appendChild(b);}
 b.onclick=function(){
  var c=client();
  if(c)c.auth.signOut().then(function(){location.reload();});};}
function modal(html){
 var o=q("authov");
 if(!o){o=document.createElement("div");o.id="authov";
  document.body.appendChild(o);
  o.addEventListener("click",function(e){
   if(e.target===o)o.className="";});}
 o.innerHTML='<div class="authbx"><button class="authx">'
  +'close</button>'+html+'</div>';
 o.className="on";
 o.querySelector(".authx").onclick=function(){o.className="";};
 return o;}
function signin(){
 modal('<h3>Sign in</h3><p class="authp">We email you a '
  +'one-time link. No password to remember, and none '
  +'stored.</p><input id="authEmail" type="email" '
  +'placeholder="you@example.com" autocomplete="email">'
  +'<label class="authck"><input type="checkbox" id="authOpt">'
  +' Email me weekly projections, injury alerts and trade '
  +'suggestions</label><button id="authGo" class="btn-blue '
  +'authgo">Send sign-in link</button>'
  +'<div id="authMsg" class="authmsg"></div>'
  +'<p class="authfine">Unsubscribe from any email in one '
  +'click. We only send what you tick above.</p>');
 q("authGo").onclick=function(){
  var c=client(),em=q("authEmail").value.trim(),m=q("authMsg");
  if(!em||em.indexOf("@")<0){m.textContent=
   "enter a valid email";return;}
  if(!c){m.textContent="auth library did not load";return;}
  try{localStorage.setItem("kf_optin",
   q("authOpt").checked?"1":"0");}catch(e){}
  m.textContent="sending...";
  c.auth.signInWithOtp({email:em,options:{
   emailRedirectTo:location.origin+location.pathname}})
  .then(function(r){
   if(r.error){m.textContent="could not send: "
    +r.error.message;return;}
   m.className="authmsg ok";
   m.textContent="Check "+em+" for your link. It expires in "
    +"an hour and may land in spam the first time.";})
  .catch(function(e){m.textContent="error: "+e.message;});};}
function prefs(){
 var c=client();
 if(!c)return;
 modal('<h3>Your account</h3><p class="authp">'
  +esc(USER.email||"")+'</p>'
  +'<label class="authck"><input type="checkbox" id="pW">'
  +' Weekly projections</label>'
  +'<label class="authck"><input type="checkbox" id="pI">'
  +' Injury alerts for your roster</label>'
  +'<label class="authck"><input type="checkbox" id="pT">'
  +' Trade suggestions</label>'
  +'<button id="pSave" class="btn-blue authgo">Save</button>'
  +'<div id="pMsg" class="authmsg"></div>'
  +'<button id="pOut" class="authout">Sign out</button>');
 c.from("email_prefs").select("*").eq("user_id",USER.id)
  .maybeSingle().then(function(r){
   var d=r.data||{};
   q("pW").checked=!!d.weekly_projections;
   q("pI").checked=!!d.injury_alerts;
   q("pT").checked=!!d.trade_suggestions;});
 q("pSave").onclick=function(){
  var any=q("pW").checked||q("pI").checked||q("pT").checked;
  var row={user_id:USER.id,
   weekly_projections:q("pW").checked,
   injury_alerts:q("pI").checked,
   trade_suggestions:q("pT").checked,
   updated_at:new Date().toISOString()};
  if(any){row.consented_at=new Date().toISOString();
   row.consent_source="account panel";
   row.unsubscribed_at=null;}
  else{row.unsubscribed_at=new Date().toISOString();}
  c.from("email_prefs").upsert(row).then(function(r){
   q("pMsg").className="authmsg ok";
   q("pMsg").textContent=r.error?("error: "+r.error.message)
    :"saved";});};
 q("pOut").onclick=function(){
  c.auth.signOut().then(function(){location.reload();});};}
function saveLeague(){
 var c=client();
 if(!c||!USER)return;
 var id="";
 try{id=localStorage.getItem("shukie_lg")||"";}catch(e){}
 if(!id)return;
 var L=[];
 try{L=JSON.parse(localStorage.getItem("shukie_lgs")||"[]");}
 catch(e){}
 var nm=(L.filter(function(x){
  return String(x.id)===String(id);})[0]||{}).name||"";
 c.from("user_leagues").upsert({user_id:USER.id,
  provider:"sleeper",league_id:String(id),name:nm,
  is_primary:true},{onConflict:"user_id,provider,league_id"})
  .then(function(){});}
function boot(){
 var c=client();
 if(!c){setTimeout(boot,400);return;}
 c.auth.getSession().then(function(r){
  USER=(r.data&&r.data.session&&r.data.session.user)||null;
  window.__kfAuthed=!!USER;
  chip();
  if(USER){var L=q("land");if(L)L.className="";}
  if(USER){saveLeague();
   var o="";
   try{o=localStorage.getItem("kf_optin")||"";}catch(e){}
   if(o==="1"){
    c.from("email_prefs").upsert({user_id:USER.id,
     weekly_projections:true,injury_alerts:true,
     trade_suggestions:true,
     consented_at:new Date().toISOString(),
     consent_source:"signup",
     updated_at:new Date().toISOString()}).then(function(){});
    try{localStorage.removeItem("kf_optin");}catch(e){}}}});
 c.auth.onAuthStateChange(function(ev,s){
  USER=(s&&s.user)||null;window.__kfAuthed=!!USER;chip();
  if(USER){var L2=q("land");if(L2)L2.className="";}
  if(USER)saveLeague();});}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",
  function(){setTimeout(boot,300);});}
else{setTimeout(boot,300);}
window.kfSignIn=signin;
})();