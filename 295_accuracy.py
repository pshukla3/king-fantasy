import json
import re

W = json.load(open("site/_wp.json"))

def g(k, f, d=None):
    return (W.get(k) or {}).get(f, d)

rows = ""
for key, lbl in [("state", "State only (no line)"),
                 ("mkt", "Market"),
                 ("mkt2", "Market + interaction")]:
    ll, br = g(key, "logloss"), g(key, "brier")
    wg = g(key, "worst_calib_gap")
    rows += ('<tr><td>%s</td><td class="n">%s</td>'
             '<td class="n">%s</td><td class="n">%s</td></tr>'
             % (lbl,
                "%.4f" % ll if ll else "&mdash;",
                "%.4f" % br if br else "&mdash;",
                "%.3f" % wg if wg else "&mdash;"))

QT = [("Q1", 2141, .5656, .5831), ("Q2", 2772, .4522, .4744),
      ("Q3", 2196, .3697, .3977), ("Q4", 2693, .2926, .3191)]
qr = ""
for q, n, a, b in QT:
    win = "w" if a < b else "l"
    qr += ('<tr><td>%s</td><td class="n">%d</td>'
           '<td class="n %s">%.4f</td><td class="n">%.4f</td>'
           '<td class="n %s">%+.1f%%</td></tr>'
           % (q, n, win, a, b, win, 100 * (b - a) / b))

HTML = ('<section id="acc"><div class="pg">'
        '<h2>Accuracy Report</h2>'
        '<p class="sub">Measured performance of the models '
        'behind this site, published in full including where '
        'they lose. Win probability is scored against ESPN '
        'on the same 9,802 plays from 60 completed games. '
        'Lower log loss is better.</p>'

        '<h3>Win probability vs ESPN</h3>'
        '<table class="tf"><tr><th>Model</th>'
        '<th>Log loss</th><th>Brier</th></tr>'
        '<tr><td>Shukie (market + interaction)</td>'
        '<td class="n w">0.4147</td>'
        '<td class="n w">0.1358</td></tr>'
        '<tr><td>ESPN</td><td class="n">0.4383</td>'
        '<td class="n">0.1428</td></tr>'
        '<tr><td>Drive Monte Carlo (rejected)</td>'
        '<td class="n">0.4326</td><td class="n">0.1407</td>'
        '</tr></table>'
        '<p class="note">The edge over ESPN is +0.0236 with '
        'a 95% confidence interval of &minus;0.0051 to '
        '+0.0530 (game-level bootstrap, 60 games). '
        '<b>That interval crosses zero, so this is not '
        'statistically significant.</b> Probability we are '
        'genuinely better: 0.943. The Monte Carlo simulator '
        'was built, scored, and rejected &mdash; the optimal '
        'blend weight came out at exactly zero.</p>'

        '<h3>By quarter</h3>'
        '<table class="tf"><tr><th>Quarter</th><th>Plays</th>'
        '<th>Shukie</th><th>ESPN</th><th>Edge</th></tr>'
        + qr + '</table>'
        '<p class="note">Calibration error (ECE) is 0.0536 '
        'for us against 0.0607 for ESPN. We are better '
        'calibrated in Q2, Q3 and Q4; ESPN is better in Q1.'
        '</p>'

        '<h3>Model selection, walk-forward by season</h3>'
        '<table class="tf"><tr><th>Variant</th>'
        '<th>Log loss</th><th>Brier</th>'
        '<th>Worst decile gap</th></tr>' + rows +
        '</table>'
        '<p class="note">Every choice was made on '
        'walk-forward validation across 5 held-out seasons, '
        'never in-sample. A gradient boosting model was '
        'tested and <b>lost</b> to the logistic (0.4988 vs '
        '0.4950), so the simpler model shipped. At kickoff '
        'the site uses a pure line model, which has the '
        'best pregame calibration gap of the three '
        '(0.031 vs 0.060 and 0.071).</p>'

        '<h3>What the models are built on</h3>'
        '<table class="tf"><tr><th>Source</th>'
        '<th>Size</th></tr>'
        '<tr><td>Play-by-play, 2015&ndash;2025</td>'
        '<td class="n">443,261 plays / 3,018 games</td></tr>'
        '<tr><td>Drive outcomes</td>'
        '<td class="n">66,529 drives</td></tr>'
        '<tr><td>Play-level state pool</td>'
        '<td class="n">444,814 plays</td></tr>'
        '<tr><td>Overtime, first possession tied</td>'
        '<td class="n">0.602 (CI 0.518&ndash;0.685)</td></tr>'
        '</table>'
        '<p class="note">Overtime uses an empirical table '
        'rather than a model, because 133 games is too few '
        'to fit one. The confidence interval is wide and '
        'shown here for that reason.</p>'
        '</div></section>')

H = open("vaporai.html").read()
n0 = len(H)
m = re.search(r'<section id="acc"[^>]*>', H)
assert m, "no acc section"
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
print("accuracy page written")
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
