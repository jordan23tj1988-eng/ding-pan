# -*- coding: utf-8 -*-
"""20261105 limitup 路：生成 judgment / body / 交易计划 / 能力回执 / 运行状态。数字全部由文件计算，不手填。"""
import os, json, datetime
import pandas as pd, numpy as np

BASE = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(BASE, '_学习')
T, P0 = '20261105', '20261104'
CDIR = os.path.join(L, '_bars_cache')

def bars(c, cache={}):
    if c in cache: return cache[c]
    f = os.path.join(CDIR, c+'.csv'); cache[c] = None
    if os.path.isfile(f):
        b = pd.read_csv(f); b['date'] = b['date'].astype(str).str.replace('-', ''); cache[c] = b
    return cache[c]

def perf(c, d=T):
    b = bars(c)
    if b is None: return None
    i = np.where(b['date'].values == d)[0]
    if not len(i) or i[0] < 1: return None
    i = int(i[0]); o, cl, pc = b['open'].values[i], b['close'].values[i], b['close'].values[i-1]
    h = b['high'].values[i]
    return dict(gap=round((o/pc-1)*100, 2), e1=round((cl/o-1)*100, 2), chg=round((cl/pc-1)*100, 2), high=round((h/pc-1)*100, 2), close=round(cl, 2))

def fb(s):
    s = str(s).split('.')[0].zfill(6); return s[:2]+':'+s[2:4]

zt = pd.read_csv(os.path.join(BASE, T, 'zt_pool.csv'), dtype={'代码': str}); zt['代码'] = zt['代码'].str.zfill(6)
zb = pd.read_csv(os.path.join(BASE, T, 'zb_pool.csv'), dtype={'代码': str}); zb['代码'] = zb['代码'].str.zfill(6)
z4 = pd.read_csv(os.path.join(BASE, P0, 'zt_pool.csv'), dtype={'代码': str}); z4['代码'] = z4['代码'].str.zfill(6)
summary = json.load(open(os.path.join(BASE, T, 'summary.json'), encoding='utf-8'))
gui = json.load(open(os.path.join(L, '题材归位_%s.json' % T), encoding='utf-8'))
jian = json.load(open(os.path.join(L, '涨停质量荐票_%s.json' % T), encoding='utf-8'))
lib = json.load(open(os.path.join(L, '_涨停质量库.json'), encoding='utf-8'))
wt = json.load(open(os.path.join(L, '_市场温度表.json'), encoding='utf-8'))
prev = json.load(open(os.path.join(L, '总审_%s.json' % P0), encoding='utf-8'))
grids = pd.read_csv(os.path.join(L, '_tmp_limitup_grids_%s.csv' % T), dtype={'代码': str})
grids['代码'] = grids['代码'].str.zfill(6)
G = {r['代码']: r for r in grids.to_dict('records')}
PF = pd.read_pickle(os.path.join(L, '_tmp_P_20261105.pkl'))

def temp(d):
    v = wt.get(d)
    return (v or {}).get('温度') if isinstance(v, dict) else v

TH, THP = temp(T), temp(P0)
zt['首封'] = zt['首次封板时间'].map(fb); zt['末封'] = zt['最后封板时间'].map(fb)
zt['开板'] = zt['炸板次数'].astype(int); zt['连板'] = zt['连板数'].astype(int)
zt['流通亿'] = zt['流通市值']/1e8; zt['封单比'] = zt['封板资金']/zt['流通市值']*100
zt['成交亿'] = zt['成交额']/1e8
n_zt = len(zt); n_zb = len(zb)
zb_rate = round(n_zb/(n_zt+n_zb)*100, 1)
feng_total = zt['封板资金'].sum()/1e8
feng_per = zt['封板资金'].mean()/1e8
fengbi_med = zt['封单比'].median(); fengbi_avg = zt['封单比'].mean()
big = int((zt['流通亿'] >= 100).sum())
ladder = zt['连板'].value_counts().sort_index().to_dict()
lian2plus = int((zt['连板'] >= 2).sum())
open_grp = {'0': int((zt['开板'] == 0).sum()), '1-2': int(zt['开板'].between(1, 2).sum()), '>=3': int((zt['开板'] >= 3).sum())}
def seg(t):
    return '一字≤9:25' if t <= '09:25' else '秒板≤9:31' if t <= '09:31' else '早盘≤10:00' if t <= '10:00' else '盘中10-14' if t <= '14:00' else '尾盘>14:00'
