# -*- coding: utf-8 -*-
import json, os, re, statistics, csv
B = r"D:\股票数据\市场数据\_学习"
M = r"D:\股票数据\市场数据"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
def show(o, n=8, w=600):
    if isinstance(o, dict):
        for k,v in list(o.items())[:n]:
            s = v if isinstance(v,str) else json.dumps(v, ensure_ascii=False)
            print("  ",k,"=",s[:w])
    elif isinstance(o,list):
        print("  list len",len(o))
        for x in o[:n]:
            print("   -", (x if isinstance(x,str) else json.dumps(x,ensure_ascii=False))[:w])

print("########## 质量库 ##########")
ql = load_any(os.path.join(B,"_涨停质量库.json"))
print("keys:", list(ql.keys()))
show(ql, 14)
