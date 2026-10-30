# -*- coding: utf-8 -*-
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p): return json.loads(open(p, encoding='utf-8-sig').read())

print('### zt_pool 表头+行')
rows = list(csv.DictReader(open(B+'20261029/zt_pool.csv', encoding='utf-8-sig')))
print('rows', len(rows), 'fields', list(rows[0].keys()))
for r in rows:
    print(r.get('代码'), r.get('名称'), '连板', r.get('连板数') or r.get('连板'), r.get('所属行业',''), '|', (r.get('涨停原因') or r.get('涨停原因类别') or '')[:40])
