import io, os, csv
B = r"D:/股票数据/市场数据/_学习/_bars_cache"
codes = ["603197","603278","003029","002724","600148","600860","002835","600178","605488","600293"]
files = os.listdir(B)
print("n files", len(files), files[:5])
for c in codes:
    p = os.path.join(B, f"{c}.csv")
    if not os.path.exists(p):
        print(c,"MISSING"); continue
    with io.open(p, encoding="utf-8-sig") as f:
        rows=list(csv.DictReader(f))
    cols=list(rows[0].keys())
    sel=[r for r in rows if str(r.get("date",""))[-10:].replace("-","") in ("20261016","20261019","20261020")]
    print("==",c,cols)
    for r in sel: print("   ", [r[k] for k in cols])
