# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
L = r"D:/股票数据/市场数据/_学习"
def load(n):
    return json.load(open(L+"/"+n, encoding='utf-8'))

for route, fn in [("auction","auction判断_20261015.json"),("lhb","lhb判断_20261015.json"),
                  ("theme","theme判断_20261015.json"),("logic","logic判断_20261015.json"),
                  ("limitup","limitup判断_20261015.json")]:
    d = load(fn)
    print("#"*30, route, "判断")
    print(json.dumps(d.get("判断"), ensure_ascii=False)[:6000])
    print()

d = load("总审_20261015.json")
def walk(o, pre=""):
    if isinstance(o, dict):
        for k,v in o.items():
            if isinstance(v,(dict,list)):
                print(pre+k, type(v).__name__, (len(v) if isinstance(v,(list,dict)) else ""))
            else:
                print(pre+k, "=", str(v)[:200])
walk(d)
