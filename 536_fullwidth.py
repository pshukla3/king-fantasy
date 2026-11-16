import glob
CSS = (".wrap{max-width:none!important;width:auto!important}"
       ".kfw{max-width:none!important}"
       "#scores .wrap{max-width:none!important}"
       "#cardbx{max-width:1500px!important}"
       ".board{max-width:none!important}"
       ".gridwrap{max-width:none!important}")
M0 = "<!--KFWIDE-->"; M1 = "<!--ENDKFWIDE-->"
BLK = M0 + '<style id="kfwide">' + CSS + '</style>' + M1

files = ["vaporai.html"] + [f for f in sorted(glob.glob("site/*.html"))
                            if not f.endswith("index.html")]
done = 0
for f in files:
    try:
        s = open(f, encoding="utf-8").read()
    except Exception as e:
        print("  skip %s (%s)" % (f, e)); continue
    if M0 in s:
        a = s.index(M0); b = s.index(M1) + len(M1)
        s = s[:a] + s[b:]
    s = s.rstrip() + "\n" + BLK + "\n"
    open(f, "w", encoding="utf-8").write(s)
    done += 1
    print("  widened %s" % f)
print("full-width override applied to %d files" % done)