zt['时段'] = zt['首封'].map(seg)
segc = zt['时段'].value_counts().to_dict()
weipan = segc.get('尾盘>14:00', 0)
def tob(x): return '<3%' if x < 3 else '3-10%' if x < 10 else '10-20%' if x < 20 else '≥20%'
zt['换手桶'] = zt['换手率'].map(tob)
tsc = zt['换手桶'].value_counts().to_dict()
prev_first = int((z4['连板数'].astype(int) == 1).sum())
yijiner = (ladder.get(2, 0))/prev_first*100
gaodu = (n_zt if False else int((zt['连板'] >= 3).sum()))/int((z4['连板数'].astype(int) >= 2).sum())*100

# 昨日池今日执1
e1s = []; gaps = []
for c in z4['代码']:
    p = perf(c)
    if p: e1s.append(p['e1']); gaps.append(p['gap'])
y_win = (np.array(e1s) > 0).mean()*100; y_avg = np.mean(e1s); y_gap = np.median(gaps)
prev_hold = int(z4['代码'].isin(zt['代码']).sum())

# 格期望
pos = int((grids['期望pp'] > 0).sum()); tot = grids['期望pp'].sum(); mean = grids['期望pp'].mean()
gtop = grids.sort_values('期望pp', ascending=False).head(8).to_dict('records')

# 因子
FAC = lib['因子']; ACT = lib['活跃因子']; base = lib['基准']
def fstat(k):
    v = FAC.get(k, {}); return v.get('权重', 0), v.get('区分度', 0), v.get('状态', '')

# 深挖格数字（从 P 重算，与前面脚本同口径）
D = PF[PF['E1'].notna()].copy()
D['时段'] = D['首封'].map(lambda t: seg(t) if isinstance(t, str) else '?')
D['开板组'] = np.where(D['开板'] == 0, '0', np.where(D['开板'] <= 2, '1-2', '>=3'))
D['换手桶'] = D['换手'].map(tob)
def cell(g):
    e1 = g['E1'].dropna(); e2 = g['E2'].dropna(); gp = g['GAP'].dropna()
    return dict(n=len(e1), w=round((e1 > 0).mean()*100, 1), r=round(e1.mean()*100, 2),
                w2=round((e2 > 0).mean()*100, 1), r2=round(e2.mean()*100, 2),
                gate=round(((gp >= -0.03) & (gp <= 0.015)).mean()*100, 1), gm=round(np.median(gp)*100, 2))
GRID = D[(D['连板'] == 1) & (D['时段'] == '尾盘>14:00') & (D['换手桶'] == '10-20%')]
G_all = cell(GRID)
G_open = {k: cell(GRID[GRID['开板组'] == k]) for k in ['0', '1-2', '>=3']}
W = D[D['时段'] == '尾盘>14:00']
W_all = cell(W); W_open = {k: cell(W[W['开板组'] == k]) for k in ['0', '1-2', '>=3']}
# 全库开板单因子
KO = cell(D[D['开板'] == 0]); K1 = cell(D[D['开板'] >= 1])
# 尾盘族三层
W2 = W.copy()
W2['市值组'] = np.where(W2['市值亿'] >= 100, '≥100亿', '<100亿')
W2['cm'] = np.where(W2['代码'].str[:2].isin(['30', '68']), '20cm', np.where(W2['代码'].str[0].isin(['4', '8', '9']), '30cm', '10cm'))
W2['连板组'] = np.where(W2['连板'] == 1, '首板', np.where(W2['连板'] == 2, '2板', '3板+'))
LAYER = []
for mv in ['≥100亿', '<100亿']:
    for cm in ['10cm', '20cm']:
        for lb in ['首板', '2板']:
            g = W2[(W2['市值组'] == mv) & (W2['cm'] == cm) & (W2['连板组'] == lb)]
            if len(g) >= 20: LAYER.append(dict(格='%s·%s·%s' % (mv, cm, lb), **cell(g)))
