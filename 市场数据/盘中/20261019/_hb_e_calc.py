# -*- coding: utf-8 -*-
"""hb-e 20261019 14:30 尾盘前哨: 取数+机械核对(只算不判)"""
import json, os, csv, time, urllib.request, statistics

D = r"D:\股票数据\市场数据\盘中\20261019"
BAR = r"D:\股票数据\市场数据\_学习\_bars_cache"

def qq(codes):
    q = ",".join(("sh" if c[0] == '6' else "sz") + c for c in codes)
    req = urllib.request.Request("http://qt.gtimg.cn/q=" + q, headers={'User-Agent': 'Mozilla/5.0'})
    raw = urllib.request.urlopen(req, timeout=15).read().decode('gbk', 'ignore')
    out, ts = {}, None
    for seg in raw.split(';'):
        seg = seg.strip()
        if not seg or '="' not in seg:
            continue
        body = seg.split('="', 1)[1].rstrip('"')
        f = body.split('~')
        if len(f) < 33:
            continue
        out[f[2]] = dict(code=f[2], name=f[1], latest=float(f[3]), preClose=float(f[4]), open=float(f[5]),
                        high=float(f[33]) if len(f) > 33 else None, low=float(f[34]) if len(f) > 34 else None,
                        pct=float(f[32]), vol=float(f[6]), amt_wan=float(f[37]) if len(f) > 37 else None,
                        tick=f[30])
        ts = f[30]
    return out, ts, raw

def ma(code, n):
    rows = list(csv.reader(open(os.path.join(BAR, code + ".csv"), encoding='utf-8')))
    rows = [r for r in rows if len(r) > 4 and r[4] and r[4][0].isdigit()]
    closes = [float(r[4]) for r in rows]
    return round(sum(closes[-n:]) / n, 3), len(closes), rows[-1][0]

CODES = ['600668', '000601', '000823', '600802', '300045']
res = dict(fetch_at=time.strftime('%Y-%m-%d %H:%M:%S'), quotes={}, raw_len=0)
try:
    quotes, ts, raw = qq(CODES)
    res['quotes'] = quotes
    res['raw_len'] = len(raw)
    res['src_tick'] = ts
except Exception as e:
    res['err'] = str(e)

lines = [l for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
frames = [json.loads(l) for l in lines]
last = frames[-1]
rows = last['rows']
pcts = [r['pct'] for r in rows]
seal = [r for r in rows if r['pct'] >= 9.7]
zha = [r for r in rows if r['high'] >= r['preClose'] * 1.095 - 1e-9 and r['latest'] < r['preClose'] * 1.095 - 1e-9]
res['pool'] = dict(ts=last['ts'], n=last['n'], pool_date=last['pool_date'],
                   seal=len(seal), zha=len(zha),
                   median=round(statistics.median(pcts), 2), mean=round(statistics.mean(pcts), 2),
                   up=sum(1 for p in pcts if p > 0), dn=sum(1 for p in pcts if p < 0),
                   low=min(pcts), high=max(pcts),
                   dn5=sum(1 for p in pcts if p <= -5), dn8=sum(1 for p in pcts if p <= -8),
                   seal_names=sorted([(r['code'], r['name'], r['pct']) for r in seal], key=lambda x: -x[2]),
                   fresh_sec=round((time.time() - os.path.getmtime(os.path.join(D, 'realtime_ticks.jsonl'))), 1))

# 帧龄
import datetime
last_dt = datetime.datetime.strptime(last['ts'], '%Y-%m-%d %H:%M:%S')
res['pool']['frame_lag_sec'] = round((datetime.datetime.now() - last_dt).total_seconds(), 1)

res['ma'] = {}
for c, n in [('000601', 10), ('000823', 20), ('600668', 10), ('600668', 20)]:
    m, cnt, ld = ma(c, n)
    res['ma'][f'{c}_MA{n}'] = dict(v=m, bars=cnt, last_bar=ld)

# 关键线核对
chk = {}
q = res['quotes']
if '600668' in q:
    x = q['600668']
    chk['600668'] = dict(cost=8.15, px=x['latest'], vs_cost=round((x['latest'] / 8.15 - 1) * 100, 2),
                         pct=x['pct'], low=x['low'], high=x['high'], open=x['open'], pre=x['preClose'],
                         dt_px=round(x['preClose'] * 0.9, 2),
                         dist_to_dt=round((x['latest'] / (x['preClose'] * 0.9) - 1) * 100, 2),
                         below_815=x['latest'] < 8.15)
if '000601' in q:
    x = q['000601']
    chk['000601'] = dict(cost=6.68, px=x['latest'], vs_cost=round((x['latest'] / 6.68 - 1) * 100, 2),
                         pct=x['pct'], low=x['low'], ma10=res['ma']['000601_MA10']['v'], line_645=6.45,
                         break_ma10=x['latest'] < res['ma']['000601_MA10']['v'], break_645=x['latest'] < 6.45)
if '000823' in q:
    x = q['000823']
    chk['000823'] = dict(cost=25.13, px=x['latest'], vs_cost=round((x['latest'] / 25.13 - 1) * 100, 2),
                         pct=x['pct'], low=x['low'], ma20=res['ma']['000823_MA20']['v'],
                         break_ma20=x['latest'] < res['ma']['000823_MA20']['v'])
res['checks'] = chk

json.dump(res, open(os.path.join(D, '_hb_e_calc.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1)[:6000])
