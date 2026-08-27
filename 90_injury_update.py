import pandas as pd

I = pd.read_csv("injuries_2026.csv")
print("before: %d rows" % len(I))

UPD = {
    "Tucker Kraft": ("QUESTIONABLE", "Knee", "",
        "off PUP and practicing; ACL return, live for Wk1"),
    "Malik Nabers": ("QUESTIONABLE", "Knee", "",
        "practicing, on track for Wk1 after ACL"),
    "Sam LaPorta": ("QUESTIONABLE", "Hip", 1.0,
        "Wk1 uncertain, Lions resting him"),
    "Alec Pierce": ("QUESTIONABLE", "Ankle", "",
        "expected off PUP this week, in line for Wk1"),
    "Tyler Warren": ("QUESTIONABLE", "Groin", "",
        "adductor strain, back within about a week"),
    "Chuba Hubbard": ("QUESTIONABLE", "Hamstring", "",
        "wk-to-wk, out for preseason; Brooks committee"),
}

NEW = [
    ("Christian McCaffrey", "SF", "RB", "QUESTIONABLE",
     "Undisclosed", "", "camp",
     "tightness, missed Aug 10; 450 touches in 2025"),
    ("Jonathon Brooks", "CAR", "RB", "QUESTIONABLE",
     "Knee", "", "carryover",
     "back from two ACLs, taking first-team reps"),
]

for nm, (st, inj, wo, note) in UPD.items():
    m = I["player"] == nm
    if not m.any():
        print("  NOT FOUND: %s" % nm)
        continue
    old = I.loc[m, "status"].iloc[0]
    I.loc[m, "status"] = st
    I.loc[m, "injury"] = inj
    I.loc[m, "weeks_out"] = wo if wo != "" else float("nan")
    I.loc[m, "note"] = note
    print("  %-22s %-12s -> %-12s" % (nm, old, st))

have = set(I["player"])
add = [r for r in NEW if r[0] not in have]
if add:
    A = pd.DataFrame(add, columns=list(I.columns))
    I = pd.concat([I, A], ignore_index=True)
    for r in add:
        print("  ADDED %-22s %s %s" % (r[0], r[1], r[4]))

I.to_csv("injuries_2026.csv", index=False)
print("after:  %d rows" % len(I))
