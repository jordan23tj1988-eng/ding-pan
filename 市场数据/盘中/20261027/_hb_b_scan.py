# -*- coding: utf-8 -*-
"""hb-b 10:30 场：池帧扫描（2分钟批量跳水/掉板/宽度演化）。只读 realtime_ticks.jsonl。"""
import json, os, statistics, datetime

D = os.path.dirname(os.path.abspath(__file__))
fr = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
print('frames', len(fr), fr[0]['ts'], '->', fr[-1]['ts'])
now = datetime.datetime.strptime(fr[-1]['ts'], '%Y-%m-%d %H:%M:%S')
print('last_age_sec_at_10:30:22<=', 0)

def snap(f):
    return {r['code']: r for r in f['rows']}

def stats(f):
    p = [r['pct'] for r in f['rows']]
    return dict(ts=f['ts'][11:], n=len(p), med=round(statistics.median(p), 2),
                mean=round(statistics.mean(p), 2),
                up=sum(1 for x in p if x > 0), dn=sum(1 for x in p if x < 0),
                zt=sum(1 for x in p if x >= 9.8), deep=sum(1 for x in p if x <= -5),
                dt=sum(1 for x in p if x <= -9.8))

print('\n--- breadth every 10th frame ---')
for f in fr[::10]:
    print(stats(f))
print('\n--- last 5 frames ---')
for f in fr[-5:]:
    print(stats(f))

# gaps
gaps = []
for i in range(1, len(fr)):
    a = datetime.datetime.strptime(fr[i-1]['ts'], '%Y-%m-%d %H:%M:%S')
    b = datetime.datetime.strptime(fr[i]['ts'], '%Y-%m-%d %H:%M:%S')
    gaps.append((b-a).total_seconds())
print('\ngap max/med', max(gaps), statistics.median(gaps))

# 2-min drop clusters
clusters = []
for i in range(len(fr)):
    t = datetime.datetime.strptime(fr[i]['ts'], '%Y-%m-%d %H:%M:%S')
    j = None
    for k in range(i-1, -1, -1):
        tk = datetime.datetime.strptime(fr[k]['ts'], '%Y-%m-%d %H:%M:%S')
        if (t-tk).total_seconds() >= 100:
            j = k
            break
    if j is None:
        continue
    a = snap(fr[j])
    drops = []
    for r in fr[i]['rows']:
        if r['code'] in a:
            dd = r['pct'] - a[r['code']]['pct']
            if dd <= -3.0:
                drops.append((r['code'], r['name'], round(a[r['code']]['pct'], 2), round(r['pct'], 2), round(dd, 2)))
    clusters.append((len(drops), fr[i]['ts'], drops))

clusters.sort(key=lambda x: -x[0])
print('\n--- top 6 clusters (>=3pp in ~2min) ---')
for n, ts, drops in clusters[:6]:
    print(n, ts, drops[:10])
print('\n--- clusters in last 30 min ---')
cut = (now - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
for n, ts, drops in clusters:
    if ts >= cut and n > 0:
        print(n, ts, [(d[1], d[4]) for d in drops])

# 掉板: frames where pct>=9.8 earlier and now below
first = snap(fr[0])
zt_early = [c for c, r in first.items() if r['pct'] >= 9.8]
last = snap(fr[-1])
lost = [(c, first[c]['name'], round(first[c]['pct'], 2), round(last[c]['pct'], 2)) for c in zt_early
        if c in last and last[c]['pct'] < 9.8]
print('\n--- 掉板: 首帧>=9.8 count', len(zt_early), 'now_still_zt', len([c for c in zt_early if c in last and last[c]['pct'] >= 9.8]))
for x in lost:
    print(' LOST', x)

# last 30min deltas
print('\n--- last 30min deltas ---')
base_idx = None
for k in range(len(fr)-1, -1, -1):
    if fr[k]['ts'] <= cut:
        base_idx = k
        break
if base_idx is not None:
    bs = snap(fr[base_idx])
    rows = []
    for r in fr[-1]['rows']:
        if r['code'] in bs:
            rows.append((round(r['pct'] - bs[r['code']]['pct'], 2), r['name'], bs[r['code']]['pct'], r['pct'], r['code']))
    rows.sort()
    print('base', fr[base_idx]['ts'])
    for x in rows[:8]:
        print(' LOSER', x)
    for x in rows[-6:]:
        print(' GAINER', x)

# holdings path
WATCH = ['002242', '003021', '300296', '002979', '300561']
print('\n--- holdings path (pct by frame, stride 5) ---')
for c in WATCH:
    seq = []
    for f in fr:
        for r in f['rows']:
            if r['code'] == c:
                seq.append((f['ts'][11:16], r['pct'], r.get('px')))
                break
    print(c, 'in_pool' if seq else 'NOT_IN_POOL')
    if seq:
        print('   first', seq[0], 'max', max(seq, key=lambda x: x[1]), 'min', min(seq, key=lambda x: x[1]), 'last', seq[-1])

print('\n--- last frame full ---')
print(stats(fr[-1]), 'pool_date', fr[-1].get('pool_date'), 'stale', fr[-1].get('pool_stale'), 'n', len(fr[-1]['rows']))
