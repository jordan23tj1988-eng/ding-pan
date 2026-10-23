# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
d = json.load(open(os.path.join(L,"子agent增强","战绩画像_limitup_20261023.json"), encoding="utf-8"))
for x in d["按日"]:
    if x["荐票日"] >= "20261012":
        print(json.dumps(x, ensure_ascii=False))
print("\n合计:", json.dumps(d.get("合计"), ensure_ascii=False, indent=1)[:1500])
print("\n归因:", json.dumps(d.get("归因"), ensure_ascii=False, indent=1)[:1200])
