import re

CSS = ('<style id="gvcss">'
       '.gvov{position:fixed;inset:0;z-index:9000;'
       'background:rgba(4,5,7,.88);display:none;'
       'align-items:flex-start;justify-content:center;'
       'overflow-y:auto;padding:34px 16px}'
       '.gvov.on{display:flex}'
       '.gvbx{background:#0d0e10;border:1px solid #2a2c30;'
       'border-radius:4px;max-width:960px;width:100%;'
       'padding:20px 22px;position:relative}'
       '.gvcl{position:absolute;top:12px;right:14px;'
       'background:#1a1c1f;color:#9aa0a6;border:1px solid '
       '#2a2c30;border-radius:3px;padding:5px 11px;'
       'cursor:pointer;font-size:11px;z-index:2}'
       '.gvhd{display:flex;justify-content:space-between;'
       'align-items:baseline;border-bottom:1px solid #2a2c30;'
       'padding-bottom:10px;margin-bottom:14px}'
       '.gvhd b{font-size:19px;color:#e8eaed}'
       '.gvhd span{font-size:11px;color:#5f6368;'
       'text-transform:uppercase;letter-spacing:.07em}'
       '.gvwp{display:flex;align-items:center;gap:14px;'
       'margin:6px 0}'
       '.gvt{display:flex;flex-direction:column;min-width:66px}'
       '.gvt i{font-style:normal;font-size:11px;color:#5f6368}'
       '.gvt b{font-size:21px;color:#e8eaed}'
       '.gvbar{flex:1;height:10px;background:#3c4043;'
       'border-radius:5px;overflow:hidden;display:flex}'
       '.gvbar i{display:block;height:100%}'
       '.gvsub{font-size:11px;color:#5f6368;margin-bottom:12px;'
       'text-transform:uppercase;letter-spacing:.06em}'
       '.gvfld{width:100%;height:auto;border:1px solid #2a2c30;'
       'border-radius:3px;margin-bottom:16px;display:block}'
       '.gvcrv{width:100%;height:auto;margin-bottom:8px;'
       'display:block}'
       '.gvgrid{display:grid;grid-template-columns:1.6fr 1fr;'
       'gap:22px}'
       '.gvgrid h4{margin:14px 0 7px;font-size:11px;'
       'color:#9aa0a6;text-transform:uppercase;'
       'letter-spacing:.08em;font-weight:600}'
       '.gvpl{font-size:12px;color:#c8ccd0;padding:6px 0;'
       'border-bottom:1px solid #1c1e21;line-height:1.45}'
       '.gvpl span{color:#5f6368;margin-right:8px;'
       'font-size:10px}'
       '.gvqt{width:100%;font-size:12px;color:#c8ccd0;'
       'border-collapse:collapse}'
       '.gvqt td{padding:4px 0;border-bottom:1px solid #1c1e21}'
       '.gvqt td:last-child{text-align:right;color:#8ab4f8}'
       '.gvrp{display:flex;justify-content:space-between;'
       'font-size:12px;padding:5px 0;'
       'border-bottom:1px solid #1c1e21}'
       '.gvrp span{color:#5f6368;font-size:11px}'
       '.gvmut{color:#5f6368;font-size:12px;padding:8px 0}'
       '.sbc{cursor:pointer}'
       '.sbc:hover{background:#17181a}'
       '@media(max-width:760px){.gvgrid{'
       'grid-template-columns:1fr}}'
       '</style>')
TAG = '<script src="_game.js"></script>'

H = open("vaporai.html").read()
n0 = len(H)

H = re.sub(r"<!--GVCSS-->.*?</style>", "", H,
           flags=re.S)
H = re.sub(r'<style id="gvcss">.*?</style>', "", H,
           flags=re.S)
H = H.replace(TAG, "")

m = re.search(r"<body[^>]*>", H)
assert m, "no <body>"
H = H[:m.end()] + CSS + TAG + H[m.end():]

assert H.count('id="gvcss"') == 1, "css not once"
assert H.count(TAG) == 1, "tag not once"
assert len(H) > n0 * 0.9, "size drop"
open("vaporai.html", "w").write(H)
print("gvcss + script moved below </body> (safe zone)")
print("vaporai.html %d -> %d bytes" % (n0, len(H)))

s = open("site/_game.js").read()
a = 'd.id="gvx";d.className="gvov";d.style.display="none";'
if a in s:
    s = s.replace(a, 'd.id="gvx";d.className="gvov";', 1)
    print("shell: inline display removed")
s = s.replace('if(d)d.style.display="none";',
              'if(d)d.classList.remove("on");', 1)
s = s.replace('document.getElementById("gvx")'
              '.style.display="flex";',
              'document.getElementById("gvx")'
              '.classList.add("on");', 1)
open("site/_game.js", "w").write(s)
print("_game.js now toggles .on class")
