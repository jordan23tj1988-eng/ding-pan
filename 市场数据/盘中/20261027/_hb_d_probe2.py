# -*- coding: utf-8 -*-
"""hb-d 辅助取证：上证/300296 分时（决断前）+ 汽车零部涨停明细。只读。"""
import json, urllib.request, os

D = os.path.dirname(os.path.abspath(__file__))


def http_get(url, timeout=12, gbk=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
        'Referer': 'http://quote.eastmoney.com/'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return raw.decode('gbk', 'ignore') if gbk else raw.decode('utf-8', 'ignore')


def minute(secid):
    url = ('http://push2his.eastmoney.com/api/qt/stock/kline/get?secid=' + secid +
           '&klt=1&fqt=0&lmt=400&end=20500101&fields1=f1,f2,f3,f4,f5'
           '&fields2=f51,f52,f53,f54,f55,f56,f57')
    j = json.loads(http_get(url))
    ks = ((j.get('data') or {}).get('klines') or [])
    out = []
    for k in ks:
        p = k.split(',')
        out.append({'t': p[0][11:16], 'o': float(p[1]), 'c': float(p[2]),
                    'h': float(p[3]), 'l': float(p[4])})
    return out


res = {}
for name, secid in [('sh000001', '1.000001'), ('sz300296', '0.300296'), ('sz002979', '0.002979')]:
    try:
        m = minute(secid)
        lows = [x for x in m if x['t'] <= '13:32']
        res[name] = {'n': len(m), 'last': m[-1] if m else None,
                     'day_low': min(x['l'] for x in lows) if lows else None,
                     'low_time': [x['t'] for x in lows if x['l'] == min(y['l'] for y in lows)][:3] if lows else None,
                     'below_ref': [x['t'] for x in lows if (name == 'sh000001' and x['l'] < 3685) or
                                   (name == 'sz300296' and x['l'] < 6.49)][:15]}
    except Exception as e:
        res[name] = {'error': repr(e)}

# 汽车零部涨停明细
try:
    url = ('http://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989'
           '&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date=' + '20261027')
    zt = json.loads(http_get(url))['data']['pool']
    auto = [{'c': str(r['c']), 'n': r['n'], 'lb': r.get('lbc'), 'ind': r.get('hybk'),
             'fbt': r.get('fbt'), 'zbc': r.get('zbc'), 'amount': r.get('amount')}
            for r in zt if (r.get('hybk') or '').startswith('汽车零')]
    res['auto_parts'] = auto
    res['auto_lb_max'] = max([a['lb'] for a in auto], default=0)
except Exception as e:
    res['auto_parts'] = {'error': repr(e)}

json.dump(res, open(os.path.join(D, '_hb_d_probe2.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
