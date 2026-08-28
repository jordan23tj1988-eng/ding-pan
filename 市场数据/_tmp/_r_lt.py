# -*- coding: utf-8 -*-
import json
X = "D:/股票数据/市场数据/_学习"
d = json.load(open(X + "/涨停对链条_20260826.json", encoding="utf-8"))
print("keys:", list(d.keys()))
s = json.dumps(d, ensure_ascii=False, indent=1)
print("len", len(s))
print(s[:9000])
