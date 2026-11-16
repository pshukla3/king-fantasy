p = "148_league_data.py"
s = open(p).read()

old = ('def key(s):\n'
       '    return re.sub(r"[^a-z]", "", str(s).lower())\n')
new = ('_SUF = re.compile(r"\\b(jr|sr|ii|iii|iv)\\b\\.?",\n'
       '                  re.I)\n'
       'def key(s):\n'
       '    s = _SUF.sub("", str(s))\n'
       '    return re.sub(r"[^a-z]", "", s.lower())\n')
assert old in s, "key() anchor not found"
s = s.replace(old, new, 1)

anc = '        DEFMAP.setdefault(_t, _r)\n'
assert anc in s, "DEFMAP anchor not found"
alias = (anc
         + '_AL = {"LA": "LAR", "LAR": "LA",\n'
         + '       "WAS": "WSH", "WSH": "WAS",\n'
         + '       "ARI": "AZ", "AZ": "ARI",\n'
         + '       "JAX": "JAC", "JAC": "JAX"}\n'
         + 'for _a, _b in list(_AL.items()):\n'
         + '    if _a in DEFMAP and _b not in DEFMAP:\n'
         + '        DEFMAP[_b] = DEFMAP[_a]\n')
s = s.replace(anc, alias, 1)
open(p, "w").write(s)
print("patched 148: suffix-stripping + DEF aliases")

q = "152_rosters.py"
t = open(q).read()
o2 = '                           "ppg": round(p["ppg"], 2)}'
n2 = ('                           "ppg": round(p["ppg"], 2),\n'
      '                           "bye": int(p["bye"])}')
assert o2 in t, "152 ppg anchor not found"
t = t.replace(o2, n2, 1)
open(q, "w").write(t)
print("patched 152: bye weeks into rosters")

import subprocess
for f in (p, q):
    r = subprocess.run(["python3", "-m", "py_compile", f],
                       capture_output=True, text=True)
    print("  %s %s" % (f, r.stderr.strip() or "ok"))
