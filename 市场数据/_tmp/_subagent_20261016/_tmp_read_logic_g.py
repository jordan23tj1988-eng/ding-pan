# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/_学习/'
def rd(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

print("===== 链条纵深库 =====")
print(json.dumps(rd(B+'链条纵深库.json'), ensure_ascii=False, indent=1)[:6000])

print("\n===== 涨停对链条_20261016 (keys) =====")
ztl = rd(B+'涨停对链条_20261016.json')
print("keys:", list(ztl.keys()) if isinstance(ztl,dict) else type(ztl))
print(json.dumps(ztl, ensure_ascii=False, indent=1)[:5000])
