# -*- coding: utf-8 -*-
import json
X = "D:/股票数据/市场数据/_学习"
t = json.load(open(X + "/_市场温度表.json", encoding="utf-8"))
if isinstance(t, dict):
    for k in ("20260825", "20260826"):
        print(k, "=", json.dumps(t.get(k), ensure_ascii=False)[:1200])
print()
s = json.load(open(X + "/_模拟盘/theme/状态.json", encoding="utf-8"))
print("状态.json =", json.dumps(s, ensure_ascii=False, indent=1)[:3500])
