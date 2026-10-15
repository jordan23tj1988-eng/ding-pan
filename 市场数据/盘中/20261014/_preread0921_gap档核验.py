import os, json, io, re, collections, statistics

L = r'D:/股票数据/市场数据/_学习'
CDIR = os.path.join(L, '_bars_cache')
ths = json.load(open(os.path.join(L, '_ths_zt_pool.json'), encoding='utf-8'))

def bars(c):
    f = os.path.join(CDIR, c + '.csv')
    if not os.path.isfile(f):
        return None
    import csv
    rows = list(csv.DictReader(io.open(f, encoding='utf-8-sig')))
    d = {}
    for r in rows:
        dt = str(r['date']).replace('-', '')
        d[dt] = r
    return d

def nban(hd):
    if not hd:
        return None
    m = re.findall(r'(\d+)板', hd)
    if m:
        return int(m[-1])
    if '首板' in hd:
        return 1
    return None

bands = [('gap<=-9.5(跌停附近)', -100, -9.5), ('-9.5~-5', -9.5, -5.0), ('-5~0', -5.0, -0.0001),
         ('0~5', 0.0, 5.0), ('>=5', 5.0, 100.0)]

def band_of(g):
    for nm, lo, hi in bands:
        if lo <= g <= hi:
            return nm
    if g == 0.0:
        return '0~5'
    return None

cache = {}
res = collections.defaultdict(list)   # (连板组, band) -> list of r
raw = []
days = sorted(ths.keys())
for d in days:
    for t in ths[d]:
        c = t['code']
        nb = nban(t.get('high_days'))
        if nb is None:
            continue
        if c not in cache:
            cache[c] = bars(c)
        b = cache[c]
        if not b or d not in b:
            continue
        idx = sorted(b.keys())
        i = idx.index(d)
        if i + 1 >= len(idx):
            continue
        d1 = idx[i + 1]
        try:
            c0 = float(b[d]['close']); o1 = float(b[d1]['open']); c1 = float(b[d1]['close'])
        except Exception:
            continue
        if c0 <= 0 or o1 <= 0:
            continue
        gap = (o1 / c0 - 1) * 100
        r = (c1 / o1 - 1) * 100
        grp = '1板' if nb <= 1 else ('2板' if nb == 2 else '3板+')
        res[(grp, band_of(gap))].append(r)
        if grp == '3板+' and gap <= -9.5:
            raw.append((d, d1, c, t.get('name'), t.get('high_days'), round(c0, 2), round(o1, 2), round(c1, 2), round(gap, 2), round(r, 2)))

print('=== 重建分桶(全样本, 未加首封/ST过滤) 执行=T+1开→T+1收 (%) ===')
for grp in ['3板+', '2板', '1板']:
    for nm, _, _ in bands:
        v = res.get((grp, nm), [])
        if len(v) >= 1:
            win = sum(1 for x in v if x > 0) / len(v) * 100
            print('%-5s %-16s n=%-5d 胜率=%.1f%% 均收=%+.2f%% 中位=%+.2f%%' % (grp, nm, len(v), win, statistics.mean(v), statistics.median(v)))
    print()
print('=== 3板+ 且 gap<=-9.5% 逐例 ===')
print('n=', len(raw))
for x in raw:
    print(x)
