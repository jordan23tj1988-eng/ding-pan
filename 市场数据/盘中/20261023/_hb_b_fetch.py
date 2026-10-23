# -*- coding: utf-8 -*-
"""hb-b 10:30 场取数：腾讯报价 + 东财 ZT/ZB/DT 池。只读生产接口，不写生产数据。"""
import json, urllib.request, datetime, os, sys

OUT = os.path.dirname(os.path.abspath(__file__))

def http(url, timeout=12):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('gbk', 'ignore'), r.read

def tencent(codes):
    url = 'http://qt.gtimg.cn/q=' + ','.join(codes)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=12) as r:
        raw = r.read().decode('gbk', 'ignore')
    out = {}
    for seg in raw.split(';'):
        seg = seg.strip()
        if '="' not in seg:
            continue
        key = seg.split('=')[0].replace('v_', '')
        f = seg.split('="')[1].strip('"').split('~')
        if len(f) < 40:
            continue
        try:
            out[key] = {
                'code': f[2], 'name': f[1], 'px': float(f[3]), 'pre': float(f[4]),
                'open': float(f[5]), 'pct': float(f[32]), 'high': float(f[33]),
                'low': float(f[34]), 'amt_wan': float(f[37]) if f[37] else None,
                't': f[30],
            }
        except Exception as e:
            out[key] = {'err': str(e), 'raw': f[:6]}
    return out

def em_pool(kind, date):
    base = {
        'zt': 'getTopicZTPool', 'zb': 'getTopicZBPool', 'dt': 'getTopicDTPool'
    }[kind]
    url = (f'http://push2ex.eastmoney.com/{base}?ut=7eea3edcaed734bea9cbfc24409ed989'
           f'&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date={date}')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
                                               'Referer': 'http://quote.eastmoney.com/'})
    with urllib.request.urlopen(req, timeout=15) as r:
        js = json.loads(r.read().decode('utf-8', 'ignore'))
    pool = (js.get('data') or {}).get('pool') or []
    return pool

if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'now'
    codes = ['sz002242', 'sh603370', 'sz002639', 'sz003021', 'sh601091',
             'sh000001', 'sz399001', 'sz399006']
    q = tencent(codes)
    qd = {'fetched': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'rows': q}
    json.dump(qd, open(os.path.join(OUT, f'_hb_b_quote_{tag}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    date = '20261023'
    pools = {'fetched': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    for k in ('zt', 'zb', 'dt'):
        try:
            pools[k] = em_pool(k, date)
        except Exception as e:
            pools[k] = {'error': repr(e)}
    json.dump(pools, open(os.path.join(OUT, f'_hb_b_pools_{tag}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print('QUOTES', json.dumps(q, ensure_ascii=False))
    for k in ('zt', 'zb', 'dt'):
        v = pools[k]
        print(k, 'ERR' if isinstance(v, dict) else len(v))
