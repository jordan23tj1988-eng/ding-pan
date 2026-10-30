# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p): return json.loads(open(p, encoding='utf-8-sig').read())
t = J(B+'产业链模板.json')
print('## 产业链模板 keys', list(t.keys()))
for k in t:
    print('---', k, '->', json.dumps(t[k], ensure_ascii=False)[:400])
print()
d = J(B+'_学习/链条纵深库.json')
print('## 纵深库 keys', list(d.keys()) if isinstance(d,dict) else len(d))
print(json.dumps(d, ensure_ascii=False)[:3000])
