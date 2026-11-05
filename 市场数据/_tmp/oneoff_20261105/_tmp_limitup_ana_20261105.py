# -*- coding: utf-8 -*-
"""20261105 limitup 路：今日池结构 + 昨日池执1 + 格重算（开板分层）。"""
import os, json, glob
import pandas as pd, numpy as np

BASE = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(BASE, '_学习')
CDIR = os.path.join(L, '_bars_cache')
P = pd.read_pickle(os.path.join(L, '_tmp_P_20261105.pkl'))
TODAY = '20261105'; PREV = '20261104'

def bars(c):
    f = os.path.join(CDIR, c+'.csv')
    if not os.path.isfile(f): return None
    b = pd.read_csv(f); b['date'] = b['date'].astype(str).str.replace('-', '')
    return b

def fb(s):
    s = str(s).split('.')[0].zfill(6)
    return s[:2]+':'+s[2:4]

def head_bucket(t):
    if t is None: return '?'
    if t <= '09:25': return '一字≤9:25'
    if t <= '09:31': return '秒板≤9:31'
    if t <= '10:00': return '早盘≤10:00'
    if t <= '14:00': return '盘中10-14'
    return '尾盘>14:00'

def to_bucket(x):
    if x is None or x != x: return '?'
    if x < 3: return '<3%'
    if x < 10: return '3-10%'
    if x < 20: return '10-20%'
    return '≥20%'

def st(v):
    v = pd.Series(v).dropna()
    if not len(v): return (0, None, None)
    return (len(v), round((v > 0).mean()*100, 1), round(v.mean()*100, 2))

# ---------- 1 今日池 ----------
zt = pd.read_csv(os.path.join(BASE, TODAY, 'zt_pool.csv'), dtype={'代码': str})
zt['代码'] = zt['代码'].str.zfill(6)
zt['首封'] = zt['首次封板时间'].map(fb)
zt['末封'] = zt['最后封板时间'].map(fb)
zt['流通亿'] = zt['流通市值']/1e8
zt['封单比'] = zt['封板资金']/zt['流通市值']*100
zt['成交亿'] = zt['成交额']/1e8
zt['开板'] = zt['炸板次数'].astype(int)
zt['连板'] = zt['连板数'].astype(int)
zt['时段'] = zt['首封'].map(head_bucket)
zt['换手桶'] = zt['换手率'].map(to_bucket)
print('=== 今日池 n=%d' % len(zt))
print('梯队', zt['连板'].value_counts().sort_index().to_dict())
print('首封时段', zt['时段'].value_counts().to_dict())
print('开板分布', zt['开板'].value_counts().sort_index().to_dict())
print('开板分组', {'0': int((zt['开板'] == 0).sum()), '1-2': int(zt['开板'].between(1, 2).sum()), '>=3': int((zt['开板'] >= 3).sum())})
print('换手桶', zt['换手桶'].value_counts().to_dict())
print('封板总额亿 %.2f 单票 %.3f 封单比中位 %.3f 均值 %.3f' % (zt['封板资金'].sum()/1e8, zt['封板资金'].mean()/1e8, zt['封单比'].median(), zt['封单比'].mean()))
print('流通≥100亿 %d (%.1f%%)  中位 %.1f亿' % ((zt['流通亿'] >= 100).sum(), (zt['流通亿'] >= 100).mean()*100, zt['流通亿'].median()))
print('末封≥14:30 %d ; 炸0即封 %d ; 10cm/20cm/30cm' % ((zt['末封'] >= '14:30').sum(), (zt['开板'] == 0).sum()))
zt['cm'] = np.where(zt['代码'].str[:2].isin(['30', '68']), '20cm', np.where(zt['代码'].str[0].isin(['4', '8', '9']), '30cm', '10cm'))
print(zt['cm'].value_counts().to_dict())
print('行业Top', zt['所属行业'].value_counts().head(8).to_dict())
print('连板≥2 名单:')
print(zt[zt['连板'] >= 2][['代码', '名称', '连板', '首封', '末封', '开板', '换手率', '流通亿', '封单比', '所属行业']].to_string(index=False))

