# -*- coding: utf-8 -*-
"""一次性补数: 为 20260820 各路荐票/竞价池结算票补齐 20260821 日K(bars_cache)。
源=腾讯qfq日K(与bars_cache口径已核验一致)。盘中管道断更第8日致bars_cache缺8/21行。
"""
import os, json, io, time, urllib.request
import pandas as pd

L = r'D:\股票数据\市场数据\_学习'
CDIR = os.path.join(L, '_bars_cache')

def need_codes():
    codes = set()
    for jf, key in [('席位荐票_20260820.json', 'top5'), ('质量荐票_20260820.json', 'top5'),
                    ('题材荐票_20260820.json', 'top5'), ('竞价池_20260820.json', '池')]:
        p = os.path.join(L, jf)
        if not os.path.isfile(p): continue
        d = json.load(io.open(p, encoding='utf-8'))
        items = d.get(key) or []
        for it in items:
            c = str(it.get('代码', '')).zfill(6)
            if c: codes.add(c)
    return sorted(codes)

def fetch_kline(c, market):
    # 腾讯日K: 拉近10日, 取 2026-08-21 行
    url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{c},day,,,10,qfq'
    d = json.load(urllib.request.urlopen(url, timeout=12))
    node = d['data'].get(f'{market}{c}') or {}
    arr = node.get('qfqday') or node.get('day') or []
    for r in arr:
        if r[0] == '2026-08-21':
            return r  # [date, open, close, high, low, volume]
    return None

def append_row(c, r):
    f = os.path.join(CDIR, c + '.csv')
    if not os.path.isfile(f):
        print('  无基础缓存,跳过', c); return False
    b = pd.read_csv(f)
    if '2026-08-21' in b['date'].astype(str).str.replace('-', '').values:
        return False  # 已有
    new = pd.DataFrame([{'date': r[0], 'open': float(r[1]), 'close': float(r[2]),
                         'high': float(r[3]), 'low': float(r[4]), 'volume': float(r[5]),
                         'turnover': None, 'circ_mv亿': None}])
    b = pd.concat([b, new], ignore_index=True)
    b.to_csv(f, index=False)
    return True

codes = need_codes()
print('待查票数:', len(codes))
ok = skip = fail = 0
for c in codes:
    market = 'sh' if c[0] in '56' else 'sz'
    try:
        r = fetch_kline(c, market)
        if r is None:
            print('  无8/21行(可能停牌)', c); fail += 1; continue
        if append_row(c, r): ok += 1
        else: skip += 1
        time.sleep(0.15)
    except Exception as e:
        print('  拉取失败', c, str(e)[:80]); fail += 1
print(f'完成: 补{ok} 已有{skip} 缺/停牌{fail}')
