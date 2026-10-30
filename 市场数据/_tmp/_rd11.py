# -*- coding: utf-8 -*-
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p): return json.loads(open(p, encoding='utf-8-sig').read())
T = J(B+'产业链模板.json')
print('## 商业航天 环节')
for h, arr in T['商业航天']['环节'].items():
    print(' -', h, arr)
print('## 环节注', json.dumps(T['商业航天'].get('环节注',{}), ensure_ascii=False)[:800])

rows = list(csv.DictReader(open(B+'20261029/zt_pool.csv', encoding='utf-8-sig')))
codes = {r['代码']: r['名称'] for r in rows}
print('\n## 今日39只 在模板中的位置')
idx = {}
for sect, v in T.items():
    if sect=='说明': continue
    for h, arr in v.get('环节',{}).items():
        for c,n in arr:
            idx.setdefault(c, []).append(f'{sect}/{h}({n})')
for c,n in codes.items():
    print(c, n, '=>', idx.get(c, '不在任何模板环节'))
