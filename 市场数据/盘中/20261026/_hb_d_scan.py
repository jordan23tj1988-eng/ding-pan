# -*- coding: utf-8 -*-
"""hb-d 13:30 场扫描：新鲜度/池帧温度/掉板/2分钟题材批量跳水/持仓路径/东财池结构。只读。"""
import json, os, statistics, datetime

D = os.path.dirname(os.path.abspath(__file__))
fr = []
for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8'):
    l = l.strip()
    if l:
        try:
            fr.append(json.loads(l))
        except Exception:
            pass
fr = [x for x in fr if x.get('ts')]
fr.sort(key=lambda x: x['ts'])
ts = [datetime.datetime.strptime(x['ts'], '%Y-%m-%d %H:%M:%S') for x in fr]
gaps = [(ts[i] - ts[i-1]).total_seconds() for i in range(1, len(ts))]
now = datetime.datetime.now()
print('帧数', len(fr), '窗口', fr[0]['ts'], '~', fr[-1]['ts'])
print('末帧龄_秒', round((now - ts[-1]).total_seconds(), 1), '最大间隔_秒', max(gaps) if gaps else None)
print('末帧 pool_date', fr[-1].get('pool_date'), 'pool_stale', fr[-1].get('pool_stale'), 'n', fr[-1].get('n'))
print('间隔>180s 的位置', [(fr[i]['ts'], int(gaps[i-1])) for i in range(1, len(ts)) if gaps[i-1] > 180])


def stats(f):
    p = [r['pct'] for r in f['rows'] if isinstance(r.get('pct'), (int, float))]
    return dict(ts=f['ts'][11:], n=len(p), med=round(statistics.median(p), 2),
                mean=round(statistics.mean(p), 2),
                up=sum(1 for x in p if x > 0), dn=sum(1 for x in p if x < 0),
                zt=sum(1 for x in p if x >= 9.8), deep=sum(1 for x in p if x <= -5),
                dt=sum(1 for x in p if x <= -9.8))


print('\n--- 关键时点温度 ---')
marks = ['2026-10-26 09:31:00', '2026-10-26 10:07:00', '2026-10-26 10:36:00',
         '2026-10-26 11:00:00', '2026-10-26 11:30:00', '2026-10-26 13:00:00',
         '2026-10-26 13:10:00', '2026-10-26 13:20:00']
for m in marks:
    cand = [x for x in fr if x['ts'] <= m]
    if cand:
        print(m, stats(cand[-1]))
print('末帧', stats(fr[-1]))

print('\n--- 跌停/深跌名单(末帧) ---')
print([f"{r['name']} {r['pct']}%" for r in fr[-1]['rows'] if isinstance(r.get('pct'), (int, float)) and r['pct'] <= -9.8])
print('≤-5%', [f"{r['name']} {r['pct']}%" for r in fr[-1]['rows'] if isinstance(r.get('pct'), (int, float)) and r['pct'] <= -5])


def snap(f):
    return {r['code']: r for r in f['rows']}


print('\n--- 2分钟 跳水簇(≤-3pp) 最近30分钟 ---')
cl = []
for i in range(len(fr)):
    t = ts[i]
    j = None
    for k in range(i - 1, -1, -1):
        if (t - ts[k]).total_seconds() >= 100:
            j = k
            break
    if j is None:
        continue
    a = snap(fr[j])
    drops = [(r['name'], round(a[r['code']]['pct'], 2), round(r['pct'], 2), round(r['pct'] - a[r['code']]['pct'], 2))
             for r in fr[i]['rows'] if r['code'] in a and r['pct'] - a[r['code']]['pct'] <= -3.0]
    cl.append((len(drops), fr[i]['ts'], drops))
cut = (ts[-1] - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
last30 = [c for c in cl if c[1] >= cut]
last30.sort(key=lambda x: -x[0])
print('最近30分钟 最大簇', last30[0] if last30 else None)
cl.sort(key=lambda x: -x[0])
print('全窗 最大簇 top3', [(n, t, d[:6]) for n, t, d in cl[:3]])

print('\n--- 掉板(日内曾≥9.8 → 末帧) ---')
ever = {}
for f in fr:
    for r in f['rows']:
        if isinstance(r.get('pct'), (int, float)) and r['pct'] >= 9.8:
            ever[r['code']] = r['name']
lastmap = snap(fr[-1])
still = [c for c in ever if isinstance(lastmap.get(c, {}).get('pct'), (int, float)) and lastmap[c]['pct'] >= 9.8]
gone = [(ever[c], lastmap.get(c, {}).get('pct')) for c in ever if c not in still]
print('日内曾涨停', len(ever), '末帧仍涨停', len(still), '掉板率', round((len(ever) - len(still)) / len(ever), 4))
print('掉板名单', gone)
op = [c for c, r in snap(fr[0]).items() if isinstance(r.get('pct'), (int, float)) and r['pct'] >= 9.8]
op_still = sum(1 for c in op if isinstance(lastmap.get(c, {}).get('pct'), (int, float)) and lastmap[c]['pct'] >= 9.8)
print('开盘(09:31)涨停', len(op), '现仍涨停', op_still, '掉板率', round((len(op) - op_still) / max(len(op), 1), 4))

print('\n--- 持仓/另账 轨迹 ---')
WATCH = ['002242', '003021', '002639', '600487', '603370']
for c in WATCH:
    seq = [(f['ts'][11:16], next((r['pct'] for r in f['rows'] if r['code'] == c), None)) for f in fr]
    seq = [s for s in seq if s[1] is not None]
    if not seq:
        print(c, 'NOT_IN_POOL')
        continue
    print(c, 'in_pool', 'first', seq[0], 'last', seq[-1], 'min', min(seq, key=lambda x: x[1]), 'max', max(seq, key=lambda x: x[1]))
    print('   ', seq[::10])

print('\n--- 东财池结构 ---')
pools = json.load(open(os.path.join(D, '_hb_d_pools_1330.json'), encoding='utf-8'))
for k in ('zt', 'zb', 'dt'):
    v = pools[k]
    print(k, len(v) if isinstance(v, list) else v)
zt, zb, dt = pools['zt'], pools['zb'], pools['dt']
if all(isinstance(x, list) for x in (zt, zb, dt)):
    print('炸板率 =', len(zb), '/', len(zt) + len(zb), '=', round(len(zb) / max(len(zt) + len(zb), 1), 4))
    from collections import Counter
    hy = Counter(r.get('hybk') for r in zt)
    print('行业分布 top8', hy.most_common(8))
    print('连板分布', Counter(r.get('lbc') for r in zt).most_common())
    print('最高板', max((r.get('lbc') or 0) for r in zt))
    print('涨停名单', [(r.get('c'), r.get('n'), r.get('hybk'), r.get('lbc')) for r in zt][:60])
    print('炸板名单', [(r.get('c'), r.get('n'), r.get('hybk'), r.get('zc'), r.get('p')) for r in zb][:30])
    hold = {'002242', '003021', '002639', '600487', '603370'}
    print('持仓是否在涨停池', [r.get('n') for r in zt if r.get('c') in hold])
    print('持仓是否在炸板池', [r.get('n') for r in zb if r.get('c') in hold])
    print('持仓是否在跌停池', [r.get('n') for r in dt if r.get('c') in hold])
