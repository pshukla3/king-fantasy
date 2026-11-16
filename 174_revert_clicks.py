p = "112_ui_v4.py"
s = open(p).read()
n = s.count("pl(x.id,x.nm)")
s = s.replace("pl(x.id,x.nm)", "E(x.nm)")
i = s.find("\nwindow.openCard=function(id){")
j = s.find("function pl(id,nm){")
if i >= 0 and j > i:
    k = s.find("</a>';}", j)
    k = s.find("\n", k) + 1 if k > 0 else -1
    if k > 0:
        s = s[:i] + "\n" + s[k:]
        print("removed injected openCard + pl block")
    else:
        print("WARNING: could not find end of pl()")
else:
    print("injected block not found")
open(p, "w").write(s)
print("reverted %d clickable name cells" % n)
print("openCard left: %d | pl( left: %d"
      % (s.count("window.openCard"), s.count("pl(x.id")))
