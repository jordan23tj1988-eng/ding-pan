# -*- coding: utf-8 -*-
"""hb-a 09:40 场取数：腾讯报价 + 东财 ZT/ZB/DT 池 + 候选行业归属。只读生产接口，不写生产数据。"""
import json, urllib.request, datetime, os, sys

OUT = os.path.dirname(os.path.abspath(__file__))


def http_json(url, timeout=15, ref='http://quote.eastmoney.com/'):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': ref})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8', 'ignore'))


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
                't': f[30], 'limit_up': float(f[47]) if len(f) > 47 and f[47] else None,
            }
        except Exception as e:
            out[key] = {'err': str(e), 'raw': f[:6]}
    return out


def em_pool(kind, date):
    base = {'zt': 'getTopicZTPool', 'zb': 'getTopicZBPool', 'dt': 'getTopicDTPool'}[kind]
    url = (f'http://push2ex.eastmoney.com/{base}?ut=7eea3edcaed734bea9cbfc24409ed989'
           f'&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date={date}')
    js = http_json(url)
    return (js.get('data') or {}).get('pool') or []


def industry(secid):
    url = (f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}'
           f'&fields=f57,f58,f127,f128,f43,f170')
    try:
        d = (http_json(url).get('data') or {})
        return {'code': d.get('f57'), 'name': d.get('f58'),
                'industry': d.get('f127'), 'region': d.get('f128')}
    except Exception as e:
        return {'err': str(e)}


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'now'
    date = '20261026'
    codes = ['sz002626', 'sz002639', 'sz002242', 'sh603370', 'sh600487',
             'sz300296', 'sz002979', 'sz003021', 'sz301502',
             'sh000001', 'sz399001', 'sz399006', 'sh000688']
    q = tencent(codes)
    json.dump({'fetched': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'rows': q},
              open(os.path.join(OUT, f'_hb_a_quote_{tag}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    pools = {'fetched': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    for k in ('zt', 'zb', 'dt'):
        try:
            pools[k] = em_pool(k, date)
        except Exception as e:
            pools[k] = {'err': str(e)}
        pools[k + '_n'] = len(pools[k]) if isinstance(pools[k], list) else None
    json.dump(pools, open(os.path.join(OUT, f'_hb_a_pools_{tag}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    inds = {}
    for code, sec in (('300296', '0.300296'), ('002979', '0.002979'), ('003021', '0.003021')):
        inds[code] = industry(sec)
    json.dump(inds, open(os.path.join(OUT, f'_hb_a_industry_{tag}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(json.dumps({'tag': tag, 'zt': pools.get('zt_n'), 'zb': pools.get('zb_n'),
                      'dt': pools.get('dt_n'), 'inds': inds}, ensure_ascii=False))
