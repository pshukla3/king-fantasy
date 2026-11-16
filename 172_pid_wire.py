p = "152_rosters.py"
s = open(p).read()
old = ('                           "ppg": round(p["ppg"], 2),\n'
       '                           "bye": int(p["bye"])}')
new = ('                           "ppg": round(p["ppg"], 2),\n'
       '                           "bye": int(p["bye"]),\n'
       '                           "pid": (None\n'
       '                                   if p.get("pid") != p.get("pid")\n'
       '                                   else p.get("pid"))}')
if '"pid": (None' in s:
    print("152 already carries pid")
else:
    assert old in s, "152 player dict anchor not found"
    s = s.replace(old, new, 1)
    open(p, "w").write(s)
    print("152_rosters.py: pid added to roster players")

q = "148_league_data.py"
t = open(q).read()
import re
m = re.search(r'WV\.append\(\{([^}]*)\}\)', t, re.S)
if m and '"pid"' not in m.group(1):
    ins = m.group(1).rstrip().rstrip(",")
    t = t.replace(m.group(0),
                  'WV.append({' + ins
                  + ',\n               "pid": str(r["player_id"])})', 1)
    open(q, "w").write(t)
    print("148_league_data.py: pid added to waivers")
elif m:
    print("148 waivers already carry pid")
else:
    print("148: WV.append pattern not found - will patch after probe")

d = "deploy.sh"
s2 = open(d).read()
a = "python3 168_card_data.py   | tail -6"
if "166_id_fix" in s2:
    print("deploy.sh already runs 166")
elif a in s2:
    s2 = s2.replace(a, "python3 166_id_fix.py      | tail -4\n" + a, 1)
    open(d, "w").write(s2)
    print("deploy.sh: 166_id_fix now runs before 168")
else:
    print("deploy.sh: 168 anchor missing")
