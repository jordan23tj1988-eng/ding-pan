# -*- coding: utf-8 -*-
import json, os, csv, statistics
B = r"D:\股票数据\市场数据\_学习"
M = r"D:\股票数据\市场数据"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
print("##### summary.json #####")
print(json.dumps(load_any(os.path.join(M,"20261016","summary.json")),ensure_ascii=False)[:2500])
print("\n##### zt_pool head #####")
with open(os.path.join(M,"20261016","zt_pool.csv"),encoding="utf-8-sig") as f:
    r=list(csv.DictReader(f))
print("rows",len(r),"cols",list(r[0].keys()))
for x in r[:3]: print(json.dumps(x,ensure_ascii=False))
print("\n##### zb_pool head #####")
with open(os.path.join(M,"20261016","zb_pool.csv"),encoding="utf-8-sig") as f:
    rb=list(csv.DictReader(f))
print("rows",len(rb),"cols",list(rb[0].keys()))
for x in rb[:3]: print(json.dumps(x,ensure_ascii=False))
print("\n##### dt_pool #####")
with open(os.path.join(M,"20261016","dt_pool.csv"),encoding="utf-8-sig") as f:
    rd=list(csv.DictReader(f))
print("rows",len(rd),"cols",list(rd[0].keys()))
for x in rd[:12]: print(json.dumps(x,ensure_ascii=False)[:300])
