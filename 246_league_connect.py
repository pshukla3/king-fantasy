import json
import pickle
import numpy as np

P = json.load(open("proj_by_sleeper_id.json"))
json.dump(P, open("site/_proj.json", "w"))
print("site/_proj.json  %d sleeper ids" % len(P))

SH = pickle.load(open("shocks.pkl", "rb"))
OUT = {}
rng = np.random.default_rng(3)
for k in SH:
    z = np.asarray(SH[k], dtype=np.float32)
    i = rng.integers(0, len(z), 1500)
    OUT[k] = [round(float(x), 3) for x in z[i]]
    print("  %-4s %5d -> 1500 | mean %.3f sd %.3f"
          % (k, len(z), np.mean(OUT[k]),
             np.std(OUT[k])))
json.dump(OUT, open("site/_shock.json", "w"))
print("site/_shock.json written")

CSS = """
body{margin:0;background:#0a0a0c;color:#e6e8ec;
font:13px/1.5 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,sans-serif}
.w{max-width:1080px;margin:0 auto;padding:18px}
h1{font-size:19px;letter-spacing:-.02em;margin:0 0 2px}
h2{font-size:10px;letter-spacing:.09em;font-weight:700;
text-transform:uppercase;color:#878c96;margin:20px 0 8px}
.dim{color:#878c96}
.bar{display:flex;gap:8px;margin:12px 0}
input,select,button{background:#16181d;color:#e6e8ec;
border:1px solid #24262d;border-radius:3px;
padding:7px 10px;font-size:13px;font-family:inherit}
input{flex:1;max-width:340px}
button{cursor:pointer;background:#c3c9d4;color:#0a0a0c;
font-weight:700;letter-spacing:.06em;
text-transform:uppercase;border-color:#c3c9d4}
#msg{color:#a8aeb9;margin:8px 0 4px}
.mc{display:flex;align-items:center;gap:14px;
background:#101115;border:1px solid #24262d;
border-radius:3px;padding:12px 14px;margin-bottom:8px}
.side{flex:1;min-width:0}
.side.r{text-align:right}
.tm{font-weight:600;font-size:14px}
.ow{color:#878c96;font-size:11px}
.pj{font-size:18px;font-weight:700;margin-top:2px}
.mid{width:190px}
.bw{height:6px;background:#24262d;border-radius:2px;
overflow:hidden;display:flex}
.bf{background:#c3c9d4;height:6px}
.pc{display:flex;justify-content:space-between;
font-size:11px;color:#878c96;margin-top:4px}
table{width:100%;border-collapse:collapse}
td{padding:7px 8px;border-bottom:1px solid #17191e}
td.r{text-align:right;color:#a8aeb9}
td.rk{color:#878c96;width:26px}
.note{color:#6f747d;font-size:11px;margin-top:14px;
line-height:1.6}
"""
js = open("site/_lg.js").read()
H = ("<!doctype html><html><head><meta charset=utf-8>"
     "<meta name=viewport content='width=device-width,"
     "initial-scale=1'><title>League</title><style>"
     + CSS + "</style></head><body><div class=w>"
     "<h1>Connect your league</h1>"
     "<div class=dim>Sleeper league ID or username &mdash;"
     " we pull your rosters and run the model on them."
     "</div>"
     "<div class=bar><input id=lid "
     "placeholder='1312181058833240064 or BabyShukla'>"
     "<button id=go>Load</button></div>"
     "<div id=msg></div>"
     "<h2>Matchups</h2>"
     "<select id=wk></select>"
     "<div id=mu style='margin-top:10px'></div>"
     "<h2>Projected standings</h2>"
     "<table><tbody id=sd></tbody></table>"
     "<div class=note>Win probability is a 1,200-run "
     "bootstrap per matchup drawing from measured "
     "per-position weekly shock pools (48,499 "
     "player-weeks). Lineups are the optimal legal "
     "start each week with byes removed. K and DST "
     "reuse the QB shock pool &mdash; their own weekly "
     "variance was never fit, so that part is an "
     "assumption.</div>"
     "</div><script>" + js + "</script></body></html>")
