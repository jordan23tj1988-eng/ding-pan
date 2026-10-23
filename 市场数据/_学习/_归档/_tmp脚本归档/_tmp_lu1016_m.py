# -*- coding: utf-8 -*-
import json, os
B = r"D:\股票数据\市场数据\_学习"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
m = load_any(os.path.join(B,"总审_20261015.json"))
for k in ["指派清单","线索跟踪","能力承接","发布门禁"]:
    v = m.get(k)
    print("\n#### ",k, type(v))
    if isinstance(v,list):
        for x in v:
            s=json.dumps(x,ensure_ascii=False)
            if "limitup" in s or True:
                print(" -", s[:1200])
    else:
        print(json.dumps(v,ensure_ascii=False)[:2000])
