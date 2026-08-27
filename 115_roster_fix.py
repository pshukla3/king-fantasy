import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
M = pd.read_csv("my_roster.csv")
K = pd.read_csv("kicker_projections.csv")
D = pd.read_csv("dst_projections_2026.csv")

def kkey(n):
    p = str(n).split()
    return (p[0][0] + "." + p[-1]).lower() if len(p) > 1 else ""

KV = {}
for _, r in K.iterrows():
    KV[str(r["kicker"]).lower()] = float(r["ppg"])

added = 0
for _, r in M.iterrows():
    nm = str(r["player"]).strip()
    if (B["player_display_name"] == nm).any():
        continue
    ppg = None
    if r["pos"] == "K":
        ppg = KV.get(kkey(nm))
    if ppg is None:
        print("  CANNOT PRICE: %s (%s)" % (nm, r["pos"]))
        continue
    row = {c: None for c in B.columns}
    row.update({"player_id": "KD_" + nm.replace(" ", "_"),
                "player_display_name": nm, "position": r["pos"],
                "points": round(ppg, 2), "exp_games": 17.0,
                "rank": int(B["rank"].max()) + 1,
                "pos_rank": int((B["position"] == r["pos"]).sum()) + 1,
                "source": "pbp"})
    B = pd.concat([B, pd.DataFrame([row])], ignore_index=True)
    added += 1
    print("  added %-22s %s  %.2f ppg" % (nm, r["pos"], ppg))

B.to_csv("board_final.csv", index=False)
print("roster players restored to board: %d" % added)
