# -*- coding: utf-8 -*-
"""今日池 gap + 环境档拆解 + 炸板/跌停池 bars 覆盖体检（自算，只读）"""
import csv, json, gzip, statistics
from pathlib import Path

L = Path(r'D:\股票数据\市场数据\_学习')
ROOT = Path(r'D:\股票数据\市场数据')
OUT = {}

# ---------- 1. 今日池 gap ----------
pool = json.load(open(L / '竞价池发出_20261105.json', encoding='utf-8'))['池']
score = {x['代码']: x for x in json.load(open(L / '竞价评分_20261105.json', encoding='utf-8'))['明细']}
snap = {}
with gzip.open(L / '竞价快照存档' / '20261105.csv.gz', 'rt', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        snap[r['代码']] = r

print('=== 今日池 13 只 · 今晨竞价 ===')
tot_amt = 0.0
rows = []
for p in pool:
    s = snap.get(p['代码'], {})
    gap = s.get('高开幅度') or '—'
    amt = float(s['成交额']) if s.get('成交额') else None
    if amt:
        tot_amt += amt
    rows.append(dict(code=p['代码'], name=p['名称'], seg=p['信号'], fb=p['封单比'], zb=p['炸板'],
                     circ=None, gap=gap, rank=s.get('竞价额排名') or '—',
                     amt=(round(amt / 1e8, 3) if amt else None),
                     score=score.get(p['代码'], {}).get('竞价分'),
                     行业=p['行业']))
    print('%s %-6s %-8s 封%5.2f%% 炸%d gap=%6s%% 额=%s亿 排名%s 分%s'
          % (p['代码'], p['名称'], p['信号'], p['封单比'], p['炸板'], gap,
             (round(amt / 1e8, 3) if amt else '—'), s.get('竞价额排名') or '—',
             score.get(p['代码'], {}).get('竞价分')))
gaps = [float(x['gap']) for x in rows if isinstance(x['gap'], str) and x['gap'] not in ('—', '')]
print('池均 gap %.2f%% | ≥+5 只数 %d/%d | gap≤0 只数 %d' % (
    sum(gaps) / len(gaps), sum(1 for g in gaps if g >= 5), len(gaps), sum(1 for g in gaps if g <= 0)))
print('池竞价额合计 %.2f 亿' % (tot_amt / 1e8))
allamt = sum(float(r['成交额']) for r in snap.values() if r.get('成交额'))
print('全市场竞价额 %.1f 亿 | 池占比 %.1f%% | 快照条数 %d' % (
    allamt / 1e8, 100.0 * tot_amt / allamt, len(snap)))
OUT['今日池'] = rows
OUT['池均gap'] = round(sum(gaps) / len(gaps), 2)
OUT['池竞价额亿'] = round(tot_amt / 1e8, 2)
OUT['全市场竞价额亿'] = round(allamt / 1e8, 1)

# ---------- 2. 环境档拆解（63 池日 × 温度表） ----------
prof = json.load(open(L / '子agent增强' / '战绩画像_auction_20261105.json', encoding='utf-8'))
temp = json.load(open(L / '_市场温度表.json', encoding='utf-8'))
days = []
for d in prof['按日']:
    t = temp.get(d['池日'])
    num, den = d['执行胜率'].split('/')
    if d.get('执行均收') is None:
        continue
    days.append(dict(day=d['池日'], n=int(den), win=int(num), ret=d['执行均收'],
                     gain=d.get('增益pp'), zt=(t or {}).get('涨停数'),
                     T=(t or {}).get('温度'), zb=(t or {}).get('炸板率')))

def bucket(d):
    T = d['T']
    if T is None:
        return None
    if T < 25: return '冰点<25'
    if T < 40: return '冷25~40'
    if T < 65: return '中40~65'
    return '热≥65'

def zbucket(z):
    if z is None: return None
    if z < 60: return '涨停<60'
    if z < 90: return '60~89'
    if z < 110: return '90~109'
    return '≥110'

def agg(sub, lab):
    if not sub:
        print('%-22s n=0' % lab); return None
    n = sum(x['n'] for x in sub); w = sum(x['win'] for x in sub)
    r = sum(x['ret'] for x in sub) / len(sub)
    pos = sum(1 for x in sub if x['ret'] > 0)
    o = dict(label=lab, 池日=len(sub), 票=n, 胜率=round(100.0 * w / n, 1),
             池均收=round(r, 2), 正日='%d/%d' % (pos, len(sub)))
    print('%-22s 池日%3d 票%4d 胜率%5.1f%% 池均收%6.2f%% 正日%s' % (lab, o['池日'], n, o['胜率'], r, o['正日']))
    return o

print('\n=== 环境分档（本路 63 个已结算池日 × 温度表） ===')
OUT['环境档'] = {}
for b in ['冰点<25', '冷25~40', '中40~65', '热≥65']:
    OUT['环境档'][b] = agg([d for d in days if bucket(d) == b], b)
print()
OUT['涨停档'] = {}
for b in ['涨停<60', '60~89', '90~109', '≥110']:
    OUT['涨停档'][b] = agg([d for d in days if zbucket(d['zt']) == b], b)
print()
OUT['交叉'] = {}
OUT['交叉']['中档×涨停<90'] = agg([d for d in days if bucket(d) == '中40~65' and d['zt'] and d['zt'] < 90], '中40~65×涨停<90')
OUT['交叉']['中档×涨停≥90'] = agg([d for d in days if bucket(d) == '中40~65' and d['zt'] and d['zt'] >= 90], '中40~65×涨停≥90')
OUT['交叉']['中档×炸板率≥33%'] = agg([d for d in days if bucket(d) == '中40~65' and d['zb'] is not None and d['zb'] >= 0.33], '中40~65×炸≥33%')
OUT['交叉']['中档×炸板率<25%'] = agg([d for d in days if bucket(d) == '中40~65' and d['zb'] is not None and d['zb'] < 0.25], '中40~65×炸<25%')

# 最近 10 个池日
print('\n=== 最近 10 池日 ===')
for d in days[-10:]:
    print('%s T=%s 涨停=%s 池%2d 胜%s 收%6.2f 增益%s' % (d['day'], d['T'], d['zt'], d['n'],
          '%d/%d' % (d['win'], d['n']), d['ret'], d['gain']))
OUT['最近10'] = days[-10:]

# ---------- 3. 炸板/跌停池 bars 覆盖体检 ----------
print('\n=== 炸板/跌停池 bars 覆盖体检（MA-20261104-02 ③） ===')
cov = {}
for day, fname in [('20261104', 'zb_pool.csv'), ('20261105', 'zb_pool.csv')]:
    p = ROOT / day / fname
    if not p.exists():
        print(day, fname, '缺件'); continue
    codes = [r['代码'] for r in csv.DictReader(open(p, encoding='utf-8-sig'))]
    have = sum(1 for c in codes if (L / '_bars_cache' / ('%s.csv' % c)).exists())
    cov['%s_zb' % day] = (len(codes), have, round(100.0 * have / max(1, len(codes)), 1))
    print(day, '炸板池', len(codes), '有K线', have, '覆盖 %.1f%%' % (100.0 * have / len(codes)))

# 跌停池: 从 dfs? 无独立文件, 用 市场温度表 跌停数与 zt_pool 反查不可行 -> 如实标注缺失
for day in ['20261104']:
    p = ROOT / day / 'dt_pool.csv'
    print(day, 'dt_pool.csv 存在:', p.exists())
OUT['bars覆盖'] = cov
json.dump(OUT, open(L / 'auction_自算_20261105.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n写入 auction_自算_20261105.json')
