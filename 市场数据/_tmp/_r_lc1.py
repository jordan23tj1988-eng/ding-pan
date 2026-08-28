# -*- coding: utf-8 -*-
import json
X = "D:/股票数据/市场数据/_学习"
d = json.load(open(X + "/题材生命周期_20260826.json", encoding="utf-8"))
print("keys:", list(d.keys()))
for k in d:
    if k != "逐线":
        print("--", k, "=", json.dumps(d[k], ensure_ascii=False)[:1500])
