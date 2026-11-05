# -*- coding: utf-8 -*-
"""尾盘封票次日竞价 gap 分布建模（MA-20261104-02 ①）
样本源: 市场数据/2026*/zt_pool.csv（含首封时间/流通市值/连板）
收益源: _学习/_bars_cache/{code}.csv（T收→T+1开=T1高开/T+1开→T+1收=执1）
零后视镜: 只用 <=20261105 的盘后数据; gap 是 T+1 09:25 已知量, 只作闸门
"""
import csv, json, glob, os, statistics
from pathlib import Path

ROOT = Path(r'D:\股票数据\市场数据')
BARS = ROOT / '_学习' / '_bars_cache'

# 读 bars 到内存: code -> {date: (open, close)}
bars = {}
for fp in BARS.glob('*.csv'):
    code = fp.stem
    d = {}
    try:
        with open(fp, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                try:
                    d[r['date']] = (float(r['open']), float(r['close']))
                except (ValueError, KeyError, TypeError):
                    pass
    except Exception:
        continue
    if d:
        bars[code] = (sorted(d.keys()), d)

days = sorted([p.name for p in ROOT.glob('2026*') if p.is_dir() and (p / 'zt_pool.csv').exists()])
print('池日数', len(days), days[0], '~', days[-1])

rows = []
missing = 0
for day in days:
    try:
        with open(ROOT / day / 'zt_pool.csv', encoding='utf-8-sig') as f:
            zt = list(csv.DictReader(f))
    except Exception:
        continue
    for r in zt:
        code = r['代码'].strip()
        ft = (r.get('首次封板时间') or '').strip()
        if len(ft) != 6:
            continue
        hh, mm = int(ft[:2]), int(ft[2:4])
        if hh < 13:
            continue  # 只建模尾盘封
        seg = '13:00-14:00' if hh < 14 else '>=14:00'
        try:
            circ = float(r['流通市值']) / 1e8
            lb = int(float(r['连板数']))
            fb = float(r['封板资金']) / float(r['流通市值']) * 100
            zb = int(float(r['炸板次数']))
        except (ValueError, KeyError):
            continue
        b = bars.get(code)
        if not b:
            missing += 1
            continue
        dates, dd = b
        iso = '%s-%s-%s' % (day[:4], day[4:6], day[6:])
        if iso not in dd:
            missing += 1
            continue
        i = dates.index(iso)
        if i + 1 >= len(dates):
            missing += 1
            continue
        d1 = dates[i + 1]
        t_close = dd[iso][1]
        o1, c1 = dd[d1]
        if t_close <= 0 or o1 <= 0:
            missing += 1
            continue
        rows.append(dict(day=day, code=code, name=r['名称'], seg=seg, circ=circ,
                         lb=lb, fb=fb, zb=zb,
                         gap=round((o1 / t_close - 1) * 100, 2),
                         exec1=round((c1 / o1 - 1) * 100, 2)))

print('尾盘封样本 n=%d, 缺bars=%d, 覆盖率=%.1f%%' % (len(rows), missing,
      100.0 * len(rows) / max(1, len(rows) + missing)))

def q(v, p):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * p
    f = int(k)
    c = min(f + 1, len(v) - 1)
    return round(v[f] + (v[c] - v[f]) * (k - f), 2)

def stat(sub, label):
    if not sub:
        print('%-28s n=0' % label)
        return None
    g = [x['gap'] for x in sub]
    e = [x['exec1'] for x in sub]
    inA = [x for x in sub if -3.0 <= x['gap'] <= 1.5]
    inB = [x for x in sub if -10.0 <= x['gap'] <= 4.9]
    out = dict(label=label, n=len(sub),
               gap_med=q(g, .5), gap_p10=q(g, .1), gap_p25=q(g, .25),
               gap_p75=q(g, .75), gap_p90=q(g, .9),
               gap_mean=round(sum(g) / len(g), 2),
               ge5=round(100.0 * sum(1 for x in g if x >= 5) / len(g), 1),
               le0=round(100.0 * sum(1 for x in g if x <= 0) / len(g), 1),
               mean_exec=round(sum(e) / len(e), 2),
               win=round(100.0 * sum(1 for x in e if x > 0) / len(e), 1),
               gateA_n=len(inA), gateA_trig=round(100.0 * len(inA) / len(g), 1),
               gateA_exec=(round(sum(x['exec1'] for x in inA) / len(inA), 2) if inA else None),
               gateA_win=(round(100.0 * sum(1 for x in inA if x['exec1'] > 0) / len(inA), 1) if inA else None),
               gateB_n=len(inB), gateB_trig=round(100.0 * len(inB) / len(g), 1),
               gateB_exec=(round(sum(x['exec1'] for x in inB) / len(inB), 2) if inB else None),
               gateB_win=(round(100.0 * sum(1 for x in inB if x['exec1'] > 0) / len(inB), 1) if inB else None))
    print('%-28s n=%4d gap中位%6.2f [p10 %6.2f p90 %6.2f] 均%6.2f | ≥5%%: %4.1f%% | 执1均%6.2f 胜%5.1f%% | A门 %d(%.0f%%) 执1 %s 胜%s | B门 %d(%.0f%%) 执1 %s'
          % (label, out['n'], out['gap_med'], out['gap_p10'], out['gap_p90'], out['gap_mean'],
             out['ge5'], out['mean_exec'], out['win'],
             out['gateA_n'], out['gateA_trig'], out['gateA_exec'], out['gateA_win'],
             out['gateB_n'], out['gateB_trig'], out['gateB_exec']))
    return out

res = {'窗口': '%s~%s' % (days[0], days[-1]), '池日数': len(days),
       '样本': len(rows), '缺bars': missing,
       'bars覆盖率pct': round(100.0 * len(rows) / max(1, len(rows) + missing), 1),
       '口径': '尾盘封=当日zt_pool首封>=13:00; gap=T+1开/T收-1; 执1=T+1开->T+1收; 零后视镜(T+1 09:25 gap已知)',
       '总': stat(rows, '全部尾盘封'),
       '按时段': {}, '按市值': {}, '按连板': {}, '交叉': {}}
for s in ['13:00-14:00', '>=14:00']:
    res['按时段'][s] = stat([x for x in rows if x['seg'] == s], s)
for s, f in [('流通>=100亿', lambda x: x['circ'] >= 100), ('流通<100亿', lambda x: x['circ'] < 100)]:
    res['按市值'][s] = stat([x for x in rows if f(x)], s)
for s, f in [('首板', lambda x: x['lb'] == 1), ('2板', lambda x: x['lb'] == 2), ('3板+', lambda x: x['lb'] >= 3)]:
    res['按连板'][s] = stat([x for x in rows if f(x)], s)

print('\n=== 交叉 时段×市值 ===')
for seg in ['13:00-14:00', '>=14:00']:
    for mv, f in [('≥100亿', lambda x: x['circ'] >= 100), ('<100亿', lambda x: x['circ'] < 100)]:
        k = '%s|%s' % (seg, mv)
        res['交叉'][k] = stat([x for x in rows if x['seg'] == seg and f(x)], k)

print('\n=== 交叉 时段×连板 ===')
for seg in ['13:00-14:00', '>=14:00']:
    for lb, f in [('首板', lambda x: x['lb'] == 1), ('2板', lambda x: x['lb'] == 2), ('3板+', lambda x: x['lb'] >= 3)]:
        k = '%s|%s' % (seg, lb)
        res['交叉'][k] = stat([x for x in rows if x['seg'] == seg and f(x)], k)

print('\n=== 按日 尾盘封占比 & 池覆盖率 ===')
daily = []
for day in days:
    try:
        with open(ROOT / day / 'zt_pool.csv', encoding='utf-8-sig') as f:
            zt = list(csv.DictReader(f))
    except Exception:
        continue
    if not zt:
        continue
    late = sum(1 for r in zt if (r.get('首次封板时间') or '') >= '130000' and len((r.get('首次封板时间') or '')) == 6)
    early = sum(1 for r in zt if (r.get('首次封板时间') or '') and (r.get('首次封板时间') or '') <= '093100')
    daily.append(dict(day=day, zt=len(zt), late=late, late_pct=round(100.0 * late / len(zt), 1),
                      early=early, pool_cov=round(100.0 * early / len(zt), 1)))
print('  尾盘封占比 中位 %.1f%% 均值 %.1f%% | 早盘池覆盖率 中位 %.1f%% 均值 %.1f%%'
      % (statistics.median([d['late_pct'] for d in daily]),
         sum(d['late_pct'] for d in daily) / len(daily),
         statistics.median([d['pool_cov'] for d in daily]),
         sum(d['pool_cov'] for d in daily) / len(daily)))
res['日度'] = dict(尾盘占比中位=round(statistics.median([d['late_pct'] for d in daily]), 1),
                  尾盘占比均值=round(sum(d['late_pct'] for d in daily) / len(daily), 1),
                  池覆盖率中位=round(statistics.median([d['pool_cov'] for d in daily]), 1),
                  池覆盖率均值=round(sum(d['pool_cov'] for d in daily) / len(daily), 1),
                  尾盘占比gte50天数=sum(1 for d in daily if d['late_pct'] >= 50),
                  日数=len(daily))
print('\n=== 交叉 市值×连板 (全时段) ===')
for mv, f in [('≥100亿', lambda x: x['circ'] >= 100), ('<100亿', lambda x: x['circ'] < 100)]:
    for lb, g in [('首板', lambda x: x['lb'] == 1), ('2板', lambda x: x['lb'] == 2), ('3板+', lambda x: x['lb'] >= 3)]:
        k = '%s|%s' % (mv, lb)
        res['交叉'][k] = stat([x for x in rows if f(x) and g(x)], k)

out = ROOT / '_学习' / 'auction_尾盘封gap建模_20261105.json'
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n写入', out)
