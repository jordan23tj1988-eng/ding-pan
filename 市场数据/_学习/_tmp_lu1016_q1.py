# -*- coding: utf-8 -*-
import json, os
B=r"D:\股票数据\市场数据\_学习"
def L(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p,encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
g=L(os.path.join(B,"题材归位_20261016.json"))
print("#### 题材归位 keys", list(g.keys()) if isinstance(g,dict) else type(g))
if isinstance(g,dict):
    for k,v in g.items():
        if isinstance(v,list): print(k,"list",len(v), json.dumps(v[0],ensure_ascii=False)[:500] if v else "")
        elif isinstance(v,dict): print(k,"dict",list(v.keys())[:15])
        else: print(k,"=",str(v)[:300])
print("\n#### 方向聚合")
for k in ["方向聚合","方向榜","聚合"]:
    if isinstance(g,dict) and k in g:
        print(json.dumps(g[k],ensure_ascii=False)[:3000])
