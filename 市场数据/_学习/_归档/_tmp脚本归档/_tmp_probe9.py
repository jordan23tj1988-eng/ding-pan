# -*- coding: utf-8 -*-
import json, os
L = r"D:/股票数据/市场数据/_学习"
def load(p):
    for enc in ("utf-8-sig","utf-8","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None

q = load(os.path.join(L, "涨停质量荐票_20261023.json"))
print("荐票 keys:", list(q.keys())[:20])
for k,v in q.items():
    if isinstance(v,(str,int,float)): print(" ", k, "=", str(v)[:200])
    elif isinstance(v,list): print(" ", k, "list", len(v))
    elif isinstance(v,dict): print(" ", k, "dict", list(v.keys())[:12])
