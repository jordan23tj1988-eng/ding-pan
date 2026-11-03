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
s6 = L("主流题材6有_20261102.json")
print("全场判定:", json.dumps(s6['全场判定'], ensure_ascii=False))
print("阈值:", json.dumps(s6['阈值'], ensure_ascii=False))
print("口径注:", s6.get('口径注'))
print("\n-- 聚类口径 --")
for r in s6['题材_聚类口径']:
    print(json.dumps(r, ensure_ascii=False))
print("\n-- 行业口径 top --")
for r in s6['题材'][:8]:
    print(json.dumps(r, ensure_ascii=False))

lc = L("题材生命周期_20261102.json")
print("\n=== 生命周期 摘要 ===")
print(json.dumps(lc['摘要'], ensure_ascii=False))
print("\n=== 阶段表 ===")
print(json.dumps(lc['阶段表'], ensure_ascii=False))
print("\n=== 转移矩阵 ===")
print(json.dumps(lc['转移矩阵'], ensure_ascii=False))
