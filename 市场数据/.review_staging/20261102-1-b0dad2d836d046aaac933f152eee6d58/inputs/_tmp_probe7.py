# -*- coding: utf-8 -*-
import json, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
base = "D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p, encoding=enc) as f: return json.load(f)
        except Exception as e: last=e
    print("LOADFAIL", p, last); return None

th = L("theme判断_20261030.json")
print("=== 昨日theme判断 keys", list(th.keys()))
print("判断:", json.dumps(th['判断'], ensure_ascii=False)[:3000])
print("\n荐票:", json.dumps(th['荐票'], ensure_ascii=False)[:1600])
print("\n认知迭代:", json.dumps(th.get('认知迭代'), ensure_ascii=False)[:1500])
print("\n深挖:", json.dumps(th.get('深挖'), ensure_ascii=False)[:1500])
print("\n框架引用:", json.dumps(th.get('框架引用'), ensure_ascii=False)[:800])
print("\n主动查证:", json.dumps(th.get('主动查证'), ensure_ascii=False)[:500])
