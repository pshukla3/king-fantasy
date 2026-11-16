p = "112_ui_v4.py"
s = open(p).read()

OLD = (" --bg:#0b0d10; --panel:#15181e; --panel2:#1c2028;\n"
       " --line:#272c36; --text:#d8dee6; --dim:#8b95a5;\n"
       " --sky:#56c2ff; --sky2:#8fd8ff;\n")
NEW = (" --bg:#08090b; --panel:#131519; --panel2:#1b1e24;\n"
       " --line:#262a33; --text:#dfe4ec; --dim:#8b95a5;\n"
       " --sky:#56c2ff; --sky2:#8fd8ff;\n")
assert OLD in s, "root palette block not found"
s = s.replace(OLD, NEW, 1)
print("palette -> satin black base")

assert "<title>VaporAI</title>" in s, "title not found"
s = s.replace("<title>VaporAI</title>",
              "<title>KING Fantasy</title>", 1)

b = '<span class="brand">VAPOR<em>AI</em></span>'
assert b in s, "brand markup not found"
s = s.replace(b, '<span class="brand">'
              '<span class="crown">&#9812;</span>'
              'KING<em>Fantasy</em></span>', 1)

cs = ".brand{font-size:20px;font-weight:800;letter-spacing:1px}"
assert cs in s, "brand css not found"
s = s.replace(cs, ".brand{font-size:20px;font-weight:800;"
              "letter-spacing:1px;display:inline-flex;"
              "align-items:center;gap:8px}\n"
              ".brand em{margin-left:4px}\n"
              ".crown{color:var(--sky);font-size:24px;"
              "line-height:1}", 1)
s = s.replace('console.log("vaporai ready")',
              'console.log("king fantasy ready")', 1)
open(p, "w").write(s)
print("renamed VaporAI -> KING Fantasy (crown placeholder)")

q = "113_home.py"
t = open(q).read()
n = t.count("VaporAI")
t = t.replace("Welcome to <em>VaporAI</em>",
              "Welcome to <em>KING Fantasy</em>")
t = t.replace("<em>VaporAI</em>", "<em>KING Fantasy</em>")
open(q, "w").write(t)
print("113_home.py: %d VaporAI refs updated" % n)
print("note: vaporai.html stays the build filename")
