# -*- coding: utf-8 -*-
import sys, io, json, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p):
    return json.loads(open(p, encoding='utf-8-sig').read())

print('### 风险日历')
print(open(B+'_学习/风险日历_20261029.json', encoding='utf-8-sig').read()[:3000])

print('### 状态.json logic')
p = B+'_学习/_模拟盘/logic/状态.json'
print('exists', os.path.exists(p))
if os.path.exists(p):
    s = J(p)
    print(json.dumps(s, ensure_ascii=False, indent=1)[:5000])

print('### summary')
print(json.dumps(J(B+'20261029/summary.json'), ensure_ascii=False, indent=1)[:3000])
