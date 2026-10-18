# -*- coding: utf-8 -*-
import json, os
B=r"D:\股票数据\市场数据\_学习"
f=json.load(open(os.path.join(B,"fact_20261016.json"),encoding="utf-8"))
print(json.dumps(f["facts"],ensure_ascii=False)[:4000])
z=json.load(open(os.path.join(B,"涨停原因_20261016.json"),encoding="utf-8"))
print("\nkeys:",list(z.keys()))
for k,v in z.items():
    if isinstance(v,list): print(k,"list",len(v),json.dumps(v[0],ensure_ascii=False)[:300] if v else "")
    elif isinstance(v,dict): print(k,"dict",list(v.keys())[:8])
    else: print(k,"=",str(v)[:200])
