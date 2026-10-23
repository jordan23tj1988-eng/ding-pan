# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
d = json.load(open(os.path.join(L,"能力预加载_20261023.json"), encoding="utf-8"))
print("top keys:", list(d.keys()))
r = d.get("routes",{}).get("limitup")
print(json.dumps(r, ensure_ascii=False, indent=1)[:2000])
