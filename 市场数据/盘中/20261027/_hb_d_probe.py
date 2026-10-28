# -*- coding: utf-8 -*-
"""hb-d 13:30 午后延续段：决断帧取数（帧池统计 + 腾讯报价 + 东财三池 + 3分钟跳水簇）。只读，不写生产数据。"""
import json, urllib.request, datetime, os, statistics

D = os.path.dirname(os.path.abspath(__file__))
DEC = datetime.datetime.now().replace(microsecond=0)


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
                         'pct': float(f[32]), 'high': float(f[33]), 'low': float(f[34]), 't': f[30]}
        except Exception:
            pass
    return out


def em_pool(kind, date):
    base = {'zt': 'getTopicZTPool', 'zb': 'getTopicZBPool', 'dt': 'getTopicDTPool'}[kind]
    url = (f'http://push2ex.eastmoney.com/{base}?ut=7eea3edcaed734bea9cbfc24409ed989'
           f'&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date={date}')
    j = json.loads(http_get(url))
    return (j.get('data') or {}).get('pool') or []


def ts2dt(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


# ---------- 1. 帧池统计 ----------
fp = os.path.join(D, 'realtime_ticks.jsonl')
frames = []
for l in open(fp, encoding='utf-8'):
    l = l.strip()
    if not l:
        continue
    j = json.loads(l)
    if j.get('rows'):
        frames.append(j)
elig = [f for f in frames if ts2dt(f['ts']) <= DEC]
last = elig[-1]
gaps = [(ts2dt(elig[i+1]['ts']) - ts2dt(elig[i]['ts'])).total_seconds() for i in range(len(elig)-1)]


def stats(rows):
    p = [r['pct'] for r in rows if r.get('pct') is not None]
    return {'n': len(p), 'median': round(statistics.median(p), 2), 'mean': round(sum(p)/len(p), 2),
            'up': sum(1 for x in p if x > 0), 'down': sum(1 for x in p if x < 0),
            'ge98': sum(1 for x in p if x >= 9.8), 'le5': sum(1 for x in p if x <= -5),
            'le98': sum(1 for x in p if x <= -9.8)}


cur = stats(last['rows'])
# 关键时点轨迹
marks = ['09:31', '10:01', '10:21', '10:35', '11:04', '13:01', '13:15', '13:29']
traj = []
for m in marks:
    cand = [f for f in elig if f['ts'][11:16] >= m]
    if cand:
        s = stats(cand[0]['rows'])
        traj.append((cand[0]['ts'][11:19], s['median'], s['ge98'], s['le5']))

# 掉板
first = {r['code']: r for r in elig[0]['rows']}
nowm = {r['code']: r for r in last['rows']}
drop_board = [(r['code'], r['name'], r['pct'], nowm.get(r['code'], {}).get('pct'))
              for r in elig[0]['rows'] if r.get('pct', 0) >= 9.8]

# 3分钟配对跳水簇（决断前30分钟）
clusters = []
for i in range(len(elig)-1, -1, -1):
    ji = elig[i]
    ti = ts2dt(ji['ts'])
    if (DEC - ti).total_seconds() > 1800:
        break
    base = None
    for k in range(i-1, -1, -1):
        d = (ti - ts2dt(elig[k]['ts'])).total_seconds()
        if d >= 150:
            base = elig[k]
            break
        if d > 240:
            break
    if base is None:
        continue
    bp = {r['code']: r['pct'] for r in base['rows'] if r.get('pct') is not None}
    drops = [(r['code'], r['name'], round(r['pct'] - bp[r['code']], 2)) for r in ji['rows']
             if r.get('pct') is not None and r['code'] in bp and (r['pct'] - bp[r['code']]) <= -3.0]
    if len(drops) >= 2:
        clusters.append({'ts': ti.strftime('%H:%M:%S'), 'n': len(drops), 'drops': drops})
max_cluster_30m = max([c['n'] for c in clusters], default=0)

# ---------- 2. 报价 ----------
QCODES = ['sz300296', 'sz002979', 'sz003021', 'sz300561', 'sz002474',
          'sh000001', 'sz399001', 'sz399006', 'sh000688']
quotes = tencent(QCODES)

# ---------- 3. 东财三池 ----------
today = DEC.strftime('%Y%m%d')
pools = {}
try:
    zt = em_pool('zt', today)
    zb = em_pool('zb', today)
    dt = em_pool('dt', today)
    lb = {}
    for r in zt:
        c = str(r.get('c'))
        lb[c] = r.get('lbc', 1)
    inds = {}
    for r in zt:
        ind = r.get('hybk') or '—'
        inds[ind] = inds.get(ind, 0) + 1
    pools = {'zt': len(zt), 'zb': len(zb), 'dt': len(dt),
             'zb_rate': round(len(zb)/(len(zt)+len(zb)), 4) if (len(zt)+len(zb)) else None,
             'max_lb': max(lb.values()) if lb else None,
             'top_ind': sorted(inds.items(), key=lambda x: -x[1])[:4],
             'zt_time': DEC.strftime('%H:%M:%S')}
except Exception as e:
    pools = {'error': repr(e)}

out = {'dec_ts': DEC.strftime('%Y-%m-%d %H:%M:%S'),
       'frames': {'n_all': len(frames), 'n_elig': len(elig), 'first': elig[0]['ts'],
                  'last': last['ts'], 'age_s': round((DEC - ts2dt(last['ts'])).total_seconds(), 1),
                  'max_gap_s': round(max(gaps), 1) if gaps else None,
                  'mean_gap_s': round(statistics.mean(gaps), 1) if gaps else None,
                  'pool_date': last.get('pool_date'), 'n_rows': len(last['rows'])},
       'pool_now': cur, 'traj': traj, 'drop_board': drop_board,
       'clusters_30m': clusters[-6:], 'max_cluster_30m': max_cluster_30m,
       'quotes': quotes, 'pools': pools}
json.dump(out, open(os.path.join(D, '_hb_d_probe.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