# 换手率复检
def toc(x):
    if x is None or x != x: return None
    return '<3%' if x < 3 else '3-10%' if x < 10 else '10-20%' if x < 20 else '≥20%'
D['换手桶2'] = D['换手'].map(toc)
TO = {k: cell(D[D['换手桶2'] == k]) for k in ['<3%', '3-10%', '10-20%', '≥20%']}
# 质量分分档
import importlib, sys
sys.path.insert(0, BASE)
M = importlib.import_module('涨停质量训练')
PF2 = PF.copy()
PF2['涨停总数'] = PF2.groupby('日')['代码'].transform('size')
PF2['行业家数'] = PF2.groupby(['日', '行业'])['代码'].transform('size')
days = sorted(PF2['日'].unique()); di = {d: i for i, d in enumerate(days)}
occ = {}
for c, d in zip(PF2['代码'], PF2['日']): occ.setdefault(c, []).append(di[d])
PF2['基因'] = [sum(1 for j in occ[c] if di[d]-10 <= j < di[d]) for c, d in zip(PF2['代码'], PF2['日'])]
PF2['温度'] = [temp(d) for d in PF2['日']]
qs = [M.质量打分(r, lib) or {} for r in PF2.to_dict('records')]
QQ = pd.DataFrame(qs)
for k in ['质量分', '预测抓龙率', '预测执1均涨', '预测执2均涨']: PF2[k] = QQ.get(k)
PF2['主导因子'] = QQ.get('主导因子')
DD = PF2[PF2['E1'].notna()].copy()
DD['分档'] = pd.cut(DD['质量分'], [-1, 3, 6, 8, 10, 99], labels=['0-3', '4-6', '7-8', '9-10', '11+'])
DEC = []
for k, g in DD.groupby('分档', observed=True):
    e1 = g['E1'].dropna(); e2 = g['E2'].dropna()
    DEC.append(dict(档=str(k), n=len(g), w=round((e1 > 0).mean()*100, 1), r=round(e1.mean()*100, 2),
                    w2=round((e2 > 0).mean()*100, 1), r2=round(e2.mean()*100, 2), dr=round((e2 >= 0.08).mean()*100, 1)))
rows = []
for d, g in DD.groupby('日'):
    g = g.sort_values(['质量分', '换手'], ascending=False); tp8 = g.head(8)
    rows.append(dict(e1=tp8['E1'].mean(), e1w=(tp8['E1'] > 0).mean(), e2=tp8['E2'].mean(),
                     dr=(tp8['E2'] >= 0.08).mean(), pool=g['E1'].mean(), pdr=(g['E2'] >= 0.08).mean()))
TT = pd.DataFrame(rows)
TOP8 = dict(days=len(TT), e1=round(TT.e1.mean()*100, 2), e1w=round(TT.e1w.mean()*100, 1), e2=round(TT.e2.mean()*100, 2),
            dr=round(TT.dr.mean()*100, 1), pool=round(TT.pool.mean()*100, 2), pdr=round(TT.pdr.mean()*100, 1),
            beat=int((TT.e1 > TT.pool).sum()), beat_pct=round((TT.e1 > TT.pool).mean()*100, 1),
            beat_dr=int((TT.dr > TT.pdr).sum()), beat_dr_pct=round((TT.dr > TT.pdr).mean()*100, 1))
T20 = TT.tail(20)
TOP8_20 = dict(e1=round(T20.e1.mean()*100, 2), e1w=round(T20.e1w.mean()*100, 1), dr=round(T20.dr.mean()*100, 1),
               pool=round(T20.pool.mean()*100, 2), pdr=round(T20.pdr.mean()*100, 1))
T5 = PF2[PF2['日'] == T].sort_values(['质量分', '换手'], ascending=False).head(8)
TOP8_TODAY = [dict(代码=r['代码'], 名称=r['名称'], 质量分=int(r['质量分']), 抓龙=round(r['预测抓龙率'], 1),
                   换手=round(r['换手'], 1), 连板=int(r['连板']), 首封=r['首封'], 开板=int(r['开板']),
                   市值=round(r['市值亿'], 1), 主导=r['主导因子']) for _, r in T5.iterrows()]
