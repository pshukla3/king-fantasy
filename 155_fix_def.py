p = "148_league_data.py"
s = open(p).read()

old = ('        if b is None and d.get("position") == "DEF":\n'
       '            b = BK.get(key(str(d.get("team", ""))'
       ' + "defense"))\n')
new = ('        if b is None and d.get("position") in\\\n'
       '                ("DEF", "DST"):\n'
       '            b = DEFMAP.get(str(d.get("team",\n'
       '                                      "")).upper())\n')
assert old in s, "DEF fallback anchor not found"
s = s.replace(old, new, 1)

anc = 'B["k"] = B["player_display_name"].apply(key)\n'
assert anc in s, "BK anchor not found"
dm = (anc
      + 'DEFMAP = {}\n'
      + 'for _, _r in B[B["position"].astype(str)\n'
      + '        .isin(["DEF", "DST"])].iterrows():\n'
      + '    _t = str(_r["team"]).upper()\n'
      + '    if _t and _t != "NAN":\n'
      + '        DEFMAP.setdefault(_t, _r)\n')
s = s.replace(anc, dm, 1)
open(p, "w").write(s)
print("patched %s" % p)

import subprocess
o = subprocess.run(["python3", "-m", "py_compile", p],
                   capture_output=True, text=True)
print("compile: %s" % (o.stderr.strip() or "ok"))