# ---------- 2 昨日池今日执1 ----------
zb = pd.read_csv(os.path.join(BASE, PREV, 'zt_pool.csv'), dtype={'代码': str})
zb['代码'] = zb['代码'].str.zfill(6)
zb['连板'] = zb['连板数'].astype(int)
prev_ladder = zb['连板'].value_counts().sort_index().to_dict()
print('\n=== 昨日(%s)池 n=%d 梯队 %s' % (PREV, len(zb), prev_ladder))
e1s = []; gs = []
for c in zb['代码']:
    b = bars(c)
    if b is None: continue
    i = np.where(b['date'].values == PREV)[0]
    if not len(i): continue
    i = int(i[0])
    if i+1 >= len(b): continue
    Tc = b['close'].values[i]; o1 = b['open'].values[i+1]; c1 = b['close'].values[i+1]
    if Tc > 0 and o1 > 0:
        e1s.append(c1/o1-1); gs.append(o1/Tc-1)
n, wr, av = st(e1s)
print('昨日池今日执1 n=%d 胜率 %.1f%% 均收 %.2f%% ; gap中位 %.2f%%' % (n, wr, av, np.median(gs)*100))
print('昨日池今日封板(仍在zt_pool) %d 只' % zb['代码'].isin(zt['代码']).sum())
prev_first = int((zb['连板'] == 1).sum())
print('今日2板 %d / 昨首板 %d = 一进二 %.1f%%' % ((zt['连板'] == 2).sum(), prev_first, (zt['连板'] == 2).sum()/prev_first*100))
print('今日3板+ %d / 昨2板+ %d = 高度晋级 %.1f%%' % ((zt['连板'] >= 3).sum(), (zb['连板'] >= 2).sum(), (zt['连板'] >= 3).sum()/max(1, (zb['连板'] >= 2).sum())*100))

# ---------- 3 格重算：首板×尾盘>14:00×换手10-20%，按开板分层 ----------
D = P[P['E1'].notna()].copy()
print('\n=== 全样本 n=%d 窗口 %s~%s' % (len(D), D['日'].min(), D['日'].max()))
D['时段'] = D['首封'].map(head_bucket)
D['换手桶'] = D['换手'].map(to_bucket)
D['开板组'] = np.where(D['开板'] == 0, '0', np.where(D['开板'] <= 2, '1-2', '>=3'))
G = D[(D['连板'] == 1) & (D['时段'] == '尾盘>14:00') & (D['换手桶'] == '10-20%')]
print('格 n=%d' % len(G))
def row(name, g):
    e1 = g['E1'].dropna(); e2 = g['E2'].dropna(); gp = g['GAP'].dropna()
    gate = ((gp >= -0.03) & (gp <= 0.015)).mean()*100 if len(gp) else None
    print('%-28s n=%-4d 执1 %5.1f%%/%6.2f%%  执2 %5.1f%%/%6.2f%%  闸门 %.1f%%  gap中位 %5.2f%%' % (
        name, len(g), (e1 > 0).mean()*100, e1.mean()*100, (e2 > 0).mean()*100, e2.mean()*100, gate, np.median(gp)*100))
row('格-全体', G)
for k in ['0', '1-2', '>=3']:
    row('  开板'+k, G[G['开板组'] == k])
row('对照 全库', D)
row('对照 首板×尾盘(不分换手)', D[(D['连板'] == 1) & (D['时段'] == '尾盘>14:00')])

print('\n=== 尾盘封族(首封>14:00) 按开板重分桶')
W = D[D['时段'] == '尾盘>14:00']
row('尾盘族-全体', W)
for k in ['0', '1-2', '>=3']:
    row('  开板'+k, W[W['开板组'] == k])
print('--- 尾盘族 × 市值 × 制度 × 连板')
W = W.copy()
W['市值组'] = np.where(W['市值亿'] >= 100, '≥100亿', '<100亿')
W['cm'] = np.where(W['代码'].str[:2].isin(['30', '68']), '20cm', np.where(W['代码'].str[0].isin(['4', '8', '9']), '30cm', '10cm'))
for mv in ['≥100亿', '<100亿']:
    for cm in ['10cm', '20cm', '30cm']:
        for lb in ['首板', '2板']:
            g = W[(W['市值组'] == mv) & (W['cm'] == cm) & ((W['连板'] == 1) if lb == '首板' else (W['连板'] == 2))]
            if len(g) >= 20:
                row('%s·%s·%s' % (mv, cm, lb), g)
print('--- 尾盘族 × 开板 × 市值(仅 n≥20)')
for mv in ['≥100亿', '<100亿']:
    for k in ['0', '1-2', '>=3']:
        g = W[(W['市值组'] == mv) & (W['开板组'] == k)]
        if len(g) >= 20: row('%s·开板%s' % (mv, k), g)
