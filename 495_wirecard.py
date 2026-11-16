s = open("vaporai.html").read()

# the old card also defines window.KFcard and loads LATER
# in the document, so it clobbers ours. Retire it.
_old = '<script src="_card.js"></script>'
if _old in s:
    s = s.replace(_old, '', 1)
    print("retired _card.js")

# 1. load _card2.js AFTER _card.js so the new object wins
old = '<script src="_card.js"></script>'
new = ('<script src="_card.js"></script>'
       '<script src="_card2.js"></script>')
if '_card2.js' not in s:
    assert s.count(old) == 1, "card.js tag"
    s = s.replace(old, new, 1)
    print("added _card2.js after _card.js")
else:
    print("_card2.js already loaded")

# 2. repoint the universal entry point at the new card.
#    Every click in rankings / my team / matchup / waivers /
#    scores / trade / mock already calls openCard(id), so
#    overriding it here catches all of them at once.
MARK = "/*KFCARD2*/"
# strip any previous block so edits actually take effect
_i = s.find("<script>" + MARK)
if _i >= 0:
    _j = s.find("</script>", _i)
    if _j > 0:
        s = s[:_i] + s[_j + len("</script>"):]
        print("stripped previous KFCARD2 block")
if MARK not in s:
    blk = ("<script>" + MARK + """
(function(){
 function go(id){
  if(window.KFcard2&&typeof window.KFcard2.open==="function"){
   window.KFcard2.open(id);return true;}
  return false;}
 var tries=0;
 function wire(){
  if(window.KFcard2&&typeof window.KFcard2.open==="function"){
   window.openCard=function(id){go(id)};
   window.KFopen=window.openCard;
   return;}
  if(tries++<40)setTimeout(wire,120);}
 wire();
 // iframes post up to the parent
 window.addEventListener("message",function(e){
  if(e.data&&e.data.kfcard)go(e.data.kfcard);});
 // delegated: any element carrying data-pid opens the card
 document.addEventListener("click",function(e){
  var t=e.target;
  while(t&&t!==document.body){
   var id=t.getAttribute&&t.getAttribute("data-pid");
   if(id){e.preventDefault();go(id);return;}
   t=t.parentNode;}
 },true);
 var _s=document.createElement("style");
 _s.textContent="[data-pid]{cursor:pointer}";
 document.head.appendChild(_s);
})();
</script>""")
    anc = "</script></body></html>"
    assert s.count(anc) >= 1, "tail anchor"
    i = s.rfind(anc)
    s = s[:i + len("</script>")] + blk + s[i + len("</script>"):]
    print("openCard repointed at KFcard.open")
else:
    print("already wired")

open("vaporai.html", "w").write(s)
print("vaporai.html ->", len(s), "bytes")
