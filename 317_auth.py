import re

SB_URL = "https://lnehxpyttfnsmotgaefo.supabase.co"
SB_KEY = "sb_publishable_ub7g0UZcRabItXx9376T9w_jX_6vA_U"

JS = ('(function(){\n'
      'var SB_URL="' + SB_URL + '";\n'
      'var SB_KEY="' + SB_KEY + '";\n' + r'''
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
})();''')
open("site/_auth.js", "w").write(JS)
print("wrote site/_auth.js (%d bytes)" % len(JS))

CSS = '''<style id="authcss">
#acct{margin-left:8px}
.acctb{background:transparent;border:1px solid
rgba(255,255,255,.18);color:#a6a9b2;border-radius:9px;
padding:7px 14px;font-size:12.5px;font-weight:600;
cursor:pointer;white-space:nowrap}
.acctb:hover{color:#fff;border-color:#fff}
.acctb.on{background:#fff;color:#0a0a0c;border-color:#fff}
#authov{display:none;position:fixed;inset:0;z-index:9900;
background:rgba(6,6,8,.9);align-items:center;
justify-content:center;padding:26px}
#authov.on{display:flex}
.authbx{position:relative;background:#131316;
border:1px solid rgba(255,255,255,.11);border-radius:16px;
padding:26px;max-width:420px;width:100%}
.authbx h3{margin:0 0 8px;font-size:19px;color:#fff}
.authp{color:#a6a9b2;font-size:13.5px;line-height:1.6;
margin:0 0 16px}
.authbx input[type=email]{width:100%;box-sizing:border-box;
background:#0b0b0e;border:1px solid rgba(255,255,255,.14);
border-radius:10px;padding:12px 14px;color:#f2f3f5;
font-size:15px;margin-bottom:12px}
.authbx input[type=email]:focus{border-color:#fff;outline:none}
.authck{display:flex;align-items:flex-start;gap:9px;
color:#a6a9b2;font-size:13px;line-height:1.5;
margin-bottom:12px;cursor:pointer}
.authck input{width:17px;height:17px;accent-color:#1668f0;
flex:0 0 auto;margin-top:1px}
.authgo{width:100%;border:0;border-radius:10px;padding:13px;
font-size:14px;font-weight:700;color:#fff;cursor:pointer}
.authmsg{color:#a6a9b2;font-size:12.5px;margin-top:11px;
line-height:1.5}
.authmsg.ok{color:#7fd7a1}
.authfine{color:#8f939c;font-size:11.5px;line-height:1.5;
margin:14px 0 0}
.authx{position:absolute;top:12px;right:14px;
background:rgba(255,255,255,.07);color:#a6a9b2;
border:1px solid rgba(255,255,255,.13);border-radius:8px;
padding:5px 11px;font-size:11px;cursor:pointer}
.authout{width:100%;margin-top:12px;background:none;
border:1px solid rgba(255,255,255,.14);color:#a6a9b2;
border-radius:10px;padding:11px;font-size:13px;cursor:pointer}
.authout:hover{color:#fff;border-color:#fff}
</style>'''

CDN = ('<script src="https://cdn.jsdelivr.net/npm/'
       '@supabase/supabase-js@2/dist/umd/supabase.js"></script>')
TAG = '<script src="_auth.js"></script>'

H = open("vaporai.html").read()
n0 = len(H)
H = re.sub(r'<style id="authcss">.*?</style>', "", H, flags=re.S)
H = H.replace(CDN, "").replace(TAG, "")
bl = list(re.finditer(r'<style id="[\w-]+">', H))
last = max(bl, key=lambda x: x.start())
j = H.index("</style>", last.start()) + 8
H = H[:j] + CSS + H[j:]
H = H.replace("</script></body></html>",
              "</script>" + CDN + TAG + "</body></html>", 1)
assert H.count('id="authcss"') == 1
assert H.count(TAG) == 1 and H.count(CDN) == 1
assert "</script></body></html>" in H, "tail broken"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav changed: %d" % nav
open("vaporai.html", "w").write(H)
print("auth wired | nav %d | %d -> %d bytes" % (nav, n0, len(H)))
