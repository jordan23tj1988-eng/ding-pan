# -*- coding: utf-8 -*-
"""20261105 limitup：质量分重算(Top8) + 今日池格期望 + 688809核对。"""
import os, sys, json
import pandas as pd, numpy as np
BASE = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(BASE, '_学习')
sys.path.insert(0, BASE)
import importlib
M = importlib.import_module('涨停质量训练')
P = pd.read_pickle(os.path.join(L, '_tmp_P_20261105.pkl'))
TODAY = '20261105'

# --- 补 涨停总数/行业家数/基因/温度
P['涨停总数'] = P.groupby('日')['代码'].transform('size')
P['行业家数'] = P.groupby(['日', '行业'])['代码'].transform('size')
days = sorted(P['日'].unique()); di = {d: i for i, d in enumerate(days)}
occ = {}
for c, d in zip(P['代码'], P['日']): occ.setdefault(c, []).append(di[d])
P['基因'] = [sum(1 for j in occ[c] if di[d]-10 <= j < di[d]) for c, d in zip(P['代码'], P['日'])]
wt = json.load(open(os.path.join(L, '_市场温度表.json'), encoding='utf-8'))
P['温度'] = [((wt.get(d) or {}) if isinstance(wt.get(d), dict) else {}).get('温度') for d in P['日']]
lib = json.load(open(os.path.join(L, '_涨停质量库.json'), encoding='utf-8'))
print('库更新', lib['更新'], '样本', lib['样本'], '基准抓龙率', lib['基准'].get('抓龙率'))

# --- 逐行打分
rows = P.to_dict('records')
sc = []
for r in rows:
    q = M.质量打分(r, lib)
    sc.append(q or {})
Q = pd.DataFrame(sc)
for k in ['质量分', '预测执1胜率', '预测执1均涨', '预测执2胜率', '预测执2均涨', '预测抓龙率']:
    P[k] = Q.get(k)
P['主导因子'] = Q.get('主导因子')
D = P[P['E1'].notna()].copy()
print('打分有效', int(P['质量分'].notna().sum()), '有前向', len(D))

# --- 质量分分档 → 执1/执2/抓龙率（历史有效性）
print('\n=== 质量分分档（全样本，执1口径）')
D['分档'] = pd.cut(D['质量分'], [-1, 3, 6, 8, 10, 99], labels=['0-3', '4-6', '7-8', '9-10', '11+'])
for k, g in D.groupby('分档', observed=True):
    e1 = g['E1'].dropna(); e2 = g['E2'].dropna()
    print('  %-5s n=%-5d 执1 %5.1f%%/%6.2f%%  执2 %5.1f%%/%6.2f%%  抓龙(r) %5.1f%%' % (
        k, len(g), (e1 > 0).mean()*100, e1.mean()*100, (e2 > 0).mean()*100, e2.mean()*100, (e2 >= 0.08).mean()*100))

# --- 每日 Top8（质量分降序，同日并列按换手降序截断）→ 次日执1/执2/抓龙
print('\n=== 每日质量分 Top8 组合（历史，n_top8 池；对比当日前 8 之外的全体）')
tp = []
for d, g in D.groupby('日'):
    g = g.sort_values(['质量分', '换手'], ascending=False)
    top = g.head(8); rest = g.iloc[8:]
    tp.append(dict(日=d, n=len(top), e1=top['E1'].mean(), e1w=(top['E1'] > 0).mean(),
                   e2=top['E2'].mean(), e2w=(top['E2'] > 0).mean(),
                   dr=(top['E2'] >= 0.08).mean(), rest_e1=rest['E1'].mean(),
                   rest_n=len(rest), pool_e1=g['E1'].mean(), pool_dr=(g['E2'] >= 0.08).mean()))
T = pd.DataFrame(tp)
print('  日数 %d  顶8平均执1 %.2f%% (胜率 %.1f%%)  执2 %.2f%%  抓龙 %.1f%%  当日全池执1 %.2f%%  池抓龙 %.1f%%' % (
    len(T), T.e1.mean()*100, T.e1w.mean()*100, T.e2.mean()*100, T.dr.mean()*100, T.pool_e1.mean()*100, T.pool_dr.mean()*100))
print('  顶8执1>池均值 的日数 %d/%d (%.1f%%)；顶8抓龙>池抓龙 日数 %d/%d (%.1f%%)' % (
    int((T.e1 > T.pool_e1).sum()), len(T), (T.e1 > T.pool_e1).mean()*100,
    int((T.dr > T.pool_dr).sum()), len(T), (T.dr > T.pool_dr).mean()*100))
for k in [10, 20, 5]:
    R = T.tail(k)
    print('  近%d日: 顶8执1 %+.2f%% (胜率 %.1f%%) 抓龙 %.1f%% | 全池执1 %+.2f%% 池抓龙 %.1f%%' % (
        k, R.e1.mean()*100, R.e1w.mean()*100, R.dr.mean()*100, R.pool_e1.mean()*100, R.pool_dr.mean()*100))

