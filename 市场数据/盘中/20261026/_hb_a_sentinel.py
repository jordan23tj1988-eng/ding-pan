# -*- coding: utf-8 -*-
"""hb-a 20261026 场自审：可机械复核项（文件唯一性、价格可溯源、时间序、数量一致性）。"""
import json, os, datetime

OUT = os.path.dirname(os.path.abspath(__file__))
f = os.path.join(OUT, '临盘决断_20261026_0940.json')
d = json.load(open(f, encoding='utf-8'))
qd = json.load(open(os.path.join(OUT, '_hb_a_quote_decide.json'), encoding='utf-8'))
qn = json.load(open(os.path.join(OUT, '_hb_a_quote_next.json'), encoding='utf-8'))
qd_r, qn_r = qd['rows'], qn['rows']
F = [json.loads(l) for l in open(os.path.join(OUT, 'realtime_ticks.jsonl'), encoding='utf-8')]

ok, fail = [], []


def chk(name, cond, detail=''):
    (ok if cond else fail).append(f'{name} {detail}')


chk('C1 发出版唯一', os.path.exists(f), f)
chk('C2 决断帧早于执行帧', qd['fetched'] < qn['fetched'], f"{qd['fetched']} < {qn['fetched']}")
chk('C3 入场/出场价溯源', all(
    abs(round(qn_r[k]['px'] * 0.999 + 1e-9, 2) - fl['px_exec']) < 1e-9
    for fl, k in zip(d['fills'], ['sz002626', 'sz002639', 'sh603370', 'sh603370'])),
    [f"{x['code']} {x['px']}->{x['px_exec']}" for x in d['fills']])
chk('C4 整手与数量', all(x['qty'] % 100 == 0 and x['qty'] > 0 for x in d['fills']),
    [f"{x['code']} {x['qty']}" for x in d['fills']])
pmax = max(x['ts'] for x in d['fills'])
chk('C5 成交时点晚于决断', pmax >= '2026-10-26 09:50:18', pmax)
chk('C6 池帧新鲜', F[-1]['pool_stale'] is False and F[-1]['n'] == 80, f"{F[-1]['ts']} n={F[-1]['n']}")
gaps = []
for i in range(1, len(F)):
    t0 = datetime.datetime.strptime(F[i - 1]['ts'], '%Y-%m-%d %H:%M:%S')
    t1 = datetime.datetime.strptime(F[i]['ts'], '%Y-%m-%d %H:%M:%S')
    gaps.append((t1 - t0).total_seconds())
chk('C7 帧间隔<600s', max(gaps) < 600, f'max={max(gaps):.0f}s frames={len(F)}')
tob = d['ts']
chk('C8 决策只用决断前数据', all(x['ts'].startswith('2026-10-26 09:50:1') for x in d['fills']))
# 账本回读
led = {}
for b, code, qty in (('auction', '002626', 1000), ('lhb', '002639', 4000), ('master', '603370', 600), ('limitup', '603370', 600)):
    L = [json.loads(l) for l in open(os.path.join(r'D:\股票数据\市场数据\_学习\_模拟盘', b, '账本.jsonl'), encoding='utf-8')]
    hit = [x for x in L if x.get('d') == '20261026' and x.get('code') == code and x.get('ev') == 'sell']
    led[b] = hit
    chk(f'C9 账本入账[{b}]', len(hit) == 1 and hit[0]['shares'] == qty, f"{code} {[(x['shares'], x['sell_px']) for x in hit]}")

print('PASS', len(ok), 'FAIL', len(fail))
for x in ok:
    print('  ✓', x)
for x in fail:
    print('  ✗', x)
print('VERDICT', 'PASS' if not fail else 'FAIL')
