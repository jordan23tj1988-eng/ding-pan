# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p): return json.loads(open(p, encoding='utf-8-sig').read())
t = J(B+'_学习/涨停对链条_20261029.json')
print('## 涨停对链条 keys', list(t.keys()))
for k,v in t.items():
    if isinstance(v,(list,dict)):
        print(k, type(v).__name__, len(v))
        print(json.dumps(v, ensure_ascii=False)[:1500])
    else: print(k,'=',v)