# --- 今日 Top8
T8 = P[P['日'] == TODAY].sort_values(['质量分', '换手'], ascending=False).head(8)
print('\n=== 今日 Top8（质量分口径）')
for r in T8.itertuples():
    print('  %s %-6s 质量分%-3d 抓龙%.1f%% 执1 %+.2f%% 连板%d 首封%s 开板%d 换手%.1f%% 市值%.0f亿 封单比%.2f%% | %s' % (
        r.代码, r.名称, r.质量分, r.预测抓龙率 or 0, r.预测执1均涨 or 0, r.连板, r.首封, r.开板, r.换手 or 0, r.市值亿 or 0, r.封单比 or 0, r.主导因子))
print('  Top8 平均预测抓龙率 %.1f%% vs 库基准 %.1f%%' % (T8['预测抓龙率'].mean(), lib['基准'].get('抓龙率') or 0))

# --- 今日池：格期望（连板桶×首封桶×换手桶，n≥30，退化到二维）
def hb(t):
    if not isinstance(t, str): return '?'
    return '一字' if t <= '09:25' else '秒板' if t <= '09:31' else '早盘' if t <= '10:00' else ('盘中' if t <= '14:00' else '尾盘')
def tb(x):
    if x is None or x != x: return '?'
    return '<3' if x < 3 else '3-10' if x < 10 else '10-20' if x < 20 else '20+'
def lb(x): return '首板' if x <= 1 else ('2板' if x == 2 else ('3板' if x == 3 else '4板+'))
for c, f in [('首封桶', hb), ('换手桶', tb), ('连板桶', lb)]:
    D[c] = D[c.replace('桶', '')].map(f) if c != '首封桶' else D['首封'].map(f)
D['连板桶'] = D['连板'].map(lb); D['换手桶'] = D['换手'].map(tb)
D['市值组'] = np.where(D['市值亿'] >= 100, 'big', 'small')

def cell(g):
    e1 = g['E1'].dropna(); gp = g['GAP'].dropna()
    if len(e1) == 0: return None
    return dict(n=len(e1), r=round(e1.mean()*100, 3), w=round((e1 > 0).mean()*100, 1),
                gate=round(((gp >= -0.03) & (gp <= 0.015)).mean()*100, 1), gn=len(gp))

def lookup(r):
    for keys in [(['连板桶', '首封桶', '换手桶'], 30), (['连板桶', '首封桶'], 60), (['首封桶', '换手桶'], 100), (['首封桶'], 200)]:
        g = D
        for k in keys[0]:
            g = g[g[k] == r[k]]
        if len(g.dropna(subset=['E1'])) >= keys[1]:
            c = cell(g); c['level'] = '+'.join(keys[0]); return c
    c = cell(D); c['level'] = '全库'; return c

Z = pd.read_csv(os.path.join(BASE, TODAY, 'zt_pool.csv'), dtype={'代码': str})
Z['代码'] = Z['代码'].str.zfill(6)
Z['首封'] = Z['首次封板时间'].astype(str).str.zfill(6).map(lambda s: s[:2]+':'+s[2:4])
Z['连板桶'] = Z['连板数'].astype(int).map(lb); Z['首封桶'] = Z['首封'].map(hb); Z['换手桶'] = Z['换手率'].map(tb)
Z['市值组'] = np.where(Z['流通市值']/1e8 >= 100, 'big', 'small')
res = []
for r in Z.to_dict('records'):
    c = lookup(r)
    c.update({'代码': r['代码'], '名称': r['名称'], '连板': int(r['连板数']), '首封': r['首封'],
              '开板': int(r['炸板次数']), '换手': round(r['换手率'], 2), '市值亿': round(r['流通市值']/1e8, 1),
              '封单比': round(r['封板资金']/r['流通市值']*100, 2), '期望pp': round(c['r']*c['gate']/100, 3)})
    res.append(c)
Rz = pd.DataFrame(res).sort_values('期望pp', ascending=False)
print('\n=== 今日池格期望 Top12（格执1均收 × 闸门触发率）')
print(Rz.head(12)[['代码', '名称', '连板', '首封', '开板', '换手', '市值亿', '封单比', 'n', 'r', 'w', 'gate', '期望pp', 'level']].to_string(index=False))
print('正期望 %d / %d，合计 %.2fpp，均值 %.3fpp' % ((Rz['期望pp'] > 0).sum(), len(Rz), Rz['期望pp'].sum(), Rz['期望pp'].mean()))
Rz.to_csv(os.path.join(L, '_tmp_limitup_grids_20261105.csv'), index=False, encoding='utf-8-sig')

# --- 688809 核对
z4 = pd.read_csv(os.path.join(BASE, '20261104', 'zt_pool.csv'), dtype={'代码': str})
z4['代码'] = z4['代码'].str.zfill(6)
print('\n=== 688809 20261104 zt_pool 原名行')
print(z4[z4['代码'] == '688809'].to_string(index=False))
print('\n=== 688809 今日是否在池: %s' % ('688809' in set(Z['代码'])))
