# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p): return json.loads(open(p, encoding='utf-8-sig').read())
t = J(B+'_学习/产业链模板.json')
print('## 产业链模板 type', type(t).__name__, list(t.keys())[:40] if isinstance(t,dict) else len(t))
s = json.dumps(t, ensure_ascii=False)
print('len chars', len(s))
for k in (list(t.keys())[:6] if isinstance(t,dict) else []):
    print('---', k, json.dumps(t[k], ensure_ascii=False)[:600])
print()
d = J(B+'_学习/链条纵深库.json')
print('## 链条纵深库 keys', list(d.keys())[:40] if isinstance(d,dict) else len(d))
print(json.dumps(d, ensure_ascii=False)[:2500])
