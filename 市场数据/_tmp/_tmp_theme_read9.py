# -*- coding: utf-8 -*-
import csv, io, os
BASE = "D:/股票数据/市场数据"
def rd(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with open(p, encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception: continue
    return []
r26 = rd(BASE+"/20260826/zt_pool.csv")
print("cols:", list(r26[0].keys()) if r26 else "EMPTY")
print("n=", len(r26))
want = {"000017","003040","002084","002742","002855","002418","000428","002094","600371","002949","002963","002703","600103","002721","301177","601212","002295","603979","600362"}
for row in r26:
    c = row.get("代码") or row.get("code")
    if c in want:
        print({k:v for k,v in row.items()})
print("\n--- 昨日20260825 涨停代码集(用于荐票合法性) ---")
r25 = rd(BASE+"/20260825/zt_pool.csv")
cs = [ (row.get("代码") or row.get("code")) for row in r25 ]
print(len(cs), cs)
