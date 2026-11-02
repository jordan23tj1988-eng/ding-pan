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
lc = L("题材生命周期_20261030.json")
print("=== 昨日生命周期 keys", list(lc.keys()))
print("摘要:", json.dumps(lc.get('摘要'), ensure_ascii=False))
print("结算:", json.dumps(lc.get('结算'), ensure_ascii=False)[:3000])
# 结算 jsonl tail
import io
p = base+"_题材生命周期结算.jsonl"
lines = [l for l in open(p, encoding='utf-8').read().splitlines() if l.strip()]
print("\n结算jsonl 行数", len(lines))
for l in lines[-3:]:
    print(json.dumps(json.loads(l), ensure_ascii=False)[:3000])
