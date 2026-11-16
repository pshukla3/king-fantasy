import glob,sys,ast
CSS='''

.wrap{max-width:none!important;padding:14px 18px!important}
.board{display:block!important}
.pane{width:100%!important;margin-top:16px}
.gridwrap{background:#101010;border:1px solid #232323;
 border-radius:12px;padding:10px!important;
 overflow:auto!important;max-height:none!important}
table.g{border-collapse:separate;border-spacing:4px;
 width:100%;table-layout:fixed}
table.g thead th{position:sticky;top:0;z-index:3;
 background:#141414;font-size:12px;padding:8px 4px;
 color:#9aa;white-space:nowrap;overflow:hidden}
table.g th.rh{position:sticky;left:0;z-index:4;
 background:#141414;width:26px;font-size:11px;color:#777}
table.g th.meh{color:#3b82f6}
table.g td.c{height:58px!important;padding:4px 6px;
 border-radius:7px;background:#161b26;
 border:1px solid #232c3d;overflow:hidden;
 position:relative;vertical-align:top}
table.g td.c em{position:absolute;top:3px;right:6px;
 font-size:10px;color:#6b7686;font-style:normal}
table.g td.c s{position:absolute;bottom:2px;left:6px;
 font-size:11px;color:#55606f;text-decoration:none}
table.g td.c b{display:block;font-size:12px;line-height:1.15;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
 max-width:88%;margin-top:3px;color:#0d1117}
table.g td.c i{display:block;font-size:9px;font-style:normal;
 color:#263040;margin-top:2px}
table.g td.me{box-shadow:inset 0 0 0 2px #3b82f6}
table.g td.on{box-shadow:0 0 0 3px #fbbf24}
.p-QB{background:#f2a0b4!important;border-color:#e07c96!important}
.p-RB{background:#8fe0b0!important;border-color:#5cc78d!important}
.p-WR{background:#86c7f0!important;border-color:#54a8df!important}
.p-TE{background:#f0b878!important;border-color:#dd9a4e!important}
.p-K,.p-DST{background:#c9c9d4!important;
 border-color:#a8a8b8!important}
.rch{outline:2px solid #ef4444}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.tabs button{display:flex;flex-direction:column;
 align-items:center;line-height:1.1;padding:6px 14px;
 border-radius:16px;font-size:12px}
.tabs button small{font-size:10px;opacity:.65;margin-top:2px}
table.pl{width:100%;border-collapse:collapse;font-size:12px}
table.pl tr.grp th{font-size:10px;color:#8b94a3;
 letter-spacing:.6px;padding:6px 4px;
 border-bottom:1px solid #222}
table.pl tr.hd2 th{font-size:10px;color:#6f7988;
 padding:5px 4px;border-bottom:1px solid #2a2a2a;
 text-align:right}
table.pl tr.hd2 th.pn{text-align:left}
table.pl td{padding:7px 4px;text-align:right;
 border-bottom:1px solid #1b1b1b;color:#c9d1d9}
table.pl td.pn{text-align:left;min-width:190px}
table.pl td.pn b{display:block;font-size:13px;color:#fff}
table.pl td.pn i{font-style:normal;font-size:10px;
 color:#8b94a3}
table.pl td.rk{color:#6f7988;width:38px}
table.pl td.hi{color:#fff;font-weight:600}
table.pl button{padding:4px 12px;border-radius:6px;
 font-size:11px}
'''
M0="/*KFGRID*/"; M1="/*ENDKFGRID*/"
tgt=None
for f in sorted(glob.glob("*.py")):
    s=open(f,encoding="utf-8").read()
    if "function drawGrid(){" in s:
        tgt=f;break
if not tgt: sys.exit("generator not found")
s=open(tgt,encoding="utf-8").read()
if M0 in s:
    a=s.index(M0); b=s.index(M1)+len(M1)
    s=s[:a]+s[b:]
anchor=".gridwrap{"
if anchor not in s: sys.exit("no .gridwrap anchor to attach after")
i=s.index(anchor)
s=s[:i]+M0+CSS+M1+"\n"+s[i:]
open(tgt,"w",encoding="utf-8").write(s)
ast.parse(s)
print("css block inserted into %s (ast ok)"%tgt)
