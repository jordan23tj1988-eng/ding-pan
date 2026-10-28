# -*- coding: utf-8 -*-
"""hb-b 10:30 场取数：腾讯报价(持仓/指数) + 东财 ZT/ZB/DT 池。只读接口，不写生产数据。"""
import json, urllib.request, datetime, os

OUT = os.path.dirname(os.path.abspath(__file__))

def http_get(url, timeout=15, gbk=False):
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
        key = seg.split('=')[0].replace('v_', '')
        f = seg.split('="')[1].strip('"').split('~')
        if len(f) < 40:
            continue
        try:
            out[key] = {'code': f[2], 'name': f[1], 'px': float(f[3]), 'pre': float(f[4]),
                        'open': float(f[5]), 'pct': float(f[32]), 'high': float(f[33]),
                        'low': float(f[34]), 'amt_wan': float(f[37]) if f[37] else None,
                        't': f[30]}
        except Exception as e:
            out[key] = {'err': str(e), 'raw': f[:6]}
    return out

def em_pool(kind, date):
    base = {'zt': 'getTopicZTPool', 'zb': 'getTopicZBPool', 'dt': 'getTopicDTPool'}[kind]
    url = (f'http://push2ex.eastmoney.com/{base}?ut=7eea3edcaed734bea9cbfc24409ed989'
           f'&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date={date}')
    txt = http_get(url)
    j = json.loads(txt)
    d = j.get('data') or {}
    rows = d.get('pool') or []
    return rows, j.get('rc'), txt[:200] if not rows else None

if __name__ == '__main__':
    date = datetime.datetime.now().strftime('%Y%m%d')
    quote_codes = ['sz002242', 'sz003021', 'sz300296', 'sz002979', 'sz300561',
                   'sh000001', 'sz399001', 'sz399006', 'sh000688']
    q = tencent(quote_codes)
    print('=== TENCENT', datetime.datetime.now().strftime('%H:%M:%S'), '===')
    for k, v in q.items():
        if 'err' in v:
            print(k, 'ERR', v)
        else:
            print(k, v['name'], 'px', v['px'], 'pct', v['pct'], 'open', v['open'],
                  'high', v['high'], 'low', v['low'], 't', v['t'])
    out = {'quote': q, 'ts': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    for kind in ('zt', 'zb', 'dt'):
        try:
            rows, rc, err = em_pool(kind, date)
            print(f'\n=== EM {kind} n={len(rows)} rc={rc} ===')
            for r in rows[:8]:
                print(r)
            out[kind] = rows
        except Exception as e:
            print(f'EM {kind} FAIL {e}')
            out[kind + '_err'] = str(e)
    with open(os.path.join(OUT, '_hb_b_quote.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    print('\nsaved _hb_b_quote.json', os.path.getsize(os.path.join(OUT, '_hb_b_quote.json')))
