# -*- coding: utf-8 -*-
"""状态型桶：温度跳升修复日 / 首板占比极高日 / 半导体×PCB 双线并行日 的次日表现"""
import json, io, sys, os, csv, statistics as st
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.chdir(r'D:\股票数据\市场数据')
wt = json.load(open('_学习/_市场温度表.json', encoding='utf-8'))
dates = sorted(wt.keys())

def load_bars(code):
    p = '_学习/_bars_cache/%s.csv' % code
    if not os.path.exists(p):
        return None
    o = {}
    for r in csv.DictReader(open(p, encoding='utf-8-sig')):
        try:
            v = (float(r['open']), float(r['close']))
            o[r['date'].replace('-', '')] = v
        except Exception:
            pass
    return o

samples = []
for i, d in enumerate(dates[:-1]):
    fp = '_学习/涨停对链条_%s.json' % d
    if not os.path.exists(fp):
        continue
    obj = json.load(open(fp, encoding='utf-8'))
    nd = dates[i + 1]
    nd2 = dates[i + 2] if i + 2 < len(dates) else None
    prev = wt[dates[i - 1]].get('温度') if i > 0 else None
    temp = wt[d].get('温度')
    lbdist = wt[d].get('梯队') or {}
    tot = sum(lbdist.values()) or 1
    first_ratio = lbdist.get('1', lbdist.get(1, 0)) / tot
    for line in obj.get('题材线', []):
        for env in line.get('环节', []):
            for s in env.get('个股', []):
                b = load_bars(s['代码'])
                if not b:
                    continue
                o1 = b.get(nd)
                if not o1:
                    continue
                r2 = None
                if nd2 and b.get(nd2):
                    r2 = (b[nd2][1] / o1[0] - 1) * 100
                samples.append(dict(d=d, nd=nd, lb=int(s.get('连板') or 1), line=line['大方向'],
                                    cat=s.get('催化') or '', r1=(o1[1] / o1[0] - 1) * 100, r2=r2,
                                    temp=temp, prev=prev, first_ratio=first_ratio,
                                    chg=(temp - prev) if (temp is not None and prev is not None) else None))

def stat(rows, label):
    r1 = [x['r1'] for x in rows if x['r1'] is not None]
    if not r1:
        return '%s  n=0' % label
    win = sum(1 for v in r1 if v > 0) / len(r1) * 100
    r2 = [x['r2'] for x in rows if x['r2'] is not None]
    return '%s  n=%d 胜率%.1f%% 执1%+.2f%% 中位%+.2f%% | 执2 n=%d %+.2f%% 胜%.1f%% | 日数=%d' % (
        label, len(r1), win, sum(r1) / len(r1), st.median(r1), len(r2),
        (sum(r2) / len(r2) if r2 else 0), (sum(1 for v in r2 if v > 0) / len(r2) * 100 if r2 else 0),
        len(set(x['d'] for x in rows)))

# 状态日
mids = [x for x in samples if x['temp'] is not None and 40 <= x['temp'] < 60]
print('== 温度 40-60 区间 ==', stat(mids, '温度40-60·全体'))
print(stat([x for x in mids if x['lb'] == 1], '温度40-60·首板'))
# 跳升修复日：今日这类样本所在日
jump_days = sorted({x['d'] for x in samples if x['chg'] is not None and x['chg'] >= 15})
print('\n跳升>=15 的日:', [(d, wt[d]['温度'], wt[d].get('温度档')) for d in jump_days])
jump = [x for x in samples if x['d'] in jump_days]
print(stat(jump, '跳升>=15 当日全部涨停·次日'))
print(stat([x for x in jump if x['lb'] == 1], '跳升>=15·首板'))
def has(x, k):
    return any(t in x['cat'] for t in k)
print(stat([x for x in jump if has(x, ['半导体', '芯片', '存储', '封装', '光刻', '靶材', '晶圆', 'HBM'])],
           '跳升>=15·半导体催化'))
print(stat([x for x in jump if has(x, ['覆铜板', 'PCB', '印制电路', '电子布', '铜箔', '载板', '树脂'])],
           '跳升>=15·PCB/CCL催化'))

# 首板占比 >=85% 的日子
hi_days = sorted({x['d'] for x in samples if x['first_ratio'] >= 0.85})
print('\n首板占比>=85% 的日:', [(d, wt[d]['温度'], round(wt[d]['梯队'].get('1', 0) / max(1, sum(wt[d]['梯队'].values())), 3)) for d in hi_days])
hi = [x for x in samples if x['d'] in hi_days]
print(stat(hi, '首板占比>=85% 当日全部涨停·次日'))
print(stat([x for x in hi if x['lb'] == 1], '首板占比>=85%·首板'))
print(stat([x for x in hi if has(x, ['半导体', '芯片', '存储', '封装', '光刻', '靶材', '晶圆', 'HBM'])],
           '首板占比>=85%·半导体催化'))

# 今日形态：温度40-60 且 首板占比>=0.85
both_days = sorted({x['d'] for x in samples if x['d'] in hi_days and x['temp'] is not None and 40 <= x['temp'] < 60})
print('\n两条件同时满足日:', [(d, wt[d]['温度']) for d in both_days])
both = [x for x in samples if x['d'] in both_days]
print(stat(both, '温度40-60×首板>=85%·全体'))
print(stat([x for x in both if has(x, ['半导体', '芯片', '存储', '封装', '光刻', '靶材', '晶圆', 'HBM'])], '  ·半导体催化'))
print(stat([x for x in both if has(x, ['覆铜板', 'PCB', '印制电路', '电子布', '铜箔', '载板', '树脂'])], '  ·PCB/CCL催化'))
