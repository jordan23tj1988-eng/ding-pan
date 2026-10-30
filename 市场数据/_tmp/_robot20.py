# -*- coding: utf-8 -*-
"""MA-20261028-05① 机器人线首板桶 按温度分层重算 (近20日题材归位口径, 复现昨日n=84)"""
import sys, io, json, os, glob, csv
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
L = B + '_学习/'
T = json.load(open(L + '_市场温度表.json', encoding='utf-8-sig'))
dates = sorted(os.path.basename(p)[-13:-5] for p in glob.glob(L + '题材归位_2026*.json'))
dates = [d for d in dates if d.isdigit()]
print('题材归位覆盖', dates[0], '~', dates[-1], len(dates), '日')

_bc = {}
def bars(c):
    if c in _bc: return _bc[c]
    f = L + '_bars_cache/' + c + '.csv'
    if not os.path.isfile(f): _bc[c] = None; return None
    b = pd.read_csv(f); b['date'] = b['date'].astype(str).str.replace('-', '')
    b = b.sort_values('date').reset_index(drop=True); _bc[c] = b; return b

def exe1(c, d):
    b = bars(c)
    if b is None: return None
    idx = b.index[b['date'] == d]
    if not len(idx): return None
    i = idx[0]
    if i + 1 >= len(b): return None
    o1, c1 = b.loc[i+1, 'open'], b.loc[i+1, 'close']
    if not o1 or o1 != o1: return None
    return round((c1/o1-1)*100, 2)

def lb_of(d, c):
    f = B + d + '/zt_pool.csv'
    if not os.path.isfile(f): return None
    for r in csv.DictReader(open(f, encoding='utf-8-sig')):
        if r['代码'] == c: return int(float(r['连板数']))
    return None

def collect(days):
    rec = []
    for d in days:
        f = L + f'题材归位_{d}.json'
        j = json.load(open(f, encoding='utf-8-sig'))
        temp = (T.get(d) or {}).get('温度')
        ln = {}
        for c, m in (j.get('映射') or {}).items():
            if '机器人' not in (m.get('大方向') or ''): continue
            lb = lb_of(d, c)
            rec.append(dict(d=d, temp=temp, code=c, name=m.get('名称'), lb=lb,
                            hj=m.get('环节'), cat=m.get('催化'), ret=exe1(c, d)))
    return pd.DataFrame(rec)

def layer(t):
    if t is None or t != t: return '未知'
    t = float(t)
    return '冰点<25' if t < 25 else ('冷25~40' if t < 40 else ('中40~65' if t < 65 else '热>=65'))

def stat(sub, label):
    s = sub.dropna(subset=['ret']); n = len(s)
    if not n: print(f'{label:<34} n=0'); return None
    w = int((s.ret > 0).sum())
    print(f'{label:<34} n={n:<3} 胜率={w}/{n}={round(w/n*100,1)}%  均收={round(s.ret.mean(),2):>6}  中位={round(s.ret.median(),2):>5}')
    return n, w, round(s.ret.mean(), 2)

win20_1028 = [d for d in dates if d <= '20261028'][-20:]
print('\n窗口(近20日, 截至20261028):', win20_1028[0], '~', win20_1028[-1])
df = collect(win20_1028)
df['ly'] = df.temp.map(layer)
r1 = df[df.lb == 1]
print('=== 复现昨日断言 ===')
stat(r1, '机器人线首板 合计(近20日)')
print('--- 按温度分层 ---')
for ly in ['冰点<25', '冷25~40', '中40~65', '热>=65']:
    stat(r1[r1.ly == ly], f'首板 {ly}')
best = r1.dropna(subset=['ret']).groupby('d').ret.agg(['mean', 'count']).sort_values('mean', ascending=False).head(3)
print('\n单日均收Top3:'); print(best)
print('--- 剔除最强日20261022后 ---')
for ly in ['冰点<25', '冷25~40', '中40~65', '热>=65']:
    stat(r1[(r1.ly == ly) & (r1.d != '20261022')], f'首板 剔1022 {ly}')
stat(r1[r1.d != '20261022'], '首板 剔1022 合计')

print('\n=== 贡献拆解(冰点层, 逐日) ===')
ice = r1[r1.ly == '冰点<25'].dropna(subset=['ret'])
for d, g in ice.groupby('d'):
    print(f'  {d} 温度{g.temp.iloc[0]:>5} n={len(g):<2} 均收{round(g.ret.mean(),2):>6} 合计贡献{round(g.ret.sum(),1)}')
print('  冰点层总合计', round(ice.ret.sum(), 1), 'n', len(ice), '均收', round(ice.ret.mean(), 2))
top3 = ice.groupby('d').ret.mean().nlargest(3).index.tolist()
rest = ice[~ice.d.isin(top3)]
print('  剔3个最强日起贡献日', top3, '→ 余', len(rest), '票 均收', round(rest.ret.mean(), 2), '贡献合计', round(rest.ret.sum(), 1))
df.to_csv(B + '_tmp/_robot20.csv', index=False, encoding='utf-8-sig')

# 商业航天同窗口
def collect_kw(days, kw):
    rec = []
    for d in days:
        f = L + f'题材归位_{d}.json'
        j = json.load(open(f, encoding='utf-8-sig'))
        temp = (T.get(d) or {}).get('温度')
        for c, m in (j.get('映射') or {}).items():
            if kw not in (m.get('大方向') or ''): continue
            rec.append(dict(d=d, temp=temp, code=c, name=m.get('名称'), lb=lb_of(d, c),
                            hj=m.get('环节'), ret=exe1(c, d)))
    return pd.DataFrame(rec)
print('\n=== 商业航天线 近20日首板 ===')
ds = collect_kw(win20_1028, '商业航天')
if len(ds):
    ds['ly'] = ds.temp.map(layer); s1 = ds[ds.lb == 1]
    stat(s1, '商业航天首板 近20日')
    for ly in ['冰点<25', '冷25~40', '中40~65', '热>=65']:
        stat(s1[s1.ly == ly], f'首板 {ly}')
    print('  逐日:'); 
    for d, g in s1.groupby('d'): print(f'   {d} 温度{g.temp.iloc[0]} n={len(g)} 均收{g.dropna(subset=["ret"]).ret.mean()}')
