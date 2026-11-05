# -*- coding: utf-8 -*-
"""20261105 limitup：结算核对 + 因子核对 + 昨日本路荐票/高度轴票今日表现。"""
import os, json
import pandas as pd, numpy as np
BASE = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(BASE, '_学习')
CDIR = os.path.join(L, '_bars_cache')
P = pd.read_pickle(os.path.join(L, '_tmp_P_20261105.pkl'))
lib = json.load(open(os.path.join(L, '_涨停质量库.json'), encoding='utf-8'))
T = '20261105'

def bars(c):
    f = os.path.join(CDIR, c+'.csv')
    if not os.path.isfile(f): return None
    b = pd.read_csv(f); b['date'] = b['date'].astype(str).str.replace('-', ''); return b

def perf(c, d=T):
    b = bars(c)
    if b is None: return None
    i = np.where(b['date'].values == d)[0]
    if not len(i) or i[0] < 1: return None
    i = int(i[0])
    o, h, lo, cl, pc = b['open'].values[i], b['high'].values[i], b['low'].values[i], b['close'].values[i], b['close'].values[i-1]
    return dict(代码=c, gap=round((o/pc-1)*100, 2), E1=round((cl/o-1)*100, 2), 当日涨=round((cl/pc-1)*100, 2),
                high=round((h/pc-1)*100, 2), low=round((lo/pc-1)*100, 2), open=o, close=cl)

print('=== 昨日本路荐票/观察今日实测(T=20261105)')
for c in ['002992', '688809', '002980', '002652']:
    print(perf(c))

print('\n=== 高度轴票今日状态(昨日条款④)')
zt = pd.read_csv(os.path.join(BASE, T, 'zt_pool.csv'), dtype={'代码': str}); zt['代码'] = zt['代码'].str.zfill(6)
zb = pd.read_csv(os.path.join(BASE, T, 'zb_pool.csv'), dtype={'代码': str}); zb['代码'] = zb['代码'].str.zfill(6)
for c in ['002827', '605577', '002058', '600261', '000995', '002086']:
    tag = '涨停' if c in set(zt['代码']) else ('炸板' if c in set(zb['代码']) else '—')
    print(c, tag, perf(c))

print('\n=== 换手率因子（库现值）')
f = lib['因子'].get('换手率')
print({k: f.get(k) for k in ['权重', '区分度', 'rho', '状态', 'RankIC', 'ICIR', 'IC_t', '近20RankIC'] if k in f})
for k, v in (f.get('桶') or {}).items():
    print('  桶', k, {kk: v.get(kk) for kk in ['n', '执1胜率', '执1均涨', '执2胜率', '执2均涨', '抓龙率']})
print('活跃因子', lib['活跃因子'])
print('基准', lib['基准'])

D = P[P['E1'].notna()].copy()
def tb(x):
    if x is None or x != x: return '?'
    return '<3' if x < 3 else '3-10' if x < 10 else '10-20' if x < 20 else '20+'
D['换手桶'] = D['换手'].map(tb)
print('\n=== 我自算 换手率桶（全样本 n=%d）' % len(D))
for k in ['<3', '3-10', '10-20', '20+']:
    g = D[D['换手桶'] == k]['E1'].dropna()
    print('  %-6s n=%-5d 执1胜率 %5.1f%% 均收 %+6.2f%%' % (k, len(g), (g > 0).mean()*100, g.mean()*100))
wt = json.load(open(os.path.join(L, '_市场温度表.json'), encoding='utf-8'))
D['温度'] = [((wt.get(d) or {}) if isinstance(wt.get(d), dict) else {}).get('温度') for d in D['日']]
mid = D[(D['温度'] >= 45) & (D['温度'] < 65)]
print('  中温档 45-65x 换手桶 (n=%d):' % len(mid))
for k in ['<3', '3-10', '10-20', '20+']:
    g = mid[mid['换手桶'] == k]['E1'].dropna()
    if len(g): print('    %-6s n=%-5d %5.1f%% %+6.2f%%' % (k, len(g), (g > 0).mean()*100, g.mean()*100))
r = D[D['日'] >= '20260901']
print('  20260901起 换手桶:')
for k in ['<3', '3-10', '10-20', '20+']:
    g = r[r['换手桶'] == k]['E1'].dropna()
    if len(g): print('    %-6s n=%-5d %5.1f%% %+6.2f%%' % (k, len(g), (g > 0).mean()*100, g.mean()*100))

print('\n=== 涨停环境(分涨停总数档) 执1')
D['环境档'] = pd.cut(D['日'].map(lambda d: 0) + D.groupby('日')['代码'].transform('size'), [0, 45, 70, 100, 500], labels=['<45', '45-70', '70-100', '>=100'])
for k, g in D.groupby('环境档', observed=True):
    e = g['E1'].dropna(); print('  %-8s n=%-5d %5.1f%% %+6.2f%%' % (k, len(e), (e > 0).mean()*100, e.mean()*100))
