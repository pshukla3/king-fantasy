import json
import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce").fillna(0)
B["adp"] = pd.to_numeric(B["adp"], errors="coerce")
B["ar"] = B["adp"].rank(method="min")
B = B.sort_values("rank")

def num(v, d=2):
    try:
        if v != v:
            return None
        return round(float(v), d)
    except Exception:
        return None

def txt(v):
    return "" if v != v else str(v)

rows = []
for _, r in B.iterrows():
    rows.append({
        "rk": int(r["rank"]),
        "nm": txt(r["player_display_name"]),
        "tm": txt(r["team"]),
        "ps": txt(r["position"]),
        "pr": int(r["pos_rank"]),
        "by": int(r["bye"]) if "bye" in r and r["bye"] == r["bye"] else 0,
        "pp": num(r["pp"], 2),
        "sz": num(r["pp"] * 17.0, 0),
        "vp": num(r["vorp"], 2),
        "ad": num(r["adp"], 1),
        "sa": num(r.get("sadp"), 1),
        "ea": num(r.get("eadp"), 1),
        "ar": num(r["ar"], 0),
        "st": txt(r["status"]),
        "id": txt(r["player_id"])})

HEAD = ("<tr><th>RK</th><th class=l>PLAYER</th>"
        "<th class=l>POS</th><th>BYE</th><th>PPG</th>"
        "<th>SEASON</th><th>VORP</th><th>ADP</th>"
        "<th>SLEEPER</th><th>ESPN</th><th>EDGE</th></tr>")
SEL = ("<select id=p><option value=''>All positions</option>"
       "<option>QB</option><option>RB</option>"
       "<option>WR</option><option>TE</option>"
       "<option>K</option><option>DST</option></select>")

css = open("site/_rank.css").read()
js = open("site/_rank.js").read().replace(
    "__DATA__", json.dumps(rows), 1)

H = ("<!doctype html><html><head><meta charset=utf-8>"
     "<meta name=viewport content='width=device-width,"
     "initial-scale=1'><title>KING Fantasy Rankings</title>"
     "<style>" + css + "</style></head><body><div class=wrap>"
     "<h1>2026 Rankings</h1><div class=sub>"
     "Ranked by value over replacement in your 10-team full-PPR "
     "league. ADP is the average of Sleeper and ESPN. EDGE is "
     "market rank minus ours &mdash; positive means we like the "
     "player more than the market. Injured and out players "
     "project zero.</div><div class=bar>"
     "<input id=q placeholder='Search player or team'>"
     + SEL + "<span class=cnt id=cnt></span></div>"
     "<table><thead>" + HEAD + "</thead><tbody id=tb>"
     "</tbody></table></div><script>" + js
     + "</script></body></html>")
open("site/rankings.html", "w").write(H)
print("wrote site/rankings.html  %d KB" % (len(H) // 1024))
print("rows %d | with ADP %d | zeroed %d"
      % (len(rows),
         sum(1 for x in rows if x["ad"] is not None),
         sum(1 for x in rows if not x["pp"])))

p = "112_ui_v4.py"
s = open(p).read()
a = '<button data-t="board">Rankings</button>'
if 'src="rankings.html"' in s:
    print("rankings tab already wired")
elif a in s:
    s = s.replace(a, a + '<button data-t="rank">Board</button>',
                  1)
    s = s.replace('<section id="board"></section>',
                  '<section id="board"></section>\n'
                  '<section id="rank"><iframe '
                  'src="rankings.html" style="width:100%;'
                  'height:2400px;border:0"></iframe></section>',
                  1)
    open(p, "w").write(s)
    print("added Board tab -> rankings.html")
else:
    print("nav anchor not found - page built but not wired")
