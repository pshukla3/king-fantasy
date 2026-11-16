import numpy as np
import pandas as pd
from collections import Counter

B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()].copy()
for c in ["adp", "points", "rank", "p10", "p90"]:
    B[c] = pd.to_numeric(B.get(c), errors="coerce")
B = B[B["points"].notna()]
B["adpf"] = B["adp"].fillna(999.0)
mx = B["adpf"].max()
B.loc[B["adpf"] > 300, "adpf"] = 220.0 + \
    B.loc[B["adpf"] > 300, "rank"].fillna(400) * 0.05
B = B.reset_index(drop=True)
N = len(B)
print("pool %d players | with real adp %d"
      % (N, int(B["adp"].notna().sum())))

TEAMS, RND, SIMS = 10, 9, 4000
rng = np.random.default_rng(11)
adp = B["adpf"].values
nm = B["player_display_name"].values
pos = B["position"].values
tm = B["team"].fillna("").values
pts = B["points"].values
mrk = B["rank"].fillna(999).values

def picks_for(seat):
    out = []
    for r in range(1, RND + 1):
        p = ((r - 1) * TEAMS + seat if r % 2 == 1
             else (r - 1) * TEAMS + (TEAMS + 1 - seat))
        out.append((r, p))
    return out

order = np.argsort(
    adp[None, :] * np.exp(rng.normal(0, 0.22, (SIMS, N))),
    axis=1)
slot = np.empty((SIMS, N), dtype=np.int32)
rows = np.arange(SIMS)[:, None]
slot[rows, order] = np.arange(N)[None, :] + 1

for seat in (1, 2):
    print("\n" + "=" * 54)
    print("SEAT %d  (10-team snake, Full PPR)" % seat)
    print("=" * 54)
    for r, p in picks_for(seat):
        avail = slot >= p
        best_ct = Counter()
        for s in range(0, SIMS, 8):
            idx = np.where(avail[s])[0]
            if not len(idx):
                continue
            b = idx[np.argmin(mrk[idx])]
            best_ct[b] += 1
        top = best_ct.most_common(4)
        ttl = sum(c for _, c in top) or 1
        print("\n  Round %d, pick %d" % (r, p))
        for i, c in top:
            print("    %5.0f%%  %-22s %-3s %-4s "
                  "%5.1f ppg  rk%3d  adp%6.1f"
                  % (100.0 * c / ttl, nm[i][:22], pos[i],
                     tm[i], pts[i], mrk[i],
                     B["adp"].values[i]
                     if B["adp"].notna().values[i] else -1))
        if r <= 3:
            idx = np.where(avail[0])[0]
            gone = np.where(~avail[0])[0]
            if len(gone):
                g = gone[np.argsort(mrk[gone])][:3]
                print("    likely gone: %s"
                      % ", ".join("%s (rk%d)"
                                  % (nm[i][:16], mrk[i])
                                  for i in g))

print("\n" + "=" * 54)
print("POSITIONAL CLIFFS (where value falls off)")
print("=" * 54)
for p in ["RB", "WR", "TE", "QB"]:
    d = B[B["position"] == p].sort_values(
        "points", ascending=False).head(40)
    v = d["points"].values
    gaps = [(i + 1, v[i] - v[i + 1])
            for i in range(min(29, len(v) - 1))]
    gaps.sort(key=lambda x: -x[1])
    top3 = sorted(gaps[:3])
    print("  %-3s biggest drops after %s"
          % (p, ", ".join("%s%d (-%.1f)" % (p, a, b)
                          for a, b in top3)))