top8_dr_avg = round(np.mean([x['抓龙'] for x in TOP8_TODAY]), 1)

# 荐票源 top5
TOP5 = jian['top5']
# 昨日荐票结算
SETTLE = []
for code, wgt, typ in [('002992', 1.0, '荐票'), ('688809', 1.2, '荐票'), ('002980', 0.0, '观察')]:
    p = perf(code)
    SETTLE.append(dict(代码=code, 名称={'002992': '宝明科技', '688809': '强一股份', '002980': '华盛昌'}[code],
                       类型=typ, 权重=wgt, gap=p['gap'], e1=p['e1'], chg=p['chg']))
nav = sum(s['权重']*s['e1'] for s in SETTLE)/100
HOLD = perf('002652')
# 高度轴
AXIS = []
for c, nm in [('002827', '高争民爆'), ('605577', '龙版传媒'), ('002058', '紫竹高科'), ('600261', '阳光照明'), ('002578', '闽发铝业'), ('601599', '浙文影业')]:
    p = perf(c); tag = '涨停' if c in set(zt['代码']) else ('炸板' if c in set(zb['代码']) else '未在册')
    AXIS.append(dict(代码=c, 名称=nm, 状态=tag, **(p or {})))
# 688809 昨日字段
r688 = z4[z4['代码'] == '688809'].iloc[0]
A688 = dict(首封=fb(r688['首次封板时间']), 末封=fb(r688['最后封板时间']), 炸板=int(r688['炸板次数']),
            封亿=round(float(r688['封板资金'])/1e8, 3), 流通亿=round(float(r688['流通市值'])/1e8, 1),
            封单比=round(float(r688['封板资金'])/float(r688['流通市值'])*100, 2),
            换手=round(float(r688['换手率']), 2), today=perf('688809'))

B = dict(T=T, TH=TH, THP=THP, n_zt=n_zt, n_zb=n_zb, zb_rate=zb_rate, feng_total=round(feng_total, 2),
         feng_per=round(feng_per, 3), fengbi_med=round(fengbi_med, 3), fengbi_avg=round(fengbi_avg, 3),
         big=big, big_pct=round(big/n_zt*100, 1), ladder=ladder, lian2plus=lian2plus, open_grp=open_grp,
         segc=segc, weipan=weipan, tsc=tsc, yijiner=round(yijiner, 1), gaodu=round(gaodu, 1),
         y_win=round(y_win, 1), y_avg=round(y_avg, 2), y_gap=round(y_gap, 2), prev_hold=prev_hold,
         pos=pos, tot=round(tot, 2), mean=round(mean, 3), gtop=gtop, GRID=G_all, G_open=G_open,
         W_all=W_all, W_open=W_open, LAYER=LAYER, TO=TO, DEC=DEC, TOP8=TOP8, TOP8_20=TOP8_20,
         TOP8_TODAY=TOP8_TODAY, top8_dr_avg=top8_dr_avg, SETTLE=SETTLE, nav=round(nav, 3), HOLD=HOLD,
         AXIS=AXIS, A688=A688, KO=KO, K1=K1, base=base, lib=lib, summary=summary,
         med_mv=round(zt['流通亿'].median(), 1), clinch=open_grp['0'])
json.dump(B, open(os.path.join(L, '_tmp_limitup_bundle_%s.json' % T), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: v for k, v in B.items() if not isinstance(v, (list, dict))}, ensure_ascii=False, indent=1, default=str))
print('GRID', G_all, G_open); print('W_all', W_all, W_open); print('LAYER', LAYER)
print('TO', TO); print('DEC', DEC); print('TOP8', TOP8, TOP8_20); print('SETTLE', SETTLE, 'nav', nav)
print('AXIS', AXIS); print('A688', A688); print('gtop', gtop[:3])
print('TOP8_TODAY', TOP8_TODAY[:2], 'avg', top8_dr_avg)
