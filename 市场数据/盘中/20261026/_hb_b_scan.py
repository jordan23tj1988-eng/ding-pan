# -*- coding: utf-8 -*-
"""hb-b 10:30 场：池帧扫描（温度/2分钟批量跳水/个股路径）。只读 realtime_ticks.jsonl。"""
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
                zt=sum(1 for x in p if x >= 9.8), deep=sum(1 for x in p if x <= -5),
                dt=sum(1 for x in p if x <= -9.8))

print('\n--- every 6th frame ---')
for f in fr[::6]:
    print(stats(f))
print('\n--- last 4 frames ---')
for f in fr[-4:]:
    print(stats(f))

# 2-min drop clusters
print('\n--- 2min drop clusters (>=3pp) ---')
maxc = []
for i in range(len(fr)):
    t = datetime.datetime.strptime(fr[i]['ts'], '%Y-%m-%d %H:%M:%S')
    j = None
    for k in range(i - 1, -1, -1):
        tk = datetime.datetime.strptime(fr[k]['ts'], '%Y-%m-%d %H:%M:%S')
        if (t - tk).total_seconds() >= 100:
            j = k
            break
    if j is None:
        continue
    a = snap(fr[j])
    drops = []
    for r in fr[i]['rows']:
        if r['code'] in a:
            d = r['pct'] - a[r['code']]['pct']
            if d <= -3.0:
                drops.append((r['code'], r['name'], round(a[r['code']]['pct'], 2), round(r['pct'], 2), round(d, 2)))
    maxc.append((len(drops), fr[i]['ts'], drops))

maxc.sort(key=lambda x: -x[0])
for n, ts, drops in maxc[:6]:
    print(n, ts, drops[:8])
print('\n--- clusters in last 30 min ---')
cut = (datetime.datetime.strptime(fr[-1]['ts'], '%Y-%m-%d %H:%M:%S') - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
for n, ts, drops in maxc:
    if ts >= cut and n > 0:
        print(n, ts, [(d[1], d[4]) for d in drops])

# individual paths over last 30min
print('\n--- last 30min deltas (top losers / top gainers) ---')
base_idx = None
for k in range(len(fr) - 1, -1, -1):
    if fr[k]['ts'] <= cut:
        base_idx = k
        break
if base_idx is not None:
    bs = snap(fr[base_idx])
    rows = []
    for r in fr[-1]['rows']:
        if r['code'] in bs:
            rows.append((round(r['pct'] - bs[r['code']]['pct'], 2), r['name'], bs[r['code']]['pct'], r['pct']))
    rows.sort()
    print('base', fr[base_idx]['ts'])
    for x in rows[:8]:
        print(' LOSER', x)
    for x in rows[-5:]:
        print(' GAINER', x)

# watch codes path
WATCH = ['002242', '003021', '002639', '600487', '603370', '301502']
print('\n--- watch code path (pct by frame, 5-frame stride) ---')
for c in WATCH:
    seq = []
    for f in fr:
        for r in f['rows']:
            if r['code'] == c:
                seq.append((f['ts'][11:16], r['pct'], r.get('px')))
                break
    print(c, 'in_pool' if seq else 'NOT_IN_POOL')
    if seq:
        print('  ', seq[::5], '->', seq[-1])

print('\n--- last frame full breadth ---')
last = fr[-1]
print(stats(last))
print('pool_date', last.get('pool_date'), 'stale', last.get('pool_stale'), 'n', len(last['rows']))
