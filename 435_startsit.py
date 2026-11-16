import re

N = open("289_nav2.py").read()

if '"k": "ss"' in N:
    print("Start / Sit group already present")
else:
    anchor = '{"k": "dr",'
    assert N.count(anchor) == 1, "draft group anchor"
    GRP = ('{"k": "ss", "ic": "\\u2696", "lb": "Start / Sit",\n'
           '  "it": [["Start / Sit", "tstart"]]},\n ')
    N = N.replace(anchor, GRP + anchor, 1)
    open("289_nav2.py", "w").write(N)
    print("Start / Sit group added below My League")

i = N.find("GROUPS")
print("-" * 52)
print(N[i:i + 620])
