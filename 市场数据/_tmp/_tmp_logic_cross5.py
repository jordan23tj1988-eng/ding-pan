import json, io, sys, os, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')
D = '20260826'

# --- 600256 bars
p = os.path.join(X, '_bars_cache', '600256.csv')
rows = list(csv.DictReader(open(p, 'r', encoding='utf-8-sig')))
print('600256 bars n=%d cols=%s' % (len(rows), rows[0].keys()))
print('tail6:')
for r in rows[-6:]:
    print('  ', {k: r[k] for k in list(r.keys())[:6]})
cl = [(r['date'], float(r['close'])) for r in rows if r.get('close') not in (None, '')]
last_d, last_c = cl[-1]
print('last', last_d, last_c)
w = [c for d, c in cl][-250:]
hi250 = max(w); lo250 = min(w)
c250 = [c for d, c in cl][-251]
c20 = [c for d, c in cl][-21]
c5 = [c for d, c in cl][-6]
prev = cl[-2][1]
print('日涨跌%%=%.2f  r5=%.2f%%  r20=%.2f%%  r250=%.2f%%  距250高=%.2f%%  距250低=+%.2f%%'
      % ((last_c/prev-1)*100, (last_c/c5-1)*100, (last_c/c20-1)*100, (last_c/c250-1)*100,
         (last_c/hi250-1)*100, (last_c/lo250-1)*100))
print('成本5.40 浮动%%=%.2f' % ((last_c/5.40-1)*100))

# --- zt_pool + 归位 join
zt = list(csv.DictReader(open(os.path.join(B, D, 'zt_pool.csv'), 'r', encoding='utf-8-sig')))
gw = json.load(open(os.path.join(X, '题材归位_%s.json' % D), 'r', encoding='utf-8'))['映射']
print()
print('=== 52涨停 × 归位 (代码 名称 连板 行业 | 大方向/环节 档) ===')
for r in zt:
    c = r['代码']; g = gw.get(c, {})
    print(' %s %-6s %sB %-8s | %s/%s %s' % (c, r['名称'], r['连板数'], r['所属行业'],
          g.get('大方向'), g.get('环节'), g.get('来源档')))

# --- 待深挖三线的个股
print()
print('=== 待深挖★新线 今日涨停成员 ===')
for line in ['有色/贵金属', '汽车/零部件', '建筑/装修装饰']:
    mem = [(c, g) for c, g in gw.items() if g.get('大方向') == line]
    print(' %s: %s' % (line, [(c, [r['名称'] for r in zt if r['代码']==c][0], g.get('环节')) for c, g in mem]))
