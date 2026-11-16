import ast, json, re

src = open("289_nav2.py").read()

i = src.find("GROUPS")
j = src.find("[", i)
assert j > 0, "no GROUPS list"
depth, k = 0, j
while k < len(src):
    if src[k] == "[":
        depth += 1
    elif src[k] == "]":
        depth -= 1
        if depth == 0:
            break
    k += 1
block = src[j:k + 1]
G = ast.literal_eval(block)
print("before: " + " | ".join(g["lb"] for g in G))

by = {g["k"]: g for g in G}

# Start / Sit and Trade Calculator become their own
# groups, so drop the duplicates from Tools
tl = by.get("tl")
if tl:
    tl["it"] = [it for it in tl["it"]
                if it[1] not in ("tcalc", "tstart")]

if "ss" not in by:
    by["ss"] = {"k": "ss", "ic": "\u2696",
                "lb": "Start / Sit",
                "it": [["Start / Sit", "tstart"]]}
by["ss"]["it"] = [["Start / Sit", "tstart"]]

by["tc"] = {"k": "tc", "ic": "\u21c4",
            "lb": "Trade Calculator",
            "it": [["Calculator", "trades"],
                   ["Trade Finder", "tfind"]]}
if tl:
    tl["it"] = [it for it in tl["it"] if it[1] != "tfind"]

ORDER = ["home", "lg", "dr", "rk", "ss", "tc", "rs", "tl"]
NEW = [by[k2] for k2 in ORDER if k2 in by and by[k2]["it"]]
for g in G:
    if g["k"] not in ORDER and g["it"]:
        NEW.append(g)

print("after:  " + " | ".join(g["lb"] for g in NEW))

lines = ["["]
for g in NEW:
    lines.append(' {"k": %s, "ic": %s, "lb": %s,'
                 % (json.dumps(g["k"]),
                    json.dumps(g["ic"]),
                    json.dumps(g["lb"])))
    lines.append('  "it": %s},' % json.dumps(g["it"]))
lines[-1] = lines[-1].rstrip(",")
lines.append("]")
out = "\n".join(lines)

src = src[:j] + out + src[k + 1:]
open("289_nav2.py", "w").write(src)
print("\nrewrote GROUPS in 289_nav2.py")

# every tab referenced must have a section
H = open("vaporai.html").read()
miss = []
for g in NEW:
    for lbl, tab in g["it"]:
        if ('id="%s"' % tab) not in H:
            miss.append("%s (%s)" % (tab, lbl))
print("tabs without a section: %s"
      % (", ".join(miss) if miss else "none"))
