# -*- coding: utf-8 -*-
import json, os
B = r"D:\股票数据\市场数据\_学习"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
print("#### 能力预加载 routes.limitup")
c = load_any(os.path.join(B,"能力预加载_20261016.json"))
print("keys", list(c.keys()))
print(json.dumps(c.get("routes",{}).get("limitup"),ensure_ascii=False)[:3000])
print("\n#### 能力回执_lhb_20261016 键结构")
r = load_any(os.path.join(B,"能力回执_lhb_20261016.json"))
print(json.dumps(r,ensure_ascii=False)[:1800])
print("\n#### 四美选股法_D组 exists?", os.path.exists(os.path.join(B,"四美选股法_D组.md")))
print("\n#### 总审_20261015 keys")
m = load_any(os.path.join(B,"总审_20261015.json"))
print(list(m.keys()) if isinstance(m,dict) else type(m))
s = json.dumps(m,ensure_ascii=False)
import re
for kw in ["limitup"]:
    for mt in re.finditer("limitup", s):
        print("...", s[max(0,mt.start()-300):mt.start()+500].replace("\n"," "))
        print("-----")
