# -*- coding: utf-8 -*-
"""一次性: 全量检查 20260820 结算票的 bars 8/21 覆盖, 缺则从腾讯qfq补(口径已核验)。"""
import os, json, io, time, urllib.request
import pandas as pd

L = r'D:\股票数据\市场数据\_学习'
CDIR = os.path.join(L, '_bars_cache')

def need_codes():
    codes = set()
    # 席位 top5
    p = os.path.join(L, '席位荐票_20260820.json')
    if os.path.isfile(p):
        for it in json.load(io.open(p, encoding='utf-8')).get('top5', []):
            codes.add(str(it.get('代码', '')).zfill(6))
    # 质量 top5
    p = os.path.join(L, '涨停质量荐票_20260820.json')
    if os.path.isfile(p):
        for it in json.load(io.open(p, encoding='utf-8')).get('top5', []):
            codes.add(str(it.get('代码', '')).zfill(6))
    # 题材 top5
    p = os.path.join(L, '题材荐票_20260820.json')
    if os.path.isfile(p):
        for it in json.load(io.open(p, encoding='utf-8')).get('荐票', [])[:5]:
            codes.add(str(it.get('代码', '')).zfill(6))
    # 竞价池 26
    p = os.path.join(L, '竞价池发出_20260820.json')
    if os.path.isfile(p):
        d = json.load(io.open(p, encoding='utf-8'))
        def collect(obj, acc):
            if isinstance(obj, dict):
                c = obj.get('代码')
                if c and str(c).isdigit(): acc.add(str(c).zfill(6))
                for v in obj.values(): collect(v, acc)
            elif isinstance(obj, list):
                for v in obj: collect(v, acc)
        collect(d, codes)
    return sorted(codes)

def fetch_kline(c, market):
    url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{c},day,,,10,qfq'
    d = json.load(urllib.request.urlopen(url, timeout=12))
    node = d['data'].get(f'{market}{c}') or {}
    arr = node.get('qfqday') or node.get('day') or []
    for r in arr:
        if r[0] == '2026-08-21':
            return r
    return None

def append_row(c, r):
    f = os.path.join(CDIR, c + '.csv')
    if not os.path.isfile(f):
        return 'nobase'
    b = pd.read_csv(f)
    if '20260821' in b['date'].astype(str).str.replace('-', '').values:
        return 'have'
    new = pd.DataFrame([{'date': r[0], 'open': float(r[1]), 'close': float(r[2]),
                         'high': float(r[3]), 'low': float(r[4]), 'volume': float(r[5]),
                         'turnover': None, 'circ_mv亿': None}])
    b = pd.concat([b, new], ignore_index=True)
    b.to_csv(f, index=False)
    return 'added'

codes = need_codes()
print('清单票数:', len(codes))
st = {'added': 0, 'have': 0, 'nobase': 0, 'fail': 0}
for c in codes:
    f = os.path.join(CDIR, c + '.csv')
    if os.path.isfile(f):
        b = pd.read_csv(f)
        if '20260821' in b['date'].astype(str).str.replace('-', '').values:
            st['have'] += 1; continue
    market = 'sh' if c[0] in '56' else 'sz'
    try:
        r = fetch_kline(c, market)
        if r is None: st['nobase'] += 1; print('  无8/21行情(停牌?)', c); continue
        st[append_row(c, r)] += 1
        time.sleep(0.12)
    except Exception as e:
        st['fail'] += 1; print('  失败', c, str(e)[:70])
print('结果:', st)
