# -*- coding: utf-8 -*-
"""重算: 机器人线首板桶 / 商业航天线首板桶, 按温度分层 + 剔最强日; 执1=T+1收/T+1开-1"""
import sys, io, json, os, glob
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:/股票数据/市场数据/'
L = B + '_学习/'
CDIR = L + '_bars_cache/'
T = json.load(open(L + '_市场温度表.json', encoding='utf-8-sig'))

_cache = {}
def bars(c):
    if c in _cache: return _cache[c]
    f = CDIR + c + '.csv'
    if not os.path.isfile(f):
        _cache[c] = None; return None
    b = pd.read_csv(f)
    b['date'] = b['date'].astype(str).str.replace('-', '')
    _cache[c] = b; return b

def exe1(c, d):
    b = bars(c)
    if b is None: return None
    idx = b.index[b['date'] == d]
    if not len(idx): return None
    i = idx[0]
    if i + 1 >= len(b): return None
    o1 = b.loc[i+1, 'open']; c1 = b.loc[i+1, 'close']
    if not o1 or o1 != o1: return None
    return round((c1/o1 - 1)*100, 2)

def layer(t):
    if t is None: return '未知'
    if t < 25: return '冰点<25'
    if t < 40: return '冷25~40'
    if t < 65: return '中40~65'
    return '热>=65'

rows = []
files = sorted(glob.glob(L + '涨停对链条_*.json'))
for f in files:
    d = os.path.basename(f).split('_')[-1].replace('.json', '')
    try:
        j = json.load(open(f, encoding='utf-8-sig'))
    except Exception as e:
        print('ERR', d, e); continue
    temp = (T.get(d) or {}).get('温度')
    for line in j.get('题材线', []):
        dn = line.get('大方向', '')
        for huan in line.get('环节', []):
            for s in huan.get('个股', []):
                rows.append(dict(d=d, temp=temp, dn=dn, code=s['代码'], name=s.get('名称'),
                                 lb=s.get('连板'), fb=s.get('首封'), zha=s.get('开板次数'),
                                 fdb=s.get('封单比'), ret=exe1(s['代码'], d)))

df = pd.DataFrame(rows)
print('总样本行', len(df), '覆盖日', df.d.nunique(), '日期范围', df.d.min(), '~', df.d.max())
def stat(sub, label):
    s = sub.dropna(subset=['ret'])
    n = len(s); win = int((s.ret > 0).sum())
    avg = round(s.ret.mean(), 2) if n else None
    print(f'{label:<28} n={n:<4} 胜率={win}/{n}={round(win/n*100,1) if n else 0}%  均收={avg}')
    return n, win, avg

for kw in ['机器人', '商业航天']:
    sub = df[df.dn.str.contains(kw, na=False)]
    print('\n' + '='*18, kw, '线 全部', '='*18)
    for lb, g in sub.groupby('lb'):
        stat(g, f'{kw} {lb}板 合计')
    print('-- 首板 按温度分层 --')
    r1 = sub[sub.lb == 1]
    for ly, g in r1.groupby(r1.temp.map(layer)):
        stat(g, f'{kw} 首板 {ly}')
    # 剔最强日
    if len(r1.dropna(subset=['ret'])):
        best = r1.dropna(subset=['ret']).groupby('d').ret.mean().idxmax()
        print(f'-- 最强日 {best} 剔后 --')
        for ly, g in r1[r1.d != best].groupby(r1[r1.d != best].temp.map(layer)):
            stat(g, f'{kw} 首板 剔{best} {ly}')
df.to_csv(B + '_tmp/_bucket_rows.csv', index=False, encoding='utf-8-sig')
print('\n已写 _tmp/_bucket_rows.csv')
