# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p): return json.loads(open(p, encoding='utf-8-sig').read())
t = J(B+'_学习/题材归位_20261029.json')
print('## 方向聚合')
print(json.dumps(t['方向聚合'], ensure_ascii=False, indent=1))
print('## 映射 全量')
for c,m in t['映射'].items():
    print(c, json.dumps(m, ensure_ascii=False))
