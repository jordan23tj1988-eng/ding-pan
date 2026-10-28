# -*- coding: utf-8 -*-
"""hb-d 13:30 场：决断后下一tick报价（fills 的 px_exec 基准）。只读。"""
import json, urllib.request, datetime, os

D = os.path.dirname(os.path.abspath(__file__))


def http_get(url, timeout=12, gbk=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
        'Referer': 'http://quote.eastmoney.com/'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return raw.decode('gbk', 'ignore') if gbk else raw.decode('utf-8', 'ignore')


CODES = ['sz300296', 'sz002979', 'sh000001', 'sz399001', 'sz399006', 'sh000688']
ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
raw = http_get('http://qt.gtimg.cn/q=' + ','.join(CODES), gbk=True)
out = {}
for seg in raw.split(';'):
    seg = seg.strip()
    if '="' not in seg:
        continue
    f = seg.split('="')[1].strip('"').split('~')
    if len(f) < 40:
        continue
    try:
        out[f[2]] = {'name': f[1], 'px': float(f[3]), 'pre': float(f[4]),
                     'pct': float(f[32]), 'high': float(f[33]), 'low': float(f[34]), 't': f[30]}
    except Exception:
        pass
json.dump({'fetch_ts': ts, 'quote': out},
          open(os.path.join(D, '_hb_d_next.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('NEXT_FETCH', ts)
for c, v in out.items():
    print(c, v['name'], v['px'], v['pct'], 'tick', v['t'])
