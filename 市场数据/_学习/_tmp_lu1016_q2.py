# -*- coding: utf-8 -*-
import json, os
B=r"D:\股票数据\市场数据\_学习"
def L(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p,encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
d=L(os.path.join(B,"龙虎榜双源校验_20261016.json"))
print("keys",list(d.keys()) if isinstance(d,dict) else type(d))
for k,v in (d.items() if isinstance(d,dict) else []):
    if isinstance(v,list): print(k,"list",len(v));print("  first:",json.dumps(v[0],ensure_ascii=False)[:400] if v else "")
    elif isinstance(v,dict): print(k,"dict",list(v.keys())[:10])
    else: print(k,"=",str(v)[:200])
# 找强矛盾
s=json.dumps(d,ensure_ascii=False)
print("\n强矛盾 count:", s.count("强矛盾"))
recs=None
for k in d:
    if isinstance(d[k],list) and d[k] and isinstance(d[k][0],dict) and any("矛盾" in str(x) for x in d[k][0].values()):
        recs=d[k]; print("records key=",k); break
if recs:
    for r in recs:
        if "强矛盾" in json.dumps(r,ensure_ascii=False):
            print("  ",json.dumps(r,ensure_ascii=False)[:400])
print("\n=== 我的候选在不在 ===")
for c in ["000530","300045","301586","002917","600668","600802","920006","000420"]:
    idx=s.find(c)
    print(c, "found" if idx>=0 else "NOT", s[max(0,idx-120):idx+260].replace("\n"," ") if idx>=0 else "")
