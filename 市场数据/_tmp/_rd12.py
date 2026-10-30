# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p): return json.loads(open(p, encoding='utf-8-sig').read())
r = J(B+'_学习/中报预增雷达_20261029.json')
print('type', type(r).__name__)
if isinstance(r, dict):
    for k,v in r.items():
        print('KEY', k, '|', type(v).__name__, (len(v) if hasattr(v,'__len__') else ''))
        print(json.dumps(v, ensure_ascii=False)[:900])
        print()
