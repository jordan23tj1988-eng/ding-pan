# -*- coding: utf-8 -*-
"""hb-c 11:00 场：决断帧取数（帧池统计 + 腾讯报价 + 东财三池）。只读，不写生产数据。"""
import json, urllib.request, datetime, os, collections, statistics

D = os.path.dirname(os.path.abspath(__file__))

def http_get(url, timeout=12, gbk=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
        'Referer': 'http://quote.eastmoney.com/'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return raw.decode('gbk', 'ignore') if gbk else raw.decode('utf-8', 'ignore')

def tencent(codes):
    raw = http_get('http://qt.gtimg.cn/q=' + ','.join(codes), gbk=True)
    out = {}
    for seg in raw.split(';'):
        seg = seg.strip()
        if '="' not in seg:
            continue
        f = seg.split('="')[1].strip('"').split('~')
        if len(f) < 40:
            continue
        try:
            out[f[2]] = {'name': f[1], 'px': float(f[3]), 'pre': float(f[4]), 'open': float(f[5]),
                         'pct': float(f[32]), 'high': float(f[33]), 'low': float(f[34]), 't': f[30],
                         'vol': f[36] if len(f) > 36 else None, 'amt': f[37] if len(f) > 37 else None}
        except Exception:
            pass
    return out

def em_pool(kind, date):
    base = {'zt': 'getTopicZTPool', 'zb': 'getTopicZBPool', 'dt': 'getTopicDTPool'}[kind]
    url = (f'http://push2ex.eastmoney.com/{base}?ut=7eea3edcaed734bea9cbfc24409ed989'
           f'&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date={date}')
    j = json.loads(http_get(url))
    return (j.get('data') or {}).get('pool') or []

# ---------- 1. 帧池统计 ----------
fp = os.path.join(D, 'realtime_ticks.jsonl')
frames = []
for l in open(fp, encoding='utf-8').read().strip().split('\n'):
    j = json.loads(l)
    if j.get('rows'):
        frames.append(j)

def ts2dt(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

last = frames[-1]
now = datetime.datetime.now()
gap_max = max((ts2dt(frames[i+1]['ts']) - ts2dt(frames[i]['ts'])).total_seconds()
              for i in range(len(frames)-1))

def stats(rows):
    p = [r['pct'] for r in rows]
    return {'n': len(p), 'median': round(statistics.median(p), 2), 'mean': round(sum(p)/len(p), 2),
            'up': sum(1 for x in p if x > 0), 'down': sum(1 for x in p if x < 0),
            'ge98': sum(1 for x in p if x >= 9.8), 'le5': sum(1 for x in p if x <= -5),
            'le98': sum(1 for x in p if x <= -9.8)}

cur = stats(last['rows'])
traj = []
for f in frames:
    if ts2dt(f['ts']).minute % 10 == 0 and ts2dt(f['ts']).second < 5:
        s = stats(f['rows'])
        traj.append((f['ts'][11:16], s['median'], s['ge98']))

# 掉板：首帧 ≥9.8% 的成员现是否仍 ≥9.8%
first = {r['code']: r for r in frames[0]['rows']}
first98 = [c for c, r in first.items() if r['pct'] >= 9.8]
nowmap = {r['code']: r for r in last['rows']}
held = [c for c in first98 if nowmap.get(c, {}).get('pct', -99) >= 9.8]
lost = [(c, first[c]['name'], first[c]['pct'], nowmap.get(c, {}).get('pct')) for c in first98 if c not in held]

# 题材批量跳水：相邻帧配对(≥100s)，统计末 30 分钟内跌落≥3pp 的只数
pairs = []
for i in range(len(frames)-1):
    a, b = frames[i], frames[i+1]
    dt = (ts2dt(b['ts']) - ts2dt(a['ts'])).total_seconds()
    if dt < 100:
        continue
    ma = {r['code']: r for r in a['rows']}
    drops = []
    for r in b['rows']:
        p0 = ma.get(r['code'], {}).get('pct')
        if p0 is None:
            continue
        d = r['pct'] - p0
        if d <= -3:
            drops.append((r['code'], r['name'], round(p0, 2), round(r['pct'], 2), round(d, 2)))
    pairs.append({'t': b['ts'], 'n': len(drops), 'drops': drops})

recent = [p for p in pairs if (ts2dt(last['ts']) - ts2dt(p['t'])).total_seconds() <= 1800]
worst_recent = max(recent, key=lambda x: x['n']) if recent else None
worst_all = max(pairs, key=lambda x: x['n']) if pairs else None

# 单票 2 分钟级最大回撤（池内）
maxdd = []
for i in range(len(frames)-1):
    a, b = frames[i], frames[i+1]
    ma = {r['code']: r for r in a['rows']}
    for r in b['rows']:
        p0 = ma.get(r['code'], {}).get('pct')
        if p0 is None:
            continue
        maxdd.append((round(r['pct']-p0, 2), r['code'], r['name'], a['ts'][11:19], b['ts'][11:19], round(p0, 2), round(r['pct'], 2)))
maxdd.sort()

# ---------- 2. 腾讯报价 ----------
CODES = ['sz003021', 'sz300561', 'sz002474', 'sz300296', 'sz002979', 'sz002242', 'sz002979',
         'sh000001', 'sz399001', 'sz399006', 'sh000688']
ts = now.strftime('%Y-%m-%d %H:%M:%S')
q = tencent(CODES)

# ---------- 3. 东财三池 ----------
date = now.strftime('%Y%m%d')
pools, perr = {}, {}
for kind in ('zt', 'zb', 'dt'):
    try:
        rows = em_pool(kind, date)
        pools[kind] = rows
    except Exception as e:
        perr[kind] = str(e)

hy = collections.Counter(r.get('hybk') or '未知' for r in pools.get('zt', []))
maxlb = max([(r.get('lbc') or 0) for r in pools.get('zt', [])], default=None)
zt_rows = [
    {'code': str(r.get('c')), 'name': r.get('n'), 'lb': r.get('lbc'), 'fbt': r.get('fbt'),
     'zbc': r.get('zbc'), 'hy': r.get('hybk'), 'pct': r.get('zdp')}
    for r in pools.get('zt', [])]

out = {
    'probe_ts': ts,
    'frame': {'file': 'realtime_ticks.jsonl', 'n_frames': len(frames), 'last_ts': last['ts'],
              'age_sec_at_probe': round((now - ts2dt(last['ts'])).total_seconds()),
              'gap_max_sec': gap_max, 'pool_date': last.get('pool_date'),
              'pool_kind': last.get('pool_kind'), 'stale': last.get('pool_stale')},
    'pool_now': cur, 'traj_10min': traj,
    'first98': len(first98), 'still98': len(held), 'lost': lost,
    'jumpdown_recent30m': worst_recent, 'jumpdown_all': worst_all,
    'maxdd_top5': maxdd[:5],
    'quote_ts': ts, 'quote': q,
    'zt_n': len(pools.get('zt', [])), 'zb_n': len(pools.get('zb', [])), 'dt_n': len(pools.get('dt', [])),
    'zb_rate': (round(len(pools.get('zb', [])) / max(1, len(pools.get('zb', [])) + len(pools.get('zt', []))), 4)
                if pools.get('zt') is not None else None),
    'max_lb': maxlb, 'hy_top': hy.most_common(6), 'zt_rows': zt_rows, 'pool_err': perr,
}
with open(os.path.join(D, '_hb_c_probe.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print('PROBE_TS', ts)
print('FRAME last', last['ts'], 'age_s', out['frame']['age_sec_at_probe'], 'gapmax', gap_max, 'frames', len(frames))
print('POOL', cur)
print('TRAJ', traj)
print('FIRST98', len(first98), 'STILL', len(held), 'LOST', lost)
print('RECENT30M', json.dumps(worst_recent, ensure_ascii=False))
print('ALLMAX', json.dumps(worst_all, ensure_ascii=False)[:600])
print('MAXDD', maxdd[:5])
print('QUOTE')
for c, v in q.items():
    print(' ', c, v['name'], 'px', v['px'], 'pct', v['pct'], 'high', v['high'], 'low', v['low'], 'open', v['open'], 't', v['t'])
print('ZT', len(pools.get('zt', [])), 'ZB', len(pools.get('zb', [])), 'DT', len(pools.get('dt', [])),
      'rate', out['zb_rate'], 'maxlb', maxlb, 'err', perr)
print('HY', hy.most_common(6))
