# -*- coding: utf-8 -*-
import json, os, csv
BASE = "D:/股票数据/市场数据"; X = BASE + "/_学习"
def load(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except FileNotFoundError: return None
        except Exception: continue
    return None

print("#### 战绩画像_theme_20260826 ####")
print(json.dumps(load(X+"/子agent增强/战绩画像_theme_20260826.json"), ensure_ascii=False, indent=1)[:4000])
print("\n#### 模拟盘 theme 状态.json ####")
print(json.dumps(load(X+"/_模拟盘/theme/状态.json"), ensure_ascii=False, indent=1)[:4000])
print("\n#### 总审_20260825 指派清单 ####")
zs = load(X+"/总审_20260825.json")
if zs:
    print("keys:", list(zs.keys()))
    for k in zs:
        if "指派" in k:
            print(json.dumps(zs[k], ensure_ascii=False, indent=1))
print("\n#### 题材荐票_20260825(昨日发出版) ####")
print(json.dumps(load(X+"/题材荐票_20260825.json"), ensure_ascii=False, indent=1))
print("\n#### 题材荐票结算_20260825 ####")
print(json.dumps(load(X+"/题材荐票结算_20260825.json"), ensure_ascii=False, indent=1)[:3500])
