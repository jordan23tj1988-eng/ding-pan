# -*- coding: utf-8 -*-
import json, os
B = r"D:\股票数据\市场数据\_学习"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
p=os.path.join(B,"_ma07_limitup_20261015.json")
d=load_any(p)
print("keys:", list(d.keys()))
for k,v in d.items():
    if isinstance(v,dict):
        print(k,"dict keys",list(v.keys())[:12])
    elif isinstance(v,list):
        print(k,"list len",len(v), json.dumps(v[0],ensure_ascii=False)[:300] if v else "")
    else:
        print(k,"=",str(v)[:300])
print("\n#### bars_cache")
bd=os.path.join(B,"_bars_cache")
fs=os.listdir(bd)
print(len(fs), fs[:8])
print("\n#### sample bar file")
import io
f0=os.path.join(bd,fs[0])
print(f0)
print(open(f0,encoding="utf-8-sig").read()[:600])
