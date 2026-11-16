import re

NAV = ("<nav>\n"
       '<button class="on" data-t="home">Home</button>\n'
       '<button data-t="league">League</button>\n'
       '<button data-t="mock">Mock_Draft</button>\n'
       '<button data-t="rank">Rankings</button>\n'
       '<button data-t="news">News</button>\n'
       '<button data-t="trades">Trades</button>\n'
       '<button data-t="calc">My Team</button>\n'
       '<button data-t="rosters">Rosters</button>\n'
       "</nav>")

p = "vaporai.html"
s = open(p).read()
print("before: %d KB" % (len(s) // 1024))
m = re.search(r"<nav>.*?</nav>", s, re.S)
assert m, "nav block not found"
old = re.findall(r'data-t="([a-z]+)"[^>]*>([^<]+)<',
                 m.group(0))
print("old nav: %s" % [a for a, _ in old])
s = s[:m.start()] + NAV + s[m.end():]

s2, n = re.subn(r'<section id="teams">.*?</section>',
                '<section id="teams"></section>',
                s, flags=re.S)
print("emptied My League iframe: %d" % n)
s = s2

a = '<section id="rosters"></section>'
if 'id="mock"' in s:
    print("mock section already present")
elif a in s:
    s = s.replace(a, a + '\n<section id="mock">'
                  '<iframe src="mock.html" '
                  'style="width:100%;height:3200px;'
                  'border:0"></iframe></section>', 1)
    print("added mock section")
else:
    raise SystemExit("rosters anchor missing")

open(p, "w").write(s)
t = open(p).read()
print("\nnew nav:")
for k, v in re.findall(r'data-t="([a-z]+)"[^>]*>([^<]+)<',
                       re.search(r"<nav>.*?</nav>",
                                 t, re.S).group(0)):
    print("  %-8s %s" % (k, v))
print("\nsections: %s"
      % re.findall(r'<section[^>]*id="([a-z]+)"', t))
