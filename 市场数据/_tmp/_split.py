# -*- coding: utf-8 -*-
import sys, io, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
df = pd.read_csv(B + '_tmp/_bucket_rows.csv', dtype={'code': str, 'd': str})  # 55日 涨停对链条
def layer(t):
    if t != t: return '未知'
    t = float(t)
    return '冰点<25' if t < 25 else ('冷25~40' if t < 40 else ('中40~65' if t < 65 else '热>=65'))
df['ly'] = df.temp.map(layer)
r = df[(df.dn.str.contains('机器人', na=False)) & (df.lb == 1)].dropna(subset=['ret'])
print('== 机器人首板 55日 冰点层 按时段拆分 ==')
for lab, sub in [('20260707~20260918', r[(r.ly == '冰点<25') & (r.d < '20260920')]),
                 ('20260920~20261029', r[(r.ly == '冰点<25') & (r.d >= '20260920')])]:
    n = len(sub); w = int((sub.ret > 0).sum())
    print(f'{lab}  n={n} 胜率={w}/{n}={round(w/n*100,1)}% 均收={round(sub.ret.mean(),2)} 中位={round(sub.ret.median(),2)}')
print('== 冷层 按时段 ==')
for lab, sub in [('20260707~20260918', r[(r.ly == '冷25~40') & (r.d < '20260920')]),
                 ('20260920~20261029', r[(r.ly == '冷25~40') & (r.d >= '20260920')])]:
    n = len(sub); w = int((sub.ret > 0).sum())
    print(f'{lab}  n={n} 胜率={w}/{n}={round(w/n*100,1) if n else 0}% 均收={round(sub.ret.mean(),2) if n else None}')
