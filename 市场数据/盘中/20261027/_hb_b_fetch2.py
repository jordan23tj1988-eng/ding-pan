# -*- coding: utf-8 -*-
"""hb-b 10:30 场：决断后取价（fills 的 px_exec 基准）。只读腾讯/东财。"""
import json, urllib.request, datetime, os, collections

D = os.path.dirname(os.path.abspath(__file__))

def http_get(url, timeout=12, gbk=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
        'Referer': 'http://quote.eastmoney.com/'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return raw.decode('gbk', 'ignore') if gbk else raw.decode('utf-8', 'ignore')

CODES = ['sz002242', 'sz003021', 'sz300296', 'sz002979', 'sz300561', 'sz002474',
         'sz688386', 'sh688386', 'sz000700', 'sh000001', 'sz399001', 'sz399006', 'sh000688']

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
                         'pct': float(f[32]), 'high': float(f[33]), 'low': float(f[34]),
                         't': f[30]}
        except Exception:
            pass
    return out

ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
q = tencent(CODES)
print('QUOTE_TS', ts)
for c, v in q.items():
    print(c, v['name'], 'px', v['px'], 'pct', v['pct'], 't', v['t'])

# 全市场涨停池行业分布（在线口，仅计行业聚合）
def em_pool(kind, date):
    base = {'zt': 'getTopicZTPool', 'zb': 'getTopicZBPool', 'dt': 'getTopicDTPool'}[kind]
    url = (f'http://push2ex.eastmoney.com/{base}?ut=7eea3edcaed734bea9cbfc24409ed989'
           f'&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date={date}')
    j = json.loads(http_get(url))
    return (j.get('data') or {}).get('pool') or []

date = datetime.datetime.now().strftime('%Y%m%d')
info = {'ts': ts, 'quote': q}
for kind in ('zt', 'zb', 'dt'):
    try:
        rows = em_pool(kind, date)
        info[kind] = rows
        print(kind, 'n', len(rows))
        if rows:
            cnt = collections.Counter(r.get('hybk') or '未知' for r in rows)
            print('  top industry', cnt.most_common(5))
            print('  max_lb', max((r.get('lbc') or 0) for r in rows))
    except Exception as e:
        info[kind + '_err'] = str(e)
        print(kind, 'FAIL', e)

with open(os.path.join(D, '_hb_b_quote_exec.json'), 'w', encoding='utf-8') as f:
    json.dump(info, f, ensure_ascii=False)
print('saved', os.path.getsize(os.path.join(D, '_hb_b_quote_exec.json')))
