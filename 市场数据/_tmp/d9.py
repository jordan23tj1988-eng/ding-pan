import io, os, csv
B = r"D:/股票数据/市场数据"
cache = os.path.join(B,"_bars_cache")
codes = ["603197","603278","003029","002724","600148","600860","002889","600178"]
print("cache exists", os.path.isdir(cache))
if os.path.isdir(cache):
    print([f for f in os.listdir(cache)][:10], "n=", len(os.listdir(cache)))
def bars(c):
    for fn in (f"{c}.csv",):
        p=os.path.join(cache,fn)
        if os.path.exists(p):
            with io.open(p, encoding="utf-8-sig") as f:
                rows=list(csv.DictReader(f))
            return rows
    return None
for c in codes:
    rows = bars(c)
    if not rows:
        print(c, "NO BARS"); continue
    cols=list(rows[0].keys())
    sel=[r for r in rows if str(r.get("date", r.get(cols[0],"")))[:10].replace("-","") in ("20261016","20261019","20261020")]
    print("==",c, cols)
    for r in sel: print("   ", {k:r[k] for k in cols})
