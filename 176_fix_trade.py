import re

p = "158_trade_page.py"
s = open(p).read()
pat = re.compile(
    r"(p\.pos\+'</span> '\+p\.name)"
    r"\+' <span class=pn.*?card</span>'"
    r"(\+'</span>)", re.S)
m = pat.search(s)
if m:
    s = pat.sub(r"\1\2", s, count=1)
    open(p, "w").write(s)
    print("removed broken card link from trade rows")
else:
    print("pattern not found - checking raw")
    i = s.find("class=pn onclick")
    print("  'class=pn onclick' at index %d" % i)
    if i > 0:
        print("  context: %s" % s[i - 120:i + 160])
print("oc( still present: %d" % s.count("function oc("))
print("class=pn left: %d" % s.count("class=pn"))
