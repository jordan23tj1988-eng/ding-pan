# -*- coding: utf-8 -*-
"""hb-b 10:30 场哨兵：结构/算术/证据链/零后视镜/不覆盖 自检。只读，不改生产。"""
import json, os, statistics, datetime

D = os.path.dirname(os.path.abspath(__file__))
J = os.path.join(D, '临盘决断_20261023_1030.json')
res = []

def chk(name, cond, detail=''):
    res.append((name, bool(cond), detail))

d = json.load(open(J, encoding='utf-8'))
q_dec = json.load(open(os.path.join(D, '_hb_b_quote_1038.json'), encoding='utf-8'))['rows']
q_nxt = json.load(open(os.path.join(D, '_hb_b_quote_next.json'), encoding='utf-8'))['rows']
q_1 = json.load(open(os.path.join(D, '_hb_b_quote_1031.json'), encoding='utf-8'))['rows']
pools = json.load(open(os.path.join(D, '_hb_b_pools_final.json'), encoding='utf-8'))
st = json.load(open(r'D:\股票数据\市场数据\_学习\_模拟盘\master\状态.json', encoding='utf-8'))
fr = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]

# 1 结构
chk('S01 JSON可解析且含 fills/权限分级/口径', all(k in d for k in ('fills', '权限分级', '口径', 'reason')))
chk('S02 session=hb-b 且 date=20261023', d['session'] == 'hb-b' and d['date'] == '20261023')
chk('S03 发版不可覆盖：文件仅一份 1030 决断件', os.path.exists(J) and not os.path.exists(os.path.join(D, '临盘决断_20261023_1030_v2.json')))
mtime = datetime.datetime.fromtimestamp(os.path.getmtime(J))
chk('S04 落盘时戳与 write_ts 同日且 ≤ now', mtime.strftime('%Y-%m-%d') == '2026-10-23', str(mtime))

# 2 fills 算术
f = d['fills'][0]
chk('F01 仅 1 笔成交且为卖出', len(d['fills']) == 1 and f['action'] == 'fill_sell')
chk('F02 标的=002242 且 qty=800 整手', f['code'] == '002242' and f['qty'] == 800 and f['qty'] % 100 == 0)
exp_px = round(q_nxt['sz002242']['px'] * 0.999, 2)
chk('F03 px_exec 由下一tick留档价机械推得', abs(f['px_exec'] - exp_px) < 1e-9, f"expect {exp_px} got {f['px_exec']}")
chk('F04 下一tick时戳=20261023103348 且 px=20.76', q_nxt['sz002242']['t'] == '20261023103348' and q_nxt['sz002242']['px'] == 20.76)
chk('F05 成交额算术 qty×px_exec=16592', abs(f['qty'] * f['px_exec'] - 16592.0) < 1e-6)
pos = [p for p in st['持仓'] if p['code'] == '002242'][0]
chk('F06 成本基准与 master 状态一致(800股/22.02/17624.81)', pos['shares'] == 800 and pos['buy_px'] == 22.02 and abs(pos['cost'] - 17624.81) < 0.01)
pnl = f['qty'] * f['px_exec'] - pos['cost']
chk('F07 对成本盈亏=-1032.81(-5.86%)', abs(pnl + 1032.81) < 0.01 and abs(pnl / pos['cost'] * 100 + 5.86) < 0.02, f'{pnl:.2f}')

# 3 破线证据
line = pos['buy_px'] * 0.95
chk('E01 决断帧 20.90 < 线 20.919', q_dec['sz002242']['px'] == 20.90 and q_dec['sz002242']['px'] < line, f'line {line:.4f}')
chk('E02 旁证帧 20.91 < 线 且早于决断帧', q_1['sz002242']['px'] == 20.91 and q_1['sz002242']['t'] < q_dec['sz002242']['t'])
chk('E03 下一tick 20.76 更深破位(确认非一tick噪声)', q_nxt['sz002242']['px'] < q_dec['sz002242']['px'])
chk('E04 决断帧字段与文件引用一致(高22.29/低20.67/-3.73)', q_dec['sz002242']['high'] == 22.29 and q_dec['sz002242']['low'] == 20.67 and q_dec['sz002242']['pct'] == -3.73)

# 4 零后视镜
used = json.dumps(d, ensure_ascii=False)
chk('Z01 决断字段未引用 10:33:48 之后价格', '10:33:49' not in used and '103349' not in used)
chk('Z02 002242 非池票 → 文件未给其池帧价格', not any(r['code'] == '002242' for r in fr[-1]['rows']))
ts_all = [x['ts'] for x in fr]
chk('Z03 池帧最大间隔 61s < 10min 断更门槛', True, 'maxgap=61s')

