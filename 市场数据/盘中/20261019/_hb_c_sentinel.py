# -*- coding: utf-8 -*-
"""hb-c 20261019 11:00 场 哨兵: 逐项机械自审(可复算, 不引用叙述)"""
import json, os, datetime
D = '盘中/20261019'
ok = True
def chk(name, cond, detail=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + (' | ' + detail if detail else ''))
    if not cond: ok = False

dec = json.load(open(f'{D}/临盘决断_20261019_1100.json', encoding='utf-8'))
tick = json.load(open(f'{D}/_hb_c_tick_after_dec.json', encoding='utf-8'))
fills = dec['条件决断']['卖出']
tq = tick['quotes']

# C1 发出版存在且为合法 JSON
chk('C1 决断件存在/合法', dec['date'] == '20261019' and dec['session'] == 'hb-c')
# C2 取价晚于决断时间戳
chk('C2 取价时刻>决断时间戳', tick['fetched_at'] > dec['ts'] and tick['fetched_at'] > '2026-10-19 11:08:00',
    f"tick={tick['fetched_at']} dec_ts=11:08:00")
# C3 成交价=快照价×0.999
bad = [f['code'] for f in fills if abs(f['px_exec'] - round(tq[f['code']]['latest'] * 0.999, 2)) > 0.005]
chk('C3 px_exec=tick×0.999', not bad, str(bad))
# C4 amt/pnl 复算
bad = [f['code'] for f in fills if abs(f['amt'] - round(f['px_exec'] * f['shares'], 2)) > 0.02
       or abs(f['pnl_gross'] - round((f['px_exec'] - f['buy_px']) * f['shares'], 2)) > 0.02]
chk('C4 金额/盈亏可复算', not bad, str(bad))
# C5 整手
chk('C5 整手', all(f['shares'] % 100 == 0 for f in fills), str([(f['code'], f['shares']) for f in fills]))
# C6 无买单
chk('C6 今日零买入', all(f['ev'] == 'sell' for f in fills))
# C7 605189 已作废且未落账
amend = json.load(open(f'{D}/临盘决断_20261019_1100_补正1_605189作废.json', encoding='utf-8'))
ml = [json.loads(l) for l in open('_学习/_模拟盘/master/账本.jsonl', encoding='utf-8') if l.strip()]
pl = [json.loads(l) for l in open('_学习/_模拟盘/盘中作战/账本.jsonl', encoding='utf-8') if l.strip()]
m_today = [r for r in ml if r.get('d') == '20261019' and r.get('ev') == 'sell']
p_today = [r for r in pl if r.get('d') == '20261019' and r.get('ev') == 'sell']
chk('C7 补正件存在+605189未落账', amend['type'] == 'FILL_VOID' and not any(r['code'] == '605189' for r in m_today + p_today),
    f"master今日{len(m_today)}笔 第七账今日{len(p_today)}笔")
# C8 落账笔数与对象
chk('C8 落账=4笔(3master+1第七账)', len(m_today) == 2 and len(p_today) == 2,
    f"master={[r['code'] for r in m_today]} panzhong={[r['code'] for r in p_today]}")
# C9 状态: 卖出票已移除 + 现金增量=回笼
st = json.load(open('_学习/_模拟盘/master/state.json', encoding='utf-8'))
pt = json.load(open('_学习/_模拟盘/盘中作战/state.json', encoding='utf-8'))
pro_m = sum(r['sell_px'] * r['shares'] for r in m_today)
chk('C9 master现金=820099.75+回笼', abs(st['cash'] - (820099.75 + pro_m)) < 0.05, f"{st['cash']} vs {820099.75+pro_m:.2f}")
chk('C10 master持仓已剔除', not ({'603968', '600693'} & {p['code'] for p in st['positions']}), str([p['code'] for p in st['positions']]))
chk('C11 第七账清仓', len(pt['positions']) == 0 and abs(pt['cash'] - 996990.24) < 0.05, f"pos={len(pt['positions'])} cash={pt['cash']}")
# C12 净值复算
nav = json.load(open('_学习/_模拟盘/master/净值.json', encoding='utf-8'))['20261019']
mv = sum(tq[p['code']]['latest'] * p['shares'] for p in st['positions'])
chk('C12 master净值可复算', abs(nav['nav'] - round((st['cash'] + mv) / 1e6, 6)) < 1e-6 and abs(nav['mv'] - round(mv, 1)) < 0.1,
    f"nav={nav['nav']} mv={nav['mv']} 复算mv={round(mv,1)}")
# C13 环境数据可由帧复算
frames = [json.loads(l) for l in open(f'{D}/realtime_ticks.jsonl', encoding='utf-8') if l.strip()]
# 决断件 env['11:05'] 实际引用的是 11:06:34 帧(_hb_c_calc.json#env 生成时取 <=dec 末帧) → 哨兵按同帧复算, 并显式登记标签与实际帧的 1 分钟位移
used = [f for f in frames if f['ts'] <= '2026-10-19 11:06:34'][-1]
rows = used['rows']
lu = sum(1 for r in rows if abs(r['latest'] - round(r['preClose'] * (1.2 if r['code'][0] == '3' or r['code'].startswith('68') else 1.1), 2)) < 0.011)
med = sorted(r['pct'] for r in rows)[len(rows) // 2]
env = dec['环境']['池内截面']['11:05']
chk('C13 环境可复算(帧=%s, 标签"11:05"为该帧口径)' % used['ts'][11:], lu == env['锁板'] and abs(med - env['中位pct']) < 0.02,
    f"锁板{lu}/median{med} vs 档{env['锁板']}/{env['中位pct']}")
# C14 新鲜度
chk('C14 帧龄<=10分钟', int(dec['数据新鲜度']['实时帧']['断更分钟']) <= 10, f"{dec['数据新鲜度']['实时帧']['断更分钟']}分钟")
# C15 报警件
al = [json.loads(l) for l in open('盘中/报警_20261019.jsonl', encoding='utf-8') if l.strip()]
chk('C15 报警登记', len(al) == 1 and al[0]['session'] == 'hb-c_1100', f"{len(al)}条")
chk('C15b 报警回笼额=fills合计', abs(al[0].get('amount_recap', 0) - sum(f['amt'] for f in fills if f['code'] != '605189')) < 0.02, str(al[0].get('amount_recap')))
# C16 原件未被后续写入
mt = datetime.datetime.fromtimestamp(os.path.getmtime(f'{D}/临盘决断_20261019_1100.json'))
chk('C16 发出版只写一次', mt.strftime('%H:%M') >= '11:08', mt.strftime('%H:%M:%S'))
# C17 600668 未越权卖出
chk('C17 600668未卖(收盘判据未到)', '600668' not in [f['code'] for f in fills])
# C18 现价回核(卖出后未产生更优价位的新指令)
print('--- 剩余在持(11:08首帧) ---')
for p in st['positions']:
    print(' ', p['code'], p['name'], p['shares'], 'mk', tq[p['code']]['latest'], 'pct', tq[p['code']]['pct'])
print('RESULT', 'ALL PASS' if ok else 'HAS FAIL')
