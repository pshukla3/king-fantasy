import json
import re

D = json.load(open("site/_tfind.json"))
T = D.get("trades", [])
rows = ""
for o in T:
    rows += ('<tr><td><b>%s</b></td>'
             '<td class="g">%s</td><td class="r">%s</td>'
             '<td class="n">+%.2f</td>'
             '<td class="n d">+%.2f</td></tr>'
             % (o["own"], " + ".join(o["give"]),
                " + ".join(o["get"]), o["gm"], o["gt"]))
if not rows:
    rows = ('<tr><td colspan="5">Nothing clears both bars '
            'right now.</td></tr>')

HTML = ('<section id="tfind"><div class="pg">'
        '<h2>Trade Finder</h2>'
        '<p class="sub">Every swap is scored twice: your '
        'gain by <b>our projections</b>, their gain by '
        '<b>market consensus</b>. Only trades where both '
        'are positive appear &mdash; the ones you win '
        'and they still accept. Gains are starting-lineup '
        'points per week, capped at three per team.</p>'
        '<table class="tf"><tr><th>Team</th>'
        '<th>You give</th><th>You get</th>'
        '<th>You gain</th><th>They gain</th></tr>'
        + rows + '</table></div></section>')

H = open("vaporai.html").read()
n0 = len(H)
m = re.search(r'<section id="tfind"[^>]*>', H)
assert m, "no tfind section"
rx = re.compile(r"</?section\b", re.I)
d, k = 0, m.start()
while True:
    mm = rx.search(H, k)
    if H[mm.start():mm.start() + 2] == "</":
        d -= 1
        if d == 0:
            en = H.index(">", mm.start()) + 1
            break
    else:
        d += 1
    k = mm.end()
H = H[:m.start()] + HTML + H[en:]
assert "</script></body></html>" in H, "tail broken"
assert len(H) > n0 * 0.9
open("vaporai.html", "w").write(H)
print("tfind page written: %d trades" % len(T))
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
