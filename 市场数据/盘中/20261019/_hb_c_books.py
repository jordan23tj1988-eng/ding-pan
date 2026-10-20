# -*- coding: utf-8 -*-
"""hb-c 20261019 账本/状态/净值 落账 + 605189 补正
三源核账: master/state.json=5只(含600693, 不含605189) + master/账本.jsonl(20261018 reject 605189) + 净值20261016 n=5
→ 账本为准: 605189 未持有 => 本场该笔卖出作废(不落账、不产生现金), 另出补正件。
"""
import json, os

D = '盘中/20261019'
fills = json.load(open(f'{D}/_hb_c_fills_1100.json', encoding='utf-8'))
tick_at = fills['tick_at']
executed = [f for f in fills['fills'] if f['code'] != '605189']
voided = [f for f in fills['fills'] if f['code'] == '605189']
assert len(executed) == 4 and len(voided) == 1

# ---------- 1. 补正件(发出版不可覆盖 → 另立补正, 不改 1100 原件) ----------
amend_path = f'{D}/临盘决断_20261019_1100_补正1_605189作废.json'
assert not os.path.exists(amend_path)
amend = dict(
    date='20261019', session='hb-c', ts='11:00', write_ts=tick_at, type='FILL_VOID',
    补正对象='盘中/20261019/临盘决断_20261019_1100.json#条件决断.卖出 中 code=605189 富春染织 一笔',
    结论='该笔卖出**作废(不执行、不落账)**: 605189 在本系统账本口径下**不属在持**。',
    三源证据=[
        '_学习/_模拟盘/master/state.json#positions = 600693/000601/603968/000823/600668 共5只, 无 605189',
        '_学习/_模拟盘/master/账本.jsonl 末段: {"ev":"reject","d":"20261016","code":"605189","why":"超5只持仓上限(含在持)","ts":"2026-10-18 09:41:50"} → 10/18 回填时已判拒单',
        '_学习/_模拟盘/master/净值.json#20261016 = {nav:1.000622, cash:820099.75, mv:180522, n:5} → 净值口径同样 n=5 无 605189',
    ],
    冲突如实登记=('20261016 09:40 场 fills 确有「买入 605189 1100股 @17.97」(19,767元), playbook 据此按「状态件未回写、按 fills 补入、禁漏票」把 605189 计入在持并给出卖出腿; '
             '但 10/18 回填把该笔判为 reject(超5只上限), 账本/状态/净值三源一致取「不持有」。→ 本场取账本口径: 不卖不落账。'
             '同时暴露 playbook 生成侧一处**换票**: 其 master 在持 5 只被写成「600668/605189/603968/000601/000823」, 而实际 5 只应为「600668/600693/603968/000601/000823」——即 605189 顶替了 600693, 导致 600693(10/16 跌停顺延 defer_sell=true) 在预案中整票缺席。'),
    处置=dict(**{
        '605189': '作废本笔; 待复盘(晚间)按 10/16 fills vs 10/18 reject 二选一定账, 本场不替账本作二次解释、不改 state。',
        '600693': '已按 B 级防守补执行卖出 4000股(见 1100#fills), 理由=defer_sell 未完成 + 相对成本 -27.82%, 证据在 1100 件内。',
        '机制建议': 'playbook 生成器加两条断言: ①state 持仓全量覆盖(每只在 sells 或 watch 必出现) ②fills 补入票必须与 backfill reject 集合无交集。'}),
    本场未改参数='未修改 playbook/闸门/阈值/生产脚本; 仅作成交登记与作废登记。',
)
json.dump(amend, open(amend_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', amend_path)

# ---------- 2. 账本落账 ----------
def append(ledger, rows):
    with open(ledger, 'a', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print('APPEND', ledger, len(rows))

m_rows, p_rows = [], []
for f in executed:
    row = dict(ev='sell', d='20261019', code=f['code'], name=f['name'],
               plan_date='20261016', buy_date=f['buy_date'], buy_px=f['buy_px'],
               sell_date='20261019', sell_px=f['px_exec'], leg=f['leg'], hold_days=None,
               defers=0, weight=None, switched=False, pnl=f['pnl_gross'], ret_pct=f['ret_pct_gross'],
               reason=f['why'] + '｜证据: ' + f['evidence'],
               pnl_note='毛差(未扣费用); 与历史账本费用口径差异见 临盘决断_20261019_1100.json#撮合口径',
               fill_at=f['tick_at'], fill_cls=f['cls'], ts=tick_at)
    (p_rows if f['account'] == 'panzhong' else m_rows).append(row)
append('_学习/_模拟盘/master/账本.jsonl', m_rows)
append('_学习/_模拟盘/盘中作战/账本.jsonl', p_rows)

# ---------- 3. 状态回写 ----------
def load(p): return json.load(open(p, encoding='utf-8'))
def dump(p, d): json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

ms = '_学习/_模拟盘/master/state.json'
st = load(ms)
before_cash = st['cash']; before_n = len(st['positions'])
sold = {f['code']: f for f in executed}
st['positions'] = [p for p in st['positions'] if p['code'] not in sold]
proceeds = round(sum(f['amt'] for f in executed if f['account'] != 'panzhong'), 2)
st['cash'] = round(before_cash + proceeds, 2)
st['closed'] = st.get('closed', [])
for f in executed:
    if f['account'] != 'panzhong':
        st['closed'].append(dict(code=f['code'], name=f['name'], buy_px=f['buy_px'], sell_px=f['px_exec'],
                                 shares=f['shares'], pnl=f['pnl_gross'], ret_pct=f['ret_pct_gross'],
                                 buy_date=f['buy_date'], sell_date='20261019', leg=f['leg']))
dump(ms, st)
print('master cash', before_cash, '->', st['cash'], '| pos', before_n, '->', len(st['positions']),
      [p['code'] for p in st['positions']])

ps = '_学习/_模拟盘/盘中作战/state.json'
pt = load(ps)
pcash = pt['cash']; pn = len(pt['positions'])
pt['positions'] = [p for p in pt['positions'] if p['code'] not in sold]
ppro = round(sum(f['amt'] for f in executed if f['account'] == 'panzhong'), 2)
pt['cash'] = round(pcash + ppro, 2)
dump(ps, pt)
print('panzhong cash', pcash, '->', pt['cash'], '| pos', pn, '->', len(pt['positions']))

# ---------- 4. 净值 ----------
mnav = load('_学习/_模拟盘/master/净值.json')
# 剩余持仓按 11:08 后首帧快照市值
q = load(f'{D}/_hb_c_tick_after_dec.json')['quotes']
mv = 0.0
for p in st['positions']:
    px = q.get(p['code'], {}).get('latest')
    assert px, 'missing latest for ' + p['code']
    mv += px * p['shares']
mnav['20261019'] = dict(nav=round((st['cash'] + mv) / 1000000, 6), cash=st['cash'], mv=round(mv, 1), n=len(st['positions']))
dump('_学习/_模拟盘/master/净值.json', mnav)
print('master nav', mnav['20261019'])

pnav = load('_学习/_模拟盘/盘中作战/净值.json')
pmv = 0.0
for p in pt['positions']:
    px = q.get(p['code'], {}).get('latest')
    assert px, 'missing latest for ' + p['code']
    pmv += px * p['shares']
pnav.update(dict(date='20261019', nav=round(pt['cash'] + pmv, 2), cash=pt['cash'],
                 pos_val=round(pmv, 1), n_pos=len(pt['positions']), mark='11:08后首帧快照'))
dump('_学习/_模拟盘/盘中作战/净值.json', pnav)
print('panzhong nav', pnav)

# ---------- 5. 报警登记 ----------
alarm = dict(
    ts=tick_at, session='hb-c_1100', level='ALARM', type='intraday_chain_broken_plus_catchup_executed',
    scope='intraday_chain',
    detail=('①执行层断链(主): 09:40 hb-a executions.status=unknown(Scheduler restarted, 09:46:09) + 10:30 hb-b failed(GatewayUnavailableError: Gateway draining: update_paused) '
            '→ 09:25 开盘腿(002860/605189/603968)+000011 gap失效腿 全部漏执行, 今日无 0940/1030 决断件、无执行流水.jsonl。'
            '②本场(11:00 hb-c)机械复核后补执行 4 笔卖单: 002860 2900@17.13 / 603968 2100@12.73 / 000011 5900@11.05 / 600693 4000@8.95(B级, 预案漏票+defer_sell未完成); 合计回笼 177,205 元。'
            '③605189 卖出作废(账本三源判不持有, 见补正1)。'
            '④数据源: iFinD 09:16 保活 rc=-2 登录被拒 → 实时全程腾讯备源, realtime_ticks 59票/分钟至 11:06:34 未断更; pulse/warboard 今日缺件不影响本场决策。'
            '⑤买入腿全空: 300045 gap+7.01% 出带放弃; 600802 入带但受「与600668同持」剔除 → 零新增暴露。'
            '⑥在持余 600668 6100/000601 6000/000823 800; 600668 收盘<8.15 则次一交易日开盘腿清仓。'),
    decision_file=f'{D}/临盘决断_20261019_1100.json',
    amendment_file=amend_path,
    fills=[dict(code=f['code'], name=f['name'], shares=f['shares'], px=f['px_exec'], cls=f['cls']) for f in executed],
    voided=[dict(code=f['code'], name=f['name'], shares=f['shares'], reason='账本判不持有') for f in voided],
)
with open('盘中/报警_20261019.jsonl', 'a', encoding='utf-8') as f:
    f.write(json.dumps(alarm, ensure_ascii=False) + '\n')
print('APPEND 盘中/报警_20261019.jsonl')
