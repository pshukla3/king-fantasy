import marshal
import os

P = "__pycache__/112_ui_v4.cpython-313.pyc"
d = open(P, "rb").read()
print("pyc %d bytes | magic %s" % (len(d), d[:4].hex()))
code = marshal.loads(d[16:])

S = []
def walk(c):
    for k in c.co_consts:
        if isinstance(k, str):
            S.append(k)
        elif hasattr(k, "co_consts"):
            walk(k)
walk(code)
S = [x for x in S if len(x) > 40]
S.sort(key=len, reverse=True)
print("string constants over 40 chars: %d" % len(S))
print("\n=== BIGGEST 8 ===")
for i, x in enumerate(S[:8]):
    print("  [%d] %6d chars | %s"
          % (i, len(x), x[:60].replace("\n", " ")))

os.makedirs("recover", exist_ok=True)
for i, x in enumerate(S[:8]):
    open("recover/blob_%d.txt" % i, "w").write(x)
print("\nwrote recover/blob_0..%d.txt"
      % (min(8, len(S)) - 1))
