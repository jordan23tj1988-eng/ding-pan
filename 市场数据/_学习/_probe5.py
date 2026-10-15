# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
L = r"D:/股票数据/市场数据/_学习"
def load(n): return json.load(open(L+"/"+n, encoding='utf-8'))

d = load("总审_20261015.json")
for k in ["五路裁决","分歧点","分歧裁决","总裁决","检查四项","发布门禁","指派清单","认知迭代"]:
    print("="*30, k)
    print(json.dumps(d.get(k), ensure_ascii=False)[:7000])
    print()

print("="*30, "竞价池发出")
print(json.dumps(load("竞价池发出_20261015.json"), ensure_ascii=False)[:2500])
print("="*30, "竞价评分")
print(json.dumps(load("竞价评分_20261015.json"), ensure_ascii=False)[:3500])
