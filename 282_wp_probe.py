import json

W = json.load(open("site/_wp.json"))

def walk(o, p="", d=0):
    if d > 3:
        return
    if isinstance(o, dict):
        ks = list(o.keys())
        num = [k for k in ks
               if isinstance(o[k], (int, float))]
        print("  %-28s dict(%d) %s"
              % (p or "<root>", len(ks),
                 ("nums:" + ",".join(num[:6]))
                 if num else ""))
        for k in ks[:12]:
            walk(o[k], (p + "." + k) if p else k, d + 1)
    elif isinstance(o, list):
        print("  %-28s list(%d) %s"
              % (p, len(o), str(o[:4])[:60]))
    else:
        pass

print("=== site/_wp.json STRUCTURE ===")
walk(W)
print("\n=== RAW (first 1200 chars) ===")
print(json.dumps(W)[:1200])
