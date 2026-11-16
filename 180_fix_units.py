p = "168_card_data.py"
s = open(p).read()

old = "def line(d, g):\n    return {\"gm\": int(g),"
new = ("def line(d, g, m=1.0):\n"
       "    return {\"gm\": int(g),")
assert old in s, "line() signature not found"
s = s.replace(old, new, 1)

import re
body = re.search(r'def line\(d, g, m=1\.0\):(.*?)\n\n',
                 s, re.S)
assert body, "line body not found"
b = body.group(1)
nb = re.sub(r'round\(float\(d\["(\w+)"\]\)\)',
            r'round(float(d["\1"]) * m)', b)
s = s.replace(b, nb, 1)

o2 = 'c["p26"] = line(SP.loc[pid], 17)'
n2 = 'c["p26"] = line(SP.loc[pid], 17, 17.0)'
assert o2 in s, "p26 call not found"
s = s.replace(o2, n2, 1)
open(p, "w").write(s)
print("patched 168: p26 now season totals (per-game x17)")
print("  2025 line unchanged (already season totals)")
