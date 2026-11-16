import numpy as np
import mc_core as M

print("=== FALLBACK LADDER COVERAGE ===")
for i, nm in enumerate(M.LNAME):
    if M.LVL[i]:
        print("  %-18s %3d cells" % (nm, M.LVL[i]))
lost = M.LVL[4] + M.LVL[5] + M.LVL[6]
print("  cells that LOSE field position: %d/160"
      % lost)

print("\n=== SANITY (reference team) ===")
print("  %-30s %7s %8s %7s"
      % ("state", "sim", "real", "err"))
print("  " + "-" * 56)
tot = 0.0
for nm, a, b, c, r in [
        ("kickoff, tied, own 25", 0, 3600, 75, 50),
        ("halftime, tied, own 25", 0, 1800, 75, 50),
        ("up 7, 2:00, own 25", 7, 120, 75, 93),
        ("down 7, 2:00, own 25", -7, 120, 75, 10),
        ("down 3, 2:00, opp 30", -3, 120, 30, 46),
        ("up 3, 0:30, own 25", 3, 30, 75, 97),
        ("up 3, 0:08, own 25", 3, 8, 75, 99),
        ("down 14, 5:00, own 25", -14, 300, 75, 2),
        ("up 17, Q4 start", 17, 900, 75, 99),
        ("tied, 0:20, opp 25", 0, 20, 25, 72),
        ("down 2, 1:00, own 40", -2, 60, 60, 22)]:
    p, _ = M.wp(a, b, c)
    e = 100 * p - r
    tot += abs(e)
    print("  %-30s %6.1f%% %7d%% %+6.1f"
          % (nm, 100 * p, r, e))
print("  mean abs error %.1f pts" % (tot / 11))

p, m = M.wp(0, 3600, 75, n=40000)
print("\n=== MARGIN, tied kickoff ===")
print("  mean %+.2f (real ~+0.5) | sd %.2f (real ~13.5)"
      % (m.mean(), m.std()))
print("  P(OT) %.3f (real ~0.06)"
      % float((m == 0).mean()))
