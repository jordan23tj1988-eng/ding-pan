# -*- coding: utf-8 -*-
import csv, io, os, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.chdir(r'D:\股票数据\市场数据')

def pos(code):
    p = '_学习/_bars_cache/%s.csv' % code
    if not os.path.exists(p):
        return None
    rows = list(csv.DictReader(open(p, encoding='utf-8-sig')))
    rows = [r for r in rows if r['close'] and r['date'] <= '2026-11-04']
    if len(rows) < 30:
        return None
    c = [float(r['close']) for r in rows]
    last = c[-1]
    r20 = (last / c[-21] - 1) * 100 if len(c) > 21 else None
    r60 = (last / c[-61] - 1) * 100 if len(c) > 61 else None
    r250 = (last / c[-251] - 1) * 100 if len(c) > 251 else None
    hi = max(c[-250:]) if len(c) >= 250 else max(c)
    lo = min(c[-250:]) if len(c) >= 250 else min(c)
    return dict(close=last, r20=round(r20, 1) if r20 is not None else None,
                r60=round(r60, 1) if r60 is not None else None,
                r250=round(r250, 1) if r250 is not None else None,
                距高=round((last / hi - 1) * 100, 1), 距低=round((last / lo - 1) * 100, 1), n=len(c))

zt = {r['代码']: r for r in csv.DictReader(open('20261104/zt_pool.csv', encoding='utf-8-sig'))}
cands = ['002636', '002916', '002463', '001389', '002156', '600206', '603186', '002821', '600584',
         '688409', '603061', '002371', '688072', '688652', '688037', '301583', '002536', '600547',
         '002827', '002365', '603906']
print('%-8s %-8s %-4s %-6s %-6s %-6s %-6s %-6s %-6s %-7s' % ('code', 'name', 'lb', 'r20', 'r60', 'r250', '距高', '距低', '封单比%', '换手%'))
for c in cands:
    p = pos(c)
    r = zt.get(c)
    if not p or not r:
        print(c, 'MISS', p is None, r is None); continue
    circ = float(r['流通市值']) / 1e8
    fb = float(r['封板资金']) / 1e8 / circ * 100 if circ else None
    print('%-8s %-8s %-4s %-6s %-6s %-6s %-6s %-6s %-6.2f  %-7.2f  circ=%.1f亿 封单%.2f亿' % (
        c, r['名称'], r['连板数'], p['r20'], p['r60'], p['r250'], p['距高'], p['距低'], fb, float(r['换手率']), circ, float(r['封板资金'])/1e8))

# 今日 118 只整体位置分布
allp = []
for c, r in zt.items():
    p = pos(c)
    if p:
        allp.append((c, r['名称'], p))
import statistics as st
for k in ['r20', 'r250', '距高']:
    vals = [x[2][k] for x in allp if x[2][k] is not None]
    print('全池 %s 中位 %.1f  (n=%d)' % (k, st.median(vals), len(vals)))
