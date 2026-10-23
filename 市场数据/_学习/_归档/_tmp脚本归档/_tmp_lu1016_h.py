# -*- coding: utf-8 -*-
import json, os
B = r"D:\股票数据\市场数据\_学习"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
y = load_any(os.path.join(B,"limitup判断_20261015.json"))
print("##### 昨日 limitup判断 #####")
print(json.dumps(y, ensure_ascii=False)[:6000])
