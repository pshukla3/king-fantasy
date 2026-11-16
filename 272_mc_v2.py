import numpy as np
import mc_core as M

print("pool %d | full cells %d | fell back %d"
      % (len(M.D), M.NFULL, M.NBACK))
print("\n=== what the endgame cells actually hold ===")
print("  drives starting UP 1-8, by time left:")
u = M.D[(M.D["sd"] > 0) & (M.D["sd"] < 8.5)]
for lo, hi in [(0, 15), (16, 40), (41, 90),
               (91, 180), (181, 420)]:
    k = u[(u["t0"] >= lo) & (u["t0"] <= hi)]
    if len(k):
        print("    %3d-%-4ds n=%5d  pts %.2f  secs %3.0f"
              % (lo, hi, len(k), k["op"].mean(),
                 k["el"].mean()))

print("\n=== SANITY (reference team) ===")
print("  %-32s %7s %9s" % ("state", "sim", "real"))
print("  " + "-" * 51)
for nm, a, b, c, r in [
        ("kickoff, tied, own 25", 0, 3600, 75, "~50%"),
        ("halftime, tied, own 25", 0, 1800, 75, "~50%"),
        ("up 7, 2:00, own 25", 7, 120, 75, "~93%"),
        ("down 7, 2:00, own 25", -7, 120, 75, "~10%"),
        ("down 3, 2:00, opp 30", -3, 120, 30, "~46%"),
        ("up 3, 0:30, own 25", 3, 30, 75, "~97%"),
        ("up 3, 0:08, own 25", 3, 8, 75, "~99%"),
        ("down 14, 5:00, own 25", -14, 300, 75, "~2%"),
        ("up 17, Q4 start", 17, 900, 75, "~99%")]:
    p, _ = M.wp(a, b, c)
    print("  %-32s %6.1f%% %9s" % (nm, 100 * p, r))

print("\n=== SPREAD RESPONSE (tied kickoff) ===")
for s in [-7, -3, 0, 3, 7]:
    p, _ = M.wp(0, 3600, 75, sp=s, n=20000)
    print("  favored by %+d   ->  %5.1f%%" % (s, 100 * p))

p, m = M.wp(0, 3600, 75, n=40000)
print("\n=== MARGIN, tied kickoff, 40k sims ===")
print("  mean %+.2f (real ~+0.5) | sd %.2f (real ~13.5)"
      % (m.mean(), m.std()))
print("  P(tie -> OT) %.3f (real ~0.06)"
      % float((m == 0).mean()))
