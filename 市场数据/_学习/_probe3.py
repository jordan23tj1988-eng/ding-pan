# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
L = r"D:/股票数据/市场数据/_学习"

def load(n):
    return json.load(open(L + "/" + n, encoding='utf-8'))

for route, fn in [("auction","auction判断_20261015.json"),("lhb","lhb判断_20261015.json"),
                  ("theme","theme判断_20261015.json"),("logic","logic判断_20261015.json"),
                  ("limitup","limitup判断_20261015.json")]:
    d = load(fn)
    print("="*20, route, "top keys:", list(d.keys()))

print("#### 交易计划五路 ####")
for route in ["auction","lhb","theme","logic","limitup"]:
    d = load("交易计划_%s_20261015.json" % route)
    print("="*25, route)
    print(json.dumps(d, ensure_ascii=False)[:3000])
