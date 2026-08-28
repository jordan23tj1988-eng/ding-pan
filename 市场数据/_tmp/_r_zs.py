# -*- coding: utf-8 -*-
import json
X = "D:/股票数据/市场数据/_学习"
d = json.load(open(X + "/总审_20260825.json", encoding="utf-8"))
print("keys:", list(d.keys()))
for k in d:
    if "指派" in k or "深挖" in k:
        print("==", k, "==")
        print(json.dumps(d[k], ensure_ascii=False, indent=1)[:4000])
