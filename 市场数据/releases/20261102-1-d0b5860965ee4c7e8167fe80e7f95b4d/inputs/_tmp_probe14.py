# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
base = "D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p, encoding=enc) as f: return json.load(f)
        except Exception as e: last=e
    print("LOADFAIL", p, last); return None
wp = L("子agent增强/战绩画像_theme_20261102.json")
print("=== 战绩画像 keys", list(wp.keys()) if isinstance(wp,dict) else type(wp))
print(json.dumps(wp, ensure_ascii=False)[:3500])
print("\n=== 昨日龙头判断 ===")
ld = L("题材龙头判断_20261030.json")
print(json.dumps(ld, ensure_ascii=False)[:2500])
