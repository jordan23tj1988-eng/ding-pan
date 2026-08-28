# -*- coding: utf-8 -*-
import json
X = "D:/股票数据/市场数据/_学习"
p = X + "/_题材四维.json"
d = json.load(open(p, encoding="utf-8"))
print(type(d), list(d.keys())[:8] if isinstance(d, dict) else len(d))
print(json.dumps(d.get("20260826", d), ensure_ascii=False, indent=1)[:9000])
