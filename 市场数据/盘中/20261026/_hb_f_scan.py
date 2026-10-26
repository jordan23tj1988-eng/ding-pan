# -*- coding: utf-8 -*-
"""hb-f 14:45 尾盘深场扫描：新鲜度/池温/掉板/2分钟批量跳水/持仓路径/东财池结构。只读。"""
import json, os, statistics, datetime
from collections import Counter

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
print('间隔>180s', [(fr[i]['ts'], int(gaps[i-1])) for i in range(1, len(ts)) if gaps[i-1] > 180])


def stats(f):
    p = [r['pct'] for r in f['rows'] if isinstance(r.get('pct'), (int, float))]
    return dict(ts=f['ts'][11:], n=len(p), med=round(statistics.median(p), 2),
                mean=round(statistics.mean(p), 2),
                up=sum(1 for x in p if x > 0), dn=sum(1 for x in p if x < 0),
                zt=sum(1 for x in p if x >= 9.8), deep=sum(1 for x in p if x <= -5),
                dt=sum(1 for x in p if x <= -9.8))


print('\n--- 关键时点温度 ---')
marks = ['2026-10-26 13:30:00', '2026-10-26 14:00:00', '2026-10-26 14:30:00', '2026-10-26 14:40:00']
for m in marks:
    cand = [x for x in fr if x['ts'] <= m]
    if cand:
        print(m, stats(cand[-1]))
print('末帧', stats(fr[-1]))


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
last30 = sorted([c for c in cl if c[1] >= cut], key=lambda x: -x[0])
print('最近30分钟 最大簇', last30[0] if last30 else None)
cl.sort(key=lambda x: -x[0])
print('全窗 最大簇 top3', [(n, t, d[:6]) for n, t, d in cl[:3]])

print('\n--- 掉板 ---')
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
WATCH = ['002242', '003021', '002639', '600487', '603370', '301502']
for c in WATCH:
    seq = [(f['ts'][11:16], next((r['pct'] for r in f['rows'] if r['code'] == c), None)) for f in fr]
    seq = [s for s in seq if s[1] is not None]
    if not seq:
        print(c, 'NOT_IN_POOL')
        continue
    print(c, 'first', seq[0], 'last', seq[-1], 'min', min(seq, key=lambda x: x[1]), 'max', max(seq, key=lambda x: x[1]))
    print('   ', seq[::12])

print('\n--- 东财池结构 ---')
pools = json.load(open(os.path.join(D, '_hb_f_pools_1445.json'), encoding='utf-8'))
zt, zb, dt = pools['zt'], pools['zb'], pools['dt']
print('ZT', len(zt) if isinstance(zt, list) else zt, 'ZB', len(zb) if isinstance(zb, list) else zb, 'DT', len(dt) if isinstance(dt, list) else dt)
if all(isinstance(x, list) for x in (zt, zb, dt)):
    print('炸板率 =', len(zb), '/', len(zt) + len(zb), '=', round(len(zb) / max(len(zt) + len(zb), 1), 4))
    hy = Counter(r.get('hybk') for r in zt)
    print('行业分布 top8', hy.most_common(8))
    print('连板分布', Counter(r.get('lbc') for r in zt).most_common())
    print('最高板', max((r.get('lbc') or 0) for r in zt))
    print('涨停名单', [(r.get('c'), r.get('n'), r.get('hybk'), r.get('lbc')) for r in zt])
    print('炸板名单', [(r.get('c'), r.get('n'), r.get('hybk'), r.get('zc'), r.get('p')) for r in zb])
    hold = {'002242', '003021', '002639', '600487', '603370'}
    print('持仓在涨停池', [r.get('n') for r in zt if r.get('c') in hold])
    print('持仓在炸板池', [r.get('n') for r in zb if r.get('c') in hold])
    print('持仓在跌停池', [r.get('n') for r in dt if r.get('c') in hold])
    print('301502', [ (r.get('n'), r.get('zc'), r.get('p'), r.get('hybk'), r.get('lbc')) for r in zb if r.get('c')=='301502'])
    print('电机Ⅱ 涨停', [r.get('n') for r in zt if r.get('hybk') == '电机Ⅱ'])