open("site/league.html", "w").write(H)
print("\nwrote site/league.html  %d KB" % (len(H) // 1024))

CSS2 = """
body{margin:0;background:#0a0a0c;color:#e6e8ec;
font:13px/1.5 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,sans-serif}
.w{max-width:1120px;margin:0 auto;padding:16px}
h1{font-size:19px;letter-spacing:-.02em;margin:0 0 2px}
h3{font-size:10px;letter-spacing:.09em;font-weight:700;
text-transform:uppercase;color:#878c96;margin:18px 0 6px}
h4{font-size:11px;letter-spacing:.08em;color:#c3c9d4;
margin:14px 0 4px;text-transform:uppercase}
.dim{color:#878c96;font-size:11px}
.bar{display:flex;gap:8px;margin:12px 0}
input,select,button{background:#16181d;color:#e6e8ec;
border:1px solid #24262d;border-radius:3px;
padding:7px 10px;font-size:13px;font-family:inherit}
input{flex:1;max-width:320px}
button{cursor:pointer}
#go{background:#c3c9d4;color:#0a0a0c;font-weight:700;
text-transform:uppercase;letter-spacing:.06em;
border-color:#c3c9d4}
#msg{color:#a8aeb9;margin:6px 0}
.tabs{display:flex;gap:6px;margin:14px 0;
flex-wrap:wrap;border-bottom:1px solid #24262d;
padding-bottom:12px}
.stab{background:#16181d;border:1px solid #24262d;
color:#878c96;border-radius:3px;padding:8px 16px;
cursor:pointer;font-size:11px;font-weight:700;
letter-spacing:.08em;text-transform:uppercase}
.stab.on{background:#c3c9d4;color:#0a0a0c;
border-color:#c3c9d4}
#app{display:none}
table{width:100%;border-collapse:collapse}
th{text-align:left;font-size:10px;color:#878c96;
letter-spacing:.08em;text-transform:uppercase;
padding:6px 7px;border-bottom:1px solid #24262d}
td{padding:7px;border-bottom:1px solid #17191e;
vertical-align:middle}
td.r,th.r{text-align:right}
td.sl{color:#878c96;font-size:10px;font-weight:700;
width:42px}
td.fc{width:34px}
.hs{width:28px;height:28px;border-radius:3px;
object-fit:cover;background:#16181d}
.av{width:34px;height:34px;border-radius:50%;
object-fit:cover;background:#16181d;display:inline-block}
.hd{display:flex;gap:10px;align-items:center;
margin-bottom:8px}
.tm{font-weight:600;font-size:14px}
.tot{margin-top:10px;padding-top:10px;
border-top:1px solid #24262d}
.mc{display:flex;align-items:center;gap:14px;
background:#101115;border:1px solid #24262d;
border-radius:3px;padding:12px 14px;margin-bottom:6px;
cursor:pointer}
.mc:hover{border-color:#c3c9d4}
.side{flex:1;min-width:0}
.side.r{text-align:right}
.pj{font-size:17px;font-weight:700}
.mid{width:170px}
.bw{height:6px;background:#24262d;border-radius:2px;
display:flex;overflow:hidden}
.bf{background:#c3c9d4;height:6px}
.pc{display:flex;justify-content:space-between;
font-size:11px;color:#878c96;margin-top:4px}
.det{background:#0d0e11;border:1px solid #24262d;
border-top:0;border-radius:0 0 3px 3px;padding:10px 14px;
margin:-6px 0 10px}
.cmp td{border-bottom:1px solid #17191e}
.cmp td.lft{text-align:right}
.cmp td.mid2{text-align:center;width:60px}
.two{display:grid;grid-template-columns:260px 1fr;
gap:22px}
@media(max-width:820px){.two{grid-template-columns:1fr}}
.gm{background:#101115;border:1px solid #24262d;
border-radius:3px;padding:9px 11px;margin-bottom:6px;
cursor:pointer}
.gr{display:flex;justify-content:space-between;
padding:2px 0}
"""
TABS = [("mu", "Matchup"), ("tm", "Team"),
        ("pl", "Players"), ("ar", "Around"),
        ("sc", "Scores")]
tb = "".join(
    '<div class="stab%s" data-s="%s" '
    'onclick="tab(\'%s\')">%s</div>'
    % (" on" if k == "mu" else "", k, k, v)
    for k, v in TABS)

js = open("site/_lg.js").read()
H = ("<!doctype html><html><head><meta charset=utf-8>"
     "<meta name=viewport content='width=device-width,"
     "initial-scale=1'><title>League</title><style>"
     + CSS2 + "</style></head><body><div class=w>"
     "<h1>Your league</h1>"
     "<div class=dim>Sleeper league ID or username</div>"
     "<div class=bar><input id=lid "
     "placeholder='league ID or username'>"
     "<button id=go>Load</button></div>"
     "<div id=msg></div>"
     "<div id=app><div class=tabs>" + tb + "</div>"
     "<div class=bar><select id=wk></select>"
     "<select id=pf><option value=''>All</option>"
     "<option>QB</option><option>RB</option>"
     "<option>WR</option><option>TE</option>"
     "<option>K</option><option>DEF</option></select>"
     "<input id=ps placeholder='find player'></div>"
     "<div id=body></div></div>"
     "<div class=dim style='margin-top:20px'>"
     "Matchup odds are a 1,000-run bootstrap per game "
     "from measured per-position weekly shock pools "
     "(48,499 player-weeks). Projections are our model, "
     "not Sleeper's. Live scores from ESPN; weekly "
     "fantasy points from Sleeper once games begin "
     "Sep 9.</div>"
     "</div><script>" + js + "</script></body></html>")
open("site/league.html", "w").write(H)
print("wrote site/league.html  %d KB" % (len(H) // 1024))
