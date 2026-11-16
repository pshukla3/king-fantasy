import glob, os

SHIM = """<script>/*KFSHIM*/
(function(){
 function up(id){
  try{
   if(window.parent&&window.parent!==window){
    window.parent.postMessage({kfcard:String(id)},"*");
    return true;}
  }catch(e){}
  return false;}
 var prev=window.openCard;
 window.openCard=function(id){
  if(up(id))return;
  if(typeof prev==="function")prev(id);
  else if(window.KFcard2)window.KFcard2.open(id);};
 window.KFopen=window.openCard;
 // every player name already carries data-pid -- one
 // delegated listener covers rankings, search, my team
 document.addEventListener("click",function(e){
  var t=e.target;
  while(t&&t!==document.body){
   var id=t.getAttribute&&t.getAttribute("data-pid");
   if(id){e.preventDefault();window.openCard(id);return;}
   t=t.parentNode;}
 },true);
 var st=document.createElement("style");
 st.textContent="[data-pid]{cursor:pointer}"+
  "[data-pid]:hover{text-decoration:underline;color:#4FB3E8}";
 document.head.appendChild(st);
})();
</script>"""

n = 0
for f in sorted(glob.glob("site/*.html")):
    if f.endswith("index.html"):
        continue
    s = open(f).read()
    if "KFSHIM" in s:
        continue
    if ("data-pid" not in s and "openCard" not in s
            and "KFopen" not in s):
        continue
    if "</body>" in s:
        s = s.replace("</body>", SHIM + "</body>", 1)
    else:
        s = s + SHIM
    open(f, "w").write(s)
    n += 1
    print("  shimmed %s" % os.path.basename(f))
print("shim added to %d pages" % n)
