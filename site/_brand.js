(function(){
function boot(){
 var sb=document.querySelector(".scorebar");
 if(!sb){setTimeout(boot,250);return;}
 if(document.getElementById("kbrand"))return;
 var d=document.createElement("div");
 d.id="kbrand";
 d.innerHTML='<span class="kbtx"><b>KING</b><i>Fantasy</i></span>';
 sb.insertBefore(d,sb.firstChild);
 d.onclick=function(){
  var b=document.querySelector('nav button[data-t="home"]');
  if(b)b.click();};}
if(document.readyState==="loading"){
 document.addEventListener("DOMContentLoaded",boot);}
else{setTimeout(boot,200);}})();