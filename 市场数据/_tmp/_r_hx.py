# -*- coding: utf-8 -*-
import json
X = "D:/股票数据/市场数据/_学习"
d = json.load(open(X + "/子agent增强/战绩画像_theme_20260826.json", encoding="utf-8"))
print(json.dumps(d, ensure_ascii=False, indent=1)[:8000])