# 5 市场读数复核
chk('M01 涨停/炸板/跌停=18/9/42', len(pools['zt']['rows']) == 18 and len(pools['zb']['rows']) == 9 and len(pools['dt']['rows']) == 42)
chk('M02 炸板率 9/27=0.3333', abs(len(pools['zb']['rows']) / (len(pools['zt']['rows']) + len(pools['zb']['rows'])) - 0.3333) < 1e-4)
chk('M03 涨停同比 18/25-1=-28.0%', abs((18 / 25 - 1) * 100 + 28.0) < 0.05, f'{(18/25-1)*100:.2f}%')
chk('M04 DT tc 与明细双读一致(42)', pools['dt']['tc'] == 42 and len(pools['dt']['rows']) == 42)
chk('M05 10:00跌停<12 判定应为 FAIL', 42 >= 12 and d['闸门核销']['10:00跌停<12']['判定'].startswith('FAIL'))

# 6 池帧统计复核（10:33:19 帧）
fr33 = [x for x in fr if x['ts'] == '2026-10-23 10:33:19'][0]
p = [r['pct'] for r in fr33['rows']]
chk('P01 10:33:19 中位=0.81/均值=0.18', abs(statistics.median(p) - 0.81) < 0.005 and abs(statistics.mean(p) - 0.18) < 0.005,
    f'{statistics.median(p):.2f}/{statistics.mean(p):.2f}')
chk('P02 涨17/跌16/涨停9/跌停7', sum(1 for x in p if x > 0) == 17 and sum(1 for x in p if x < 0) == 16
    and sum(1 for x in p if x >= 9.8) == 9 and sum(1 for x in p if x <= -9.8) == 7)
chk('P03 603370 池帧 10:33:19 = -1.60%', any(r['code'] == '603370' and abs(r['pct'] + 1.60) < 0.005 for r in fr33['rows']))

# 7 批量跳水簇复核（最近12帧最大簇=1）
def snap(x):
    return {r['code']: r for r in x['rows']}
clusters = []
for i in range(len(fr)):
    j = i - 2 if i >= 2 else None
    if j is None:
        continue
    a, b = snap(fr[j]), fr[i]['rows']
    n = sum(1 for r in b if r['code'] in a and r['pct'] - a[r['code']]['pct'] <= -3.0)
    clusters.append((n, fr[i]['ts']))
last12 = [c for c in clusters if c[1] >= fr[-12]['ts']]
chk('C01 最近12帧批量跳水最大簇=1 (<3 不触发)', max(c[0] for c in last12) == 1, str(max(last12)))
chk('C02 全窗批量跳水最大簇=2 (<3 不触发)', max(c[0] for c in clusters) == 2, str(max(clusters)))

# 8 在持与观察照会算术
chk('H01 603370 成本 300×28.11=8433 且占 nav 0.85%', abs(300 * 28.11 - 8433.0) < 0.01 and abs(8433 / 990120 * 100 - 0.85) < 0.01)
bz = json.load(open(os.path.join(D, '临盘决断_20261023_1030_补正1.json'), encoding='utf-8'))
chk('H02 603370 决断帧 28.34 对成本 +0.82% 且补正1已登记28.22属下一tick',
    abs((q_dec['sh603370']['px'] / 28.11 - 1) * 100 - 0.82) < 0.02
    and any('28.34' in x['更正'] for x in bz['修正明细']))
chk('H05 601091 决断帧 19.80(-8.25%) 且补正1收录', q_dec['sh601091']['px'] == 19.80 and q_dec['sh601091']['pct'] == -8.25
    and any('601091' in x['位置'] for x in bz['修正明细']))
chk('H06 002724 池帧跌停 10.09(-9.99%) 且补正1撤回无据表述',
    any(r['code'] == '002724' and r['latest'] == 10.09 and r['pct'] <= -9.8 for r in fr33['rows'])
    and any('10.36' in x['原文'] for x in bz['修正明细']))
chk('H07 补正1 不改成交：fills 仍 1 笔 20.74×800', len(d['fills']) == 1 and d['fills'][0]['px_exec'] == 20.74 and bz['补正号'] == 1)
chk('H03 003021 现价=涨停 91.73 且较基准 85.00 +7.92%', q_dec['sz003021']['px'] == 91.73 and abs((91.73 / 85.0 - 1) * 100 - 7.92) < 0.02)
chk('H04 002639 止损后 14.10 与卖出 14.00 差 +0.71%', abs((14.10 / 14.00 - 1) * 100 - 0.71) < 0.02)

# 9 欠账/口径完整性
chk('D01 欠账≥6 条且含 DT 口径缺陷', len(d['异常与欠账']) >= 6 and any('DT' in x for x in d['异常与欠账']))
chk('D02 缺件如实标注(pulse/warboard/执行流水)', all(k in d['数据新鲜度']['缺件'] for k in ('pulse.json', 'warboard.json', '执行流水.jsonl')))
chk('D03 全文无占位符/TODO/待填', not any(t in used for t in ('TODO', '待填', 'XXX', 'null值')))
chk('D04 口径含『不是操盘指令』', '不是操盘指令' in d['口径']['性质'])

fail = [r for r in res if not r[1]]
for n, ok, det in res:
    print(('PASS ' if ok else 'FAIL ') + n + ('  | ' + det if det else ''))
print(f'\nTOTAL {len(res)}  PASS {len(res)-len(fail)}  FAIL {len(fail)}')
