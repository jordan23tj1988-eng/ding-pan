# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p): return json.loads(open(p, encoding='utf-8-sig').read())

t = J(B+'_学习/题材归位_20261029.json')
print('## 题材归位 keys', list(t.keys()))
for k,v in t.items():
    if isinstance(v,list): print(k,'list len',len(v)); print(json.dumps(v[:2],ensure_ascii=False)[:800])
    elif isinstance(v,dict): print(k,'dict keys',list(v.keys())[:20])
    else: print(k,'=',str(v)[:200])
