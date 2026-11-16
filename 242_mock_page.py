import json
import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
B["ad"] = pd.to_numeric(B["adp"], errors="coerce")
B = B[B["pp"].fillna(0) > 0].sort_values("rank")
B = B.head(280)
P = []
for _, r in B.iterrows():
    a = r["ad"]
    by = r["bye"] if "bye" in r else 0
    P.append({"n": str(r["player_display_name"]),
              "p": str(r["position"]),
              "t": str(r["team"]),
              "b": int(by) if by == by else 0,
              "g": round(float(r["pp"]), 2),
              "v": round(float(r["vorp"]), 2),
              "a": round(float(a), 1) if a == a
                   else float(r["rank"]),
              "r": int(r["rank"]),
              "id": str(r["player_id"])})
json.dump(P, open("site/_mock.json", "w"))
print("mock pool: %d players" % len(P))
print(pd.Series([x["p"] for x in P])
      .value_counts().to_string())
print("adp from board: %d | fell back to rank: %d"
      % (int(B["ad"].notna().sum()),
         int(B["ad"].isna().sum())))

CSS = """
body{margin:0;background:#0a0a0c;color:#e6e8ec;
font:13px/1.5 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,sans-serif}
.w{max-width:1240px;margin:0 auto;padding:18px}
h1{font-size:20px;letter-spacing:-.02em;margin:0 0 4px}
h2{font-size:11px;letter-spacing:.09em;
text-transform:uppercase;color:#878c96;margin:18px 0 6px}
.bar{display:flex;gap:10px;align-items:center;
flex-wrap:wrap;margin:12px 0}
select,input,button{background:#16181d;color:#e6e8ec;
border:1px solid #24262d;border-radius:3px;
padding:6px 9px;font-size:13px}
button{cursor:pointer}
button:hover{background:#24262d}
.grid{display:grid;grid-template-columns:1fr 330px;
gap:22px}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:13px}
td{padding:6px 7px;border-bottom:1px solid #17191e}
td.r{text-align:right;color:#a8aeb9}
td.sl{color:#878c96;font-size:11px;font-weight:700;
width:46px}
.pos{display:inline-block;min-width:34px;
text-align:center;padding:2px 6px;border-radius:3px;
font-size:10px;font-weight:800;color:#0a0a0c}
.QB{background:#f2f4f8}.RB{background:#d9dee6}
.WR{background:#c0c6d0}.TE{background:#a8aeb9}
.K{background:#9096a1}.DEF{background:#7d838e}
.tm{color:#878c96}
.you{color:#fff}
.lg{padding:4px 0;border-bottom:1px solid #17191e;
color:#a8aeb9}
.lg span{color:#878c96;display:inline-block;width:34px}
.big{font-size:26px;font-weight:700}
"""

js = open("site/_mock.js").read().replace(
    "__DATA__", json.dumps(P), 1)
H = ("<!doctype html><html><head><meta charset=utf-8>"
     "<meta name=viewport content='width=device-width,"
     "initial-scale=1'><title>Mock Draft</title>"
     "<style>" + CSS + "</style></head><body><div class=w>"
     "<h1>Mock Draft</h1><div id=st></div>"
     "<div class=bar>your slot "
     "<select id=sl>"
     + "".join("<option>%d</option>" % i
               for i in range(1, 11))
     + "</select><button id=go>new draft</button>"
     "<input id=s placeholder='search player'>"
     "<select id=f><option value=''>all</option>"
     "<option>QB</option><option>RB</option>"
     "<option>WR</option><option>TE</option>"
     "<option>K</option><option>DEF</option>"
     "</select></div><div class=grid><div>"
     "<h2>Best available</h2><table><tbody id=bd>"
     "</tbody></table></div><div>"
     "<h2>Your lineup &middot; <span class=big "
     "id=mt>0</span> ppg</h2>"
     "<table><tbody id=me></tbody></table>"
     "<h2>Live standings</h2>"
     "<table><tbody id=gr></tbody></table>"
     "<h2>Recent picks</h2><div id=lg></div>"
     "</div></div></div><script>" + js
     + "</script></body></html>")
open("site/mock.html", "w").write(H)
print("\nwrote site/mock.html  %d KB" % (len(H) // 1024))
