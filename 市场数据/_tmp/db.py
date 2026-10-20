import io, os, csv
B = r"D:/股票数据/市场数据/_学习/_bars_cache"
for c in ["605189","002889","603197","002088"]:
    p=os.path.join(B,f"{c}.csv")
    if not os.path.exists(p): print(c,"MISSING"); continue
    with io.open(p,encoding="utf-8-sig") as f: rows=list(csv.DictReader(f))
    print("==",c)
    for r in rows:
        if r["date"]>="2026-10-14": print("  ",r["date"],"O",r["open"],"C",r["close"],"H",r["high"],"L",r["low"])
