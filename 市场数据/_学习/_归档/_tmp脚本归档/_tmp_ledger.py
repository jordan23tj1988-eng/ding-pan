# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
S = os.path.join(L,"_模拟盘","limitup")
for f in os.listdir(S):
    print(f, os.path.getsize(os.path.join(S,f)))
print("\n=== 状态.json ===")
print(open(os.path.join(S,"状态.json"), encoding="utf-8").read()[:2500])
for nm in ("净值.json","state.json"):
    p = os.path.join(S,nm)
    if os.path.exists(p):
        print("\n=== %s ===" % nm)
        print(open(p, encoding="utf-8").read()[:1500])
