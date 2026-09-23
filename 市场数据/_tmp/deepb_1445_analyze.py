# -*- coding: utf-8 -*-
"""深场B 14:45 尾盘场 tick 分析 (零后视镜: 仅用 ts<=14:45:00 留档)"""
import json, datetime, statistics, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DEC = '2026-09-21 14:45:00'
p = r'D:\股票数据\市场数据\盘中\20260921\realtime_ticks.jsonl'
snaps = []
for line in open(p, encoding='utf-8'):
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get('ts', '') <= DEC:
        snaps.append(d)

print('=== 留档快照条数(<=%s) = %d ===' % (DEC, len(snaps)))
first, last = snaps[0], snaps[-1]
print('首条 ts=%s 末条 ts=%s src=%s pool_date=%s pool_stale=%s kind=%s n=%s' % (
    first['ts'], last['ts'], last.get('src'), last.get('pool_date'), last.get('pool_stale'), last.get('pool_kind'), last.get('n')))

def snap(ts):
    for d in snaps:
        if d['ts'] == ts:
            return d
    # nearest <= ts
    best = None
    for d in snaps:
        if d['ts'] <= ts:
            best = d
    return best

def stat(d):
    rows = d['rows']
    pcts = [r['pct'] for r in rows if r.get('pct') is not None]
    up = sum(1 for x in pcts if x > 0)
    dn = sum(1 for x in pcts if x < 0)
    flat = len(pcts) - up - dn
    zt = [r for r in rows if r.get('pct') is not None and r['pct'] >= 9.8]
    dt = [r for r in rows if r.get('pct') is not None and r['pct'] <= -9.8]
    return dict(ts=d['ts'], n=len(rows), up=up, dn=dn, flat=flat,
                mean=round(statistics.mean(pcts), 3), med=round(statistics.median(pcts), 3),
                zt=len(zt), dt=len(dt),
                zt_names=[(r['code'], r['name'], r['pct']) for r in zt],
                top=[(r['code'], r['name'], r['pct']) for r in sorted(rows, key=lambda x: -x['pct'])[:5]],
                bot=[(r['code'], r['name'], r['pct']) for r in sorted(rows, key=lambda x: x['pct'])[:5]])

print('\n=== 盘中轨迹(均值/中位/涨跌家数) ===')
for ts in ['2026-09-21 11:46:29', '2026-09-21 12:59:xx', '2026-09-21 13:00:xx', '2026-09-21 13:30:xx',
           '2026-09-21 14:00:xx', '2026-09-21 14:15:xx', '2026-09-21 14:30:xx', '2026-09-21 14:40:xx',
           '2026-09-21 14:45:00']:
    if 'xx' in ts:
        pref = ts[:14]
        cand = [d for d in snaps if d['ts'].startswith(pref)]
        if not cand:
            continue
        d = cand[0]
    else:
        d = snap(ts)
    if not d:
        continue
    s = stat(d)
    print('%s n=%d 涨%d/跌%d/平%d 均%+.3f%% 中%+.3f%% 涨停%d 跌停%d' % (
        s['ts'], s['n'], s['up'], s['dn'], s['flat'], s['mean'], s['med'], s['zt'], s['dt']))

print('\n=== 断档检查(相邻 tick 间隔>90s) ===')
prev = None
gaps = []
for d in snaps:
    t = datetime.datetime.strptime(d['ts'], '%Y-%m-%d %H:%M:%S')
    if prev:
        dt = (t - prev[0]).total_seconds()
        if dt > 90:
            gaps.append((prev[1], d['ts'], dt))
    prev = (t, d['ts'])
if gaps:
    for g in gaps:
        print('  断档 %s -> %s = %.0fs' % g)
else:
    print('  无 >90s 断档')
t_last = datetime.datetime.strptime(last['ts'], '%Y-%m-%d %H:%M:%S')
t_dec = datetime.datetime.strptime(DEC, '%Y-%m-%d %H:%M:%S')
print('  决断时点断更 = %.1fs = %.2f min' % ((t_dec - t_last).total_seconds(), (t_dec - t_last).total_seconds() / 60))

