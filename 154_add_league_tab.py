p = "112_ui_v4.py"
s = open(p).read()

a1 = '<button data-t="calc">My Team</button>'
a2 = '<section id="calc"></section>'
assert a1 in s, "nav anchor not found"
assert a2 in s, "section anchor not found"

if 'data-t="league"' in s:
    print("league tab already present")
else:
    b1 = a1 + '\n<button data-t="league">League</button>'
    b2 = (a2 + '\n<section id="league">'
          '<iframe src="league.html" '
          'style="width:100%;height:2200px;border:0;'
          'background:transparent"></iframe></section>')
    s = s.replace(a1, b1, 1).replace(a2, b2, 1)
    open(p, "w").write(s)
    print("added League nav button + section")

t = open(p).read()
print("nav buttons now:")
import re
for m in re.finditer(r'data-t="([a-z]+)"[^>]*>([^<]+)<', t):
    print("  %-10s %s" % (m.group(1), m.group(2)))
