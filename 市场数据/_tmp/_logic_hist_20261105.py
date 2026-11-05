# -*- coding: utf-8 -*-
"""构建 57+ 日涨停池票级数据集 + 日级状态特征，供 logic 路建桶。零后视镜：只用 <=20261105 数据。"""
import json, os, glob
import pandas as pd, numpy as np

BASE = 'D:/股票数据/市场数据'
CACHE = os.path.join(BASE, '_学习/_bars_cache')
rows = []
day = []
files = sorted(glob.glob(os.path.join(BASE, '_学习/涨停对链条_*.json')))
trade = json.load(open(os.path.join(BASE, '_学习/_市场温度表.json'), encoding='utf-8'))
if isinstance(trade, dict) and 'days' in trade:
    trade = trade['days']

def get_temp(d):
    try:
        v = trade.get(d)
        if isinstance(v, dict):
            return v.get('温度') or v.get('temp')
        return v
    except Exception:
        return None

bars_cache = {}
def bars(c):
    if c in bars_cache:
        return bars_cache[c]
    p = os.path.join(CACHE, c + '.csv')
    if not os.path.exists(p):
        bars_cache[c] = None
        return None
    b = pd.read_csv(p)
    b['date'] = b['date'].astype(str)
    b = b.set_index('date')
    bars_cache[c] = b
    return b

for f in files:
    d = os.path.basename(f).replace('涨停对链条_', '').replace('.json', '')
    if d > '20261105':
        continue
    try:
        J = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    stocks = []
    for L in J.get('题材线', []):
        for h in L.get('环节', []):
            for s in h.get('个股', []):
                s['_line'] = L['大方向']
                s['_env'] = h['环节']
                stocks.append(s)
    n = len(stocks)
    if n == 0:
        continue
    fb = []
    first_board = 0
    late = 0
    for s in stocks:
        link = s.get('连板') or 1
        if link == 1:
            first_board += 1
        ff = str(s.get('首封') or '').replace(':', '').rjust(4, '0')
        try:
            fm = int(ff[:2]) * 60 + int(ff[2:4])
        except Exception:
            fm = None
        if fm is not None and fm >= 780:
            late += 1
        v = s.get('封单比')
        if isinstance(v, (int, float)):
            fb.append(v)
        rows.append(dict(date=d, code=s['代码'], name=s.get('名称'), line=s['_line'], env=s['_env'],
                         fm=fm, fb=v, lian=link, zm=s.get('开板次数')))
    day.append(dict(date=d, n=n, first_board_pct=100.0 * first_board / n,
                    late_pct=100.0 * late / n, fb_med=float(np.median(fb)) if fb else np.nan,
                    max_lian=max([(s.get('连板') or 1) for s in stocks]),
                    temp=get_temp(d)))

df = pd.DataFrame(rows)
dd = pd.DataFrame(day).sort_values('date')

# 计算执1（T+1 开→收）、收/收、执2
res = []
for i, r in df.iterrows():
    b = bars(r['code'])
    if b is None:
        continue
    d0 = r['date'][:4] + '-' + r['date'][4:6] + '-' + r['date'][6:]
    dates = b.index.tolist()
    if d0 not in dates:
        continue
    k = dates.index(d0)
    if k + 1 >= len(dates):
        continue
    t1 = b.iloc[k + 1]
    row = dict(r)
    row['t1_date'] = dates[k + 1]
    row['t1_open'] = t1['open']; row['t1_close'] = t1['close']; row['t1_high'] = t1['high']
    row['c0'] = b.iloc[k]['close']
    row['zhi1'] = (t1['close'] / t1['open'] - 1) * 100
    row['ss'] = (t1['close'] / b.iloc[k]['close'] - 1) * 100
    row['gap'] = (t1['open'] / b.iloc[k]['close'] - 1) * 100
    if k + 2 < len(dates):
        row['zhi2'] = (b.iloc[k + 2]['close'] / t1['open'] - 1) * 100
    else:
        row['zhi2'] = np.nan
    res.append(row)

out = pd.DataFrame(res)
out.to_pickle(os.path.join(BASE, '_tmp/logic_hist_20261105.pkl'))
dd.to_pickle(os.path.join(BASE, '_tmp/logic_days_20261105.pkl'))
print('days', len(dd), 'rows', len(out), 'date range', out.date.min(), out.date.max())
print(dd.tail(8).to_string(index=False))
