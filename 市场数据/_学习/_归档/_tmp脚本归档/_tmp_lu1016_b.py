# -*- coding: utf-8 -*-
import json, os, csv, re
B = r"D:\股票数据\市场数据\_学习"
M = r"D:\股票数据\市场数据"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None

q = load_any(os.path.join(B,"涨停质量荐票_20261016.json"))
det = q["明细"]
print("detail len", len(det))
print("sample keys:", list(det[0].keys()))
# summary stats
for k in det[0].keys():
    v = det[0][k]
    if not isinstance(v,(list,dict)):
        print("  key:",k,"=",v)
