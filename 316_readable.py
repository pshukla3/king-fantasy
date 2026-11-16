import glob
import re
import shutil

OLD, NEW = "DejaVu Fantasy", "King Fantasy"

H = open("vaporai.html").read()
n0 = len(H)
c = H.count(OLD)
H = H.replace(OLD, NEW)
H = re.sub(r"(<title>)[^<]*(</title>)", r"\1" + NEW + r"\2",
           H, count=1)
print("renamed %d in vaporai.html" % c)

hit = 0
for f in sorted(glob.glob("*.py")):
    if f.startswith("316_"):
        continue
    s = open(f).read()
    if OLD not in s:
        continue
    shutil.copy(f, f + ".prename")
    open(f, "w").write(s.replace(OLD, NEW))
    hit += 1
    print("  %s renamed" % f)
print("%d generators renamed" % hit)

CSS = '''<style id="readcss">
:root{--dm:#a6a9b2!important}
body,.pg,.nrow,table.tf td,table.st td{
-webkit-font-smoothing:antialiased}
.pg .sub,.pg .note,.hnote,.dnote,.gvmut,.tcempty,
.soon p,.lwrap p.lsub{color:#a6a9b2!important;
font-size:13.5px!important;line-height:1.65!important}
.nmeta,.sbmeta,.tcsug span,.tcchip span,.skrow span,
.tcrow span,.gvrp span,.ssrow span,.sscard span,
.ssfc,.tctot,.ssteam span{
color:#a6a9b2!important;font-size:11.5px!important}
.hsec,.gvgrid h4,.tceq h4,.gvteam h5,.pg h3{
color:#c7cad1!important;font-size:12px!important;
letter-spacing:.07em!important}
table.tf th,table.st th{color:#b6b9c1!important;
font-size:11px!important;letter-spacing:.07em!important}
table.tf td,table.st td{font-size:13.5px!important}
table.tf td span{color:#a6a9b2!important;
font-size:11.5px!important}
table.tf td.n.d,table.tf td.tg{color:#b6b9c1!important}
table.tf td.tag{font-size:11px!important}
#rail button{font-size:11px!important;
color:#a6a9b2!important}
#rail button.on{color:#0a0a0c!important}
#subbar button{font-size:13.5px!important;
color:#a6a9b2!important}
#subbar button.on{color:#fff!important}
.sbrow{font-size:13.5px!important}
.sbrow span.vv{color:#b6b9c1!important;
font-size:12.5px!important}
.sbmeta{font-size:10.5px!important}
.gvpl{font-size:13px!important}
.gvpl span,.gvpl i{color:#a6a9b2!important;
font-size:11px!important}
.gvpl u{color:#e8eaee!important}
.gvpl b{font-size:12.5px!important}
.gvhd span,.gvsub{color:#a6a9b2!important;
font-size:11.5px!important}
.welc p{color:#c7cad1!important;font-size:15px!important}
.welc h1 em{color:#a6a9b2!important}
.ssrow{font-size:13.5px!important}
.ssrow b em{color:#a6a9b2!important;font-size:12px!important}
.ssrow.ssh b,.ssrow.ssh u{color:#b6b9c1!important;
font-size:11px!important}
.tcset label,.lnote{color:#a6a9b2!important;
font-size:11.5px!important}
.brk{font-size:10.5px!important}
::placeholder{color:#8f939c!important;opacity:1}
.lfeat p{color:#a6a9b2!important;font-size:13px!important}
.lfeat h4{font-size:14px!important}
</style>'''

H = re.sub(r'<style id="readcss">.*?</style>', "", H, flags=re.S)
bl = list(re.finditer(r'<style id="[\w-]+">', H))
last = max(bl, key=lambda x: x.start())
j = H.index("</style>", last.start()) + 8
H = H[:j] + CSS + H[j:]

assert H.count('id="readcss"') == 1
assert "</script></body></html>" in H, "tail broken"
nav = len(re.findall(r'<button[^>]*data-t=', H))
assert nav == 26, "nav changed: %d" % nav
i = H.index('id="readcss"')
print("readcss last: %s"
      % all(i > H.index('id="%s"' % k)
            for k in ("finalcss", "polishcss", "landcss")
            if 'id="%s"' % k in H))
open("vaporai.html", "w").write(H)
print("vaporai.html %d -> %d bytes" % (n0, len(H)))
