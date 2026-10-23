# -*- coding: utf-8 -*-
import os, csv
B = r"D:\股票数据\市场数据\_学习"
bd=os.path.join(B,"_bars_cache")
for c in ["605058","600812","002945","002815","600825"]:
    p=os.path.join(bd,c+".csv")
    print(c, os.path.exists(p))
    if os.path.exists(p):
        rows=list(csv.DictReader(open(p,encoding="utf-8-sig")))
        print("  rows",len(rows),"last3:",[(r["date"],r["open"],r["close"]) for r in rows[-4:]])
print("\n质量荐票_20261015 exists:", os.path.exists(os.path.join(B,"涨停质量荐票_20261015.json")))
print("能力回执_lhb_20261016 exists:", os.path.exists(os.path.join(B,"能力回执_lhb_20261016.json")))
print("温度表 exists:", os.path.exists(os.path.join(B,"_市场温度表.json")))
