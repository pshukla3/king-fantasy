import re, time

s = open("vaporai.html").read()
stamp = str(int(time.time()))
# refresh any existing stamp, add one where missing
s = re.sub(r'(data-src|src)="([a-z0-9_]+\.html)(\?v=\d+)?"',
           lambda m: '%s="%s?v=%s"' % (m.group(1), m.group(2),
                                       stamp), s)
# the data files the pages fetch, too
for f in ("_board.json", "_cards.json", "_projweek.json",
          "_card2.js", "_rankhist.json"):
    s = s.replace('"%s"' % f, '"%s?v=%s"' % (f, stamp))
open("vaporai.html", "w").write(s)
n = len(re.findall(r'\?v=' + stamp, s))
print("cache stamp %s applied to %d references" % (stamp, n))
