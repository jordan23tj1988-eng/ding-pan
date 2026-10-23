# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
d = json.load(open(os.path.join(L,"子agent增强","战绩画像_limitup_20261023.json"), encoding="utf-8"))
print("keys:", list(d.keys()))
s = json.dumps(d, ensure_ascii=False, indent=1)
print(s[:4000])
