# -*- coding: utf-8 -*-
import json, os
B = r"D:\股票数据\市场数据\_学习"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
s = load_any(os.path.join(B,"质量荐票结算_20261015.json"))
print("#### 结算 keys", list(s.keys()) if isinstance(s,dict) else "")
print(json.dumps(s,ensure_ascii=False)[:5000])
