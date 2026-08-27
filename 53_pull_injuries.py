import pandas as pd, importlib

YEARS = list(range(2016, 2026))
inj, src = None, None

for mod, fn in [("nfl_data_py", "import_injuries"), ("nflreadpy", "load_injuries")]:
    try:
        m = importlib.import_module(mod)
    except ImportError:
        print(f"  {mod}: not installed")
        continue
    try:
        raw = getattr(m, fn)(YEARS) if mod == "nfl_data_py" else getattr(m, fn)(seasons=YEARS)
        inj = raw.to_pandas() if hasattr(raw, "to_pandas") else pd.DataFrame(raw)
        src = mod
        break
    except Exception as e:
        print(f"  {mod}.{fn} failed: {e}")

if inj is None:
    raise SystemExit("No nflverse package found. Run:  pip install nflreadpy")

print(f"source: {src} | rows: {len(inj)}")
print("\ncolumns:", list(inj.columns))
inj.to_csv("injuries_raw.csv", index=False)

for c in ["season", "report_status", "practice_status", "report_primary_injury",
          "practice_primary_injury", "position"]:
    if c in inj.columns:
        print(f"\n--- {c}: top 25 ---")
        print(inj[c].value_counts(dropna=False).head(25).to_string())

idc = next((c for c in ["gsis_id", "player_id"] if c in inj.columns), None)
nmc = next((c for c in ["full_name", "player_name", "player_display_name"]
            if c in inj.columns), None)
print("\nid col:", idc, "| name col:", nmc)
if idc:
    print("null ids:", int(inj[idc].isna().sum()))

if "report_status" in inj.columns:
    o = inj[inj["report_status"].astype(str).str.strip().eq("Out")]
    print("\ntotal OUT designations:", len(o))
    if "report_primary_injury" in o.columns:
        print("\n--- injuries most often causing OUT ---")
        print(o["report_primary_injury"].value_counts().head(30).to_string())

print("\nSaved injuries_raw.csv")
