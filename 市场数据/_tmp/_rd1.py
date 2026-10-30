# -*- coding: utf-8 -*-
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def show(p, limit=None):
    print('='*20, p, '='*20)
    try:
        t = open(B+p, encoding='utf-8-sig').read()
    except Exception as e:
        print('ERR', e); return
    if limit: t = t[:limit]
    print(t)

for p in ['_学习/子agent增强/战绩画像_logic_20261029.json',
          '_学习/子agent增强/_战绩画像汇总_20261029.json']:
    show(p, 8000)
