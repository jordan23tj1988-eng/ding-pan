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
print("top keys", list(y.keys()))
for k in y:
    if k=="判断": continue
    print("\n#### ",k)
    print(json.dumps(y[k],ensure_ascii=False)[:3500])
print("\n#### 判断.荐票/档位/置信度/可证伪")
for k in ["档位","置信度","可证伪条件","独立盲区声明","荐票"]:
    print("--",k,":",json.dumps(y["判断"].get(k),ensure_ascii=False)[:3000])
