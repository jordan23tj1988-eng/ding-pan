# -*- coding: utf-8 -*-
import json, io, os
base = r'D:\股票数据\市场数据\_学习'
t = json.load(io.open(os.path.join(base, '_市场温度表.json'), encoding='utf-8'))
for d in ['20260814', '20260817', '20260818']:
    if d in t:
        x = t[d]
        print(d, '涨停', x['涨停数'], '炸板', x['炸板数'], '炸板率', round(x['炸板率'], 3), '跌停', x['跌停数'],
              '温度', x['温度'], '温度档', x.get('温度档'), '最高板', x['最高板'], '二板加', x['二板加'], '梯队', x['梯队'],
              '成交额亿', x.get('成交额亿'), '封板总额亿', x.get('封板总额亿'))
print('--- 先行指标 ---')
x = json.load(io.open(os.path.join(base, '_情绪先行指标.json'), encoding='utf-8'))
for d in ['20260814', '20260817', '20260818']:
    if d in x:
        y = x[d]
        print(d, '晋级', json.dumps(y.get('晋级'), ensure_ascii=False), '昨日涨停溢价', json.dumps(y.get('昨日涨停溢价'), ensure_ascii=False))
