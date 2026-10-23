# -*- coding: utf-8 -*-
import json, os
B=r"D:\股票数据\市场数据\_学习"
def L(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p,encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
f=L(os.path.join(B,"fact_20261016.json"))
print("#### fact_20261016 keys", list(f.keys()) if isinstance(f,dict) else type(f))
if isinstance(f,dict):
    for k,v in f.items():
        s=v if isinstance(v,str) else json.dumps(v,ensure_ascii=False)
        print(" ",k,"=",s[:600])
print("\n#### 涨停原因 samples")
z=L(os.path.join(B,"涨停原因_20261016.json"))
print(type(z), list(z.keys())[:5] if isinstance(z,dict) else len(z))
def show(c):
    if isinstance(z,dict):
        for k in z:
            if c in k: print("  ",k,z[k] if isinstance(z[k],str) else json.dumps(z[k],ensure_ascii=False)[:400])
    elif isinstance(z,list):
        for x in z:
            if x.get("代码")==c or x.get("code")==c: print("  ",json.dumps(x,ensure_ascii=False)[:500])
for c in ["000530","300045","301586","002917","600802","600825","920006"]:
    show(c)
