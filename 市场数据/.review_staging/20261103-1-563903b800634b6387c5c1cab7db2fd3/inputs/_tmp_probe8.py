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

m = L("总审_20261030.json")
print("总审 keys:", list(m.keys()))
for k in m:
    if '指派' in k:
        print("\n==",k,"==")
        print(json.dumps(m[k], ensure_ascii=False)[:6000])
