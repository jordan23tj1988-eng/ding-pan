import json, csv, collections, statistics as st

t = json.load(open('_学习/_市场温度表.json', encoding='utf-8'))
dates = [d for d in sorted(t) if d <= '20261027'][-250:]


def pct(key):
    vals = [t[d].get(key) for d in dates]
    vals = [x for x in vals if x is not None]
    v = t['20261027'][key]
    return dict(val=v, pct=round(sum(1 for x in vals if x <= v) / len(vals) * 100, 2),
                n=len(vals), med=round(st.median(vals), 2), mn=min(vals), mx=max(vals))


print('温度', pct('温度'))
print('成交额亿', pct('成交额亿'))
print('封板总额亿', pct('封板总额亿'))
print('近8日:')
for d in sorted(t)[-8:]:
    x = t[d]
    print('  ', d, '温', x['温度'], '额', x['成交额亿'], '涨', x['涨停数'], '跌', x['跌停数'],
          '炸率', x['炸板率'], '最高', x['最高板'], '二板加', x['二板加'], '封总', x['封板总额亿'])


def load(d):
    return list(csv.DictReader(open('%s/zt_pool.csv' % d, encoding='utf-8-sig')))


r27 = load('20261027')
r26 = load('20261026')
print('\ncols:', list(r27[0].keys()))


def lad(rows):
    c = collections.Counter(int(float(r.get('连板数') or 1)) for r in rows)
    return dict(sorted(c.items()))


print('ladder27', lad(r27), 'n', len(r27))
print('ladder26', lad(r26), 'n', len(r26))


def code(r):
    return r.get('代码') or r.get('股票代码') or r.get('code')


c27 = {code(r) for r in r27}


def lv(rows, n):
    return [r for r in rows if int(float(r.get('连板数') or 1)) == n]


for a, b in [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]:
    base = lv(r26, a)
    if not base:
        print('%d进%d: 无样本' % (a, b))
        continue
    hit = [r for r in base if code(r) in c27]
    print('%d进%d: %d/%d = %.3f' % (a, b, len(hit), len(base), len(hit) / len(base)))

allc = {code(r) for r in r26}
alive = [x for x in allc if x in c27]
print('昨停存活', len(alive), '/', len(allc), '=', round(len(alive) / len(allc), 3))

flds = [k for k in r27[0] if ('首封' in k or '流通' in k or '封单' in k or '换手' in k or '炸板' in k)]
print('字段样例:', {k: r27[0][k] for k in flds})