print('\n=== 尾盘30分钟(14:15->14:45) 变化 ===')
d15 = snap('2026-09-21 14:15:00')
if d15:
    s15, s45 = stat(d15), stat(last)
    print('14:15 均%+.3f%% -> 14:45 均%+.3f%% (Δ%+.3fpp); 涨家 %d->%d' % (
        s15['mean'], s45['mean'], s45['mean'] - s15['mean'], s15['up'], s45['up']))
    m15 = {r['code']: r['pct'] for r in d15['rows']}
    m45 = {r['code']: r['pct'] for r in last['rows']}
    both = [c for c in m45 if c in m15]
    drops = sorted(both, key=lambda c: m45[c] - m15[c])[:6]
    print('  尾盘30min跌幅前6: ' + ', '.join('%s(%s) %+.2f->%+.2f' % (c, next(r['name'] for r in last['rows'] if r['code'] == c), m15[c], m45[c]) for c in drops))
    rises = sorted(both, key=lambda c: -(m45[c] - m15[c]))[:6]
    print('  尾盘30min涨幅前6: ' + ', '.join('%s(%s) %+.2f->%+.2f' % (c, next(r['name'] for r in last['rows'] if r['code'] == c), m15[c], m45[c]) for c in rises))

print('\n=== 末tick明细(涨跌前5 & 涨停) ===')
s = stat(last)
print('涨停:', s['zt_names'])
print('涨前5:', s['top'])
print('跌前5:', s['bot'])

print('\n=== 防守触发扫描(B级, 判定对象=池内40只) ===')
# 2分钟批量跳水 >=3只 且在2分钟内 -3%
win = [d for d in snaps if d['ts'] >= '2026-09-21 14:00:00']
batch = 0
for i in range(len(win)):
    for j in range(i + 1, len(win)):
        t1 = datetime.datetime.strptime(win[i]['ts'], '%Y-%m-%d %H:%M:%S')
        t2 = datetime.datetime.strptime(win[j]['ts'], '%Y-%m-%d %H:%M:%S')
        if (t2 - t1).total_seconds() > 120:
            break
        m1 = {r['code']: r['pct'] for r in win[i]['rows']}
        m2 = {r['code']: r['pct'] for r in win[j]['rows']}
        c = sum(1 for k in m2 if k in m1 and m2[k] - m1[k] <= -3.0)
        if c >= 3:
            batch += 1
            print('  批量跳水 %s->%s count=%d' % (win[i]['ts'], win[j]['ts'], c))
print('  2分钟批量跳水事件数 = %d' % batch)
# 单票2分钟急跌
fast = 0
for i in range(len(win)):
    for j in range(i + 1, len(win)):
        t1 = datetime.datetime.strptime(win[i]['ts'], '%Y-%m-%d %H:%M:%S')
        t2 = datetime.datetime.strptime(win[j]['ts'], '%Y-%m-%d %H:%M:%S')
        if (t2 - t1).total_seconds() > 120:
            break
        m1 = {r['code']: r['pct'] for r in win[i]['rows']}
        m2 = {r['code']: r['pct'] for r in win[j]['rows']}
        for k in m2:
            if k in m1 and m2[k] - m1[k] <= -3.0:
                fast += 1
print('  单票2分钟急跌(<=-3%)事件数 = %d' % fast)
# 高点回撤
dd = []
for r in last['rows']:
    if r.get('high') and r.get('latest') and r['high'] > 0:
        d = (r['latest'] - r['high']) / r['high'] * 100
        dd.append((round(d, 2), r['code'], r['name'], r['pct']))
dd.sort()
print('  自当日高点回撤前5:', dd[:5])

print('\n=== 观察锚核查(9/18复盘§八 6条) — 是否在池内 ===')
anchors = {'002185': '华天科技', '603248': '锡华科技', '001216': '华瓷股份', '603230': '内蒙新华',
           '002285': '世联行', '605058': '澳弘电子', '002463': '沪电股份'}
codes = {r['code']: r for r in last['rows']}
for c, n in anchors.items():
    r = codes.get(c)
    print('  %s %s -> %s' % (c, n, ('在池内: %s' % r) if r else '不在池内(池为20260911陈旧池)'))
print('  池内代码:', sorted(codes.keys()))
