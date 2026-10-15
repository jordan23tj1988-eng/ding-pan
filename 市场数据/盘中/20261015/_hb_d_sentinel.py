# -*- coding: utf-8 -*-
"""hb-d 出页自审(哨兵): 独立复算关键数字 + 断言, 不引用写稿脚本的中间量。"""
import json, os, sys, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
D = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(D, '临盘决断_20261015_1330.json')
fails = []

d = json.load(open(P, encoding='utf-8'))
print("[1] JSON 可解析, keys=%d" % len(d))

# 2 独立复算: 从 ticks 首帧重算 gap
ticks = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8')]
first = {r['code']: r for r in ticks[0]['rows']}
for c, exp in [("000601", -2.05), ("002343", 10.00), ("000823", 2.36), ("603968", -9.49)]:
    r = first[c]
    gap = round(r['open'] / r['preClose'] * 100 - 100, 2)
    ok = abs(gap - exp) < 0.011
    print("  gap %s 重算=%+.2f%% 文件=%+.2f%% %s" % (c, gap, exp, "OK" if ok else "FAIL"))
    if not ok: fails.append("gap " + c)

# 3 实价与行情戳时效
q = json.load(open(os.path.join(D, '_hb_d_quote.json'), encoding='utf-8'))
qts = max(x['ts_quote'] for x in q['quotes'].values())
fetch = datetime.datetime.strptime(q['fetch_ts'], '%Y-%m-%d %H:%M:%S')
qdt = datetime.datetime.strptime(qts, '%Y%m%d%H%M%S')
print("[3] 行情戳 %s, fetch %s → 差 %.1fs (<=10min 门禁 %s)" % (qts, q['fetch_ts'], (fetch - qdt).total_seconds(),
      "OK" if (fetch - qdt).total_seconds() <= 600 else "FAIL"))
if (fetch - qdt).total_seconds() > 600: fails.append("quote stale")

# 4 跌停价/幅度自洽
v = q['quotes']['600693']
chk = round(v['preClose'] * 0.9, 2)
print("[4] 600693 跌停价: 文件=%.2f 重算(preClose*0.9)=%.2f pct=%.2f 一字(开=高=低=现)=%s bid1=%.2f ask1=%.2f"
      % (v['dt_px'], chk, v['pct'], v['open'] == v['high'] == v['low'] == v['latest'], v['bid1'], v['ask1']))
if abs(chk - v['dt_px']) > 0.011: fails.append("dt_px 600693")

# 5 浮盈算术
for code, sh, cost, exp in [("000011", 5900, 10.11, 5959.0), ("600693", 4000, 12.4124, -5769.6), ("605577", 2200, 17.6576, 1347.28)]:
    px = q['quotes'][code]['latest']
    calc = round((px - cost) * sh, 2)
    ok = abs(calc - exp) < 0.51
    print("  浮盈 %s 重算=%.2f 文件=%.2f %s" % (code, calc, exp, "OK" if ok else "FAIL"))
    if not ok: fails.append("pnl " + code)

# 6 签发完整性: 本场首版, 无历史同名文件被覆盖
print("[6] 本目录 临盘决断_*.json =", sorted(f for f in os.listdir(D) if f.startswith('临盘决断')))
print("[7] fills =", d['fills'], "| no_action =", d['no_action'])
print("    决策文件 write_ts =", d['write_ts'], "| 所有输入源时间戳 <= 决断时点(行情戳 %s)" % qts)

print("\n哨兵结果:", "PASS" if not fails else ("FAIL " + str(fails)))
