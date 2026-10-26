# -*- coding: utf-8 -*-
"""hb-f 14:45 尾盘深场B取数：腾讯报价(持仓+指数) + 东财 ZT/ZB/DT 池。只读接口，不写生产数据。"""
import json, urllib.request, datetime, os, sys

OUT = os.path.dirname(os.path.abspath(__file__))


def http_get(url, timeout=12, gbk=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
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
        key = seg.split('=')[0].replace('v_', '')
        f = seg.split('="')[1].strip('"').split('~')
        if len(f) < 40:
            continue
        try:
            out[key] = {
                'code': f[2], 'name': f[1], 'px': float(f[3]), 'pre': float(f[4]),
                'open': float(f[5]), 'pct': float(f[32]), 'high': float(f[33]),
                'low': float(f[34]), 'vol_hand': float(f[36]) if f[36] else None,
                'amt_wan': float(f[37]) if f[37] else None,
                't': f[30],
            }
        except Exception as e:
            out[key] = {'err': str(e), 'raw': f[:8]}
    return out


def em_pool(kind, date):
    base = {'zt': 'getTopicZTPool', 'zb': 'getTopicZBPool', 'dt': 'getTopicDTPool'}[kind]
    url = (f'http://push2ex.eastmoney.com/{base}?ut=7eea3edcaed734bea9cbfc24409ed989'
           f'&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date={date}')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
                                               'Referer': 'http://quote.eastmoney.com/'})
    with urllib.request.urlopen(req, timeout=15) as r:
        js = json.loads(r.read().decode('utf-8', 'ignore'))
    return (js.get('data') or {}).get('pool') or []


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'now'
    codes = ['sz002242', 'sz003021', 'sz002639', 'sh600487', 'sh603370',
             'sh000001', 'sz399001', 'sz399006', 'sh000688']
    q = tencent(codes)
    json.dump({'fetched': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'rows': q},
              open(os.path.join(OUT, f'_hb_f_quote_{tag}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    date = '20261026'
    pools = {'fetched': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             'pool_date_arg': date}
    for k in ('zt', 'zb', 'dt'):
        try:
            pools[k] = em_pool(k, date)
        except Exception as e:
            pools[k] = {'error': repr(e)}
    json.dump(pools, open(os.path.join(OUT, f'_hb_f_pools_{tag}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    for k, v in q.items():
        print(k, v.get('name'), v.get('px'), v.get('pct'), 'hi', v.get('high'), 'lo', v.get('low'), 't=', v.get('t'))
    for k in ('zt', 'zb', 'dt'):
        v = pools[k]
        print(k, 'ERR ' + str(v)[:160] if isinstance(v, dict) else len(v))
