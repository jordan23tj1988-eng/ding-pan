# -*- coding: utf-8 -*-
import sys, io, json
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:/股票数据/市场数据/'
df = pd.read_csv(B + '_tmp/_bucket_rows.csv', dtype={'code': str, 'd': str})
def layer(t):
    if t != t: return '未知'
    t = float(t)
    return '冰点<25' if t < 25 else ('冷25~40' if t < 40 else ('中40~65' if t < 65 else '热>=65'))
df['ly'] = df.temp.map(layer)
df['line_n'] = df.groupby(['d', 'dn']).code.transform('count')

def stat(sub, label):
    s = sub.dropna(subset=['ret'])
    n = len(s)
    if not n: print(f'{label:<40} n=0'); return
    w = int((s.ret > 0).sum())
    print(f'{label:<40} n={n:<4} 胜率={w}/{n}={round(w/n*100,1)}%  均收={round(s.ret.mean(),2):>6}')

print('=== 全样本基线 ===')
stat(df[df.lb == 1], '全部首板')
for ly, g in df[df.lb == 1].groupby('ly'):
    stat(g, '全部首板 ' + ly)

print('\n=== 商业航天 首板 逐日 ===')
s = df[(df.dn.str.contains('商业航天', na=False)) & (df.lb == 1)]
for d, g in s.groupby('d'):
    stat(g, f'{d} 温度{g.temp.iloc[0]} 线内{g.line_n.iloc[0]}只')
print('\n=== 商业航天 首板 × 线内家数 ===')
stat(s[s.line_n <= 4], '线内≤4只')
stat(s[s.line_n >= 8], '线内≥8只(扩散日)')
stat(s[(s.line_n >= 8) & (s.ly == '冰点<25')], '线内≥8只 × 冰点')

print('\n=== 机器人 冰点层 逐日 ===')
r = df[(df.dn.str.contains('机器人', na=False)) & (df.lb == 1) & (df.ly == '冰点<25')]
for d, g in r.groupby('d'):
    stat(g, f'{d} 温度{g.temp.iloc[0]} 线内{g.line_n.iloc[0]}只')

print('\n=== 今日20261029 温度 ===')
print(df[df.d == '20261029'].temp.iloc[0])
print('\n=== 今日商业航天10只(无ret) ===')
print(df[(df.d == '20261029') & (df.dn.str.contains('商业航天', na=False))][['code','name','lb','fb','zha','fdb']].to_string(index=False))
