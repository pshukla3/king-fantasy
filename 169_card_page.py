import json

D = json.load(open("player_cards.json"))
css = open("site/_player.css").read()
js = open("site/_player.js").read()
js = js.replace("__DATA__", json.dumps(D), 1)

H = ("<!doctype html><html><head><meta charset=utf-8>"
     "<meta name=viewport content='width=device-width,"
     "initial-scale=1'><title>Player</title><style>"
     + css + "</style></head><body><div id=root></div>"
     "<script>" + js + "</script></body></html>")
open("site/player.html", "w").write(H)
print("cards %d | player.html %d KB" % (len(D), len(H) // 1024))

s = [v for v in D.values() if v["nm"] == "Caleb Williams"]
if s:
    p = s[0]
    print("%s | %s | age %s %s %s lbs | %s"
          % (p["nm"], p["tm"], p["age"], p["ht"],
             p["wt"], p["col"]))
    print("  #%s overall #%s %s | %.2f ppg | %d seasons"
          % (p["rk"], p["prk"], p["ps"], p["ppg"],
             len(p["career"])))
    print("  id=%s" % p["id"])
