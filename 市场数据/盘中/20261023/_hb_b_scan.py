# -*- coding: utf-8 -*-
"""hb-b 10:30 场：昨涨停池帧扫描（趋势/中位/2分钟批量跳水簇）。只读 realtime_ticks.jsonl。"""
import json, os, statistics, datetime

D = os.path.dirname(os.path.abspath(__file__))
fr = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
print('frames', len(fr), fr[0]['ts'], '->', fr[-1]['ts'])

def snap(f):
    return {r['code']: r for r in f['rows']}

def stats(f):
    p = [r['pct'] for r in f['rows']]
    return dict(ts=f['ts'], n=len(p), med=round(statistics.median(p), 2),
                mean=round(statistics.mean(p), 2),
                up=sum(1 for x in p if x > 0), dn=sum(1 for x in p if x < 0),
                zt=sum(1 for x in p if x >= 9.8), dt=sum(1 for x in p if x <= -9.8))

for f in fr[::6]:
    print(stats(f))

print('\n--- last 3 frames ---')
for f in fr[-3:]:
    print(stats(f))
    print('  codes', len(f['rows']), 'pool_date', f.get('pool_date'))

# 2-minute clusters: window ending at frame i, compare pct(i) vs pct(nearest frame <= t-120s)
print('\n--- 2min drop clusters (>=3pp) ---')
maxc = []
for i in range(len(fr)):
    t = datetime.datetime.strptime(fr[i]['ts'], '%Y-%m-%d %H:%M:%S')
    # find j = latest frame with time <= t-100s (approx 2 frames back)
    j = None
    for k in range(i - 1, -1, -1):
        tk = datetime.datetime.strptime(fr[k]['ts'], '%Y-%m-%d %H:%M:%S')
        if (t - tk).total_seconds() >= 100:
            j = k
            break
    if j is None:
        continue
    a, b = snap(fr[j]), fr[i]['rows']
    drops = []
    for r in b:
        if r['code'] in a:
            d = r['pct'] - a[r['code']]['pct']
            if d <= -3.0:
                drops.append((r['code'], r['name'], round(a[r['code']]['pct'], 2), round(r['pct'], 2), round(d, 2)))
    maxc.append((len(drops), fr[i]['ts'], drops))

maxc.sort(key=lambda x: -x[0])
for n, ts, drops in maxc[:5]:
    print(n, ts, drops[:6])

print('\n--- last 12 frames clusters ---')
for n, ts, drops in [x for x in maxc if x[1] >= fr[-12]['ts']]:
    print(n, ts, [(d[1], d[4]) for d in drops])

# biggest droppers over last 20 min
base = fr[-21]
bs = snap(base)
last = fr[-1]
rows = []
for r in last['rows']:
    if r['code'] in bs:
        rows.append((round(r['pct'] - bs[r['code']]['pct'], 2), r['name'], bs[r['code']]['pct'], r['pct']))
rows.sort()
print('\n--- biggest 20min droppers from', base['ts'], '---')
for x in rows[:8]:
    print(x)
print('--- biggest 20min gainers ---')
for x in rows[-5:]:
    print(x)
print('\n003021 in pool?', any(r['code'] == '003021' for r in last['rows']))
print('002242 in pool?', any(r['code'] == '002242' for r in last['rows']))
print('603370 in pool?', any(r['code'] == '603370' for r in last['rows']))
