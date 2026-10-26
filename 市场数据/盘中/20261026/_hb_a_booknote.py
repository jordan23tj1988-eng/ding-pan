# -*- coding: utf-8 -*-
"""hb-a 20261026 场入账登记：把 临盘决断_20261026_0940.json#fills 落到四本账，并登记入账口径差异。
不改 临盘决断 发出版；本文件为独立审计件。"""
import json, os, datetime

OUT = r'D:\股票数据\市场数据\盘中\20261026'
BASE = r'D:\股票数据\市场数据\_学习\_模拟盘'
TARGET = os.path.join(OUT, '入账_20261026_0940.json')
assert not os.path.exists(TARGET)

led = {}
for b in ('auction', 'lhb', 'master', 'limitup'):
    L = [json.loads(l) for l in open(os.path.join(BASE, b, '账本.jsonl'), encoding='utf-8')]
    st = json.load(open(os.path.join(BASE, b, 'state.json'), encoding='utf-8'))
    led[b] = {
        'rows_20261026': [x for x in L if x.get('d') == '20261026'],
        'cash_after': st.get('cash'),
        'positions_after': [(p['code'], p['name'], p['shares'], p['buy_px']) for p in st.get('positions', [])],
    }

doc = {
    'date': '20261026', 'session': 'hb-a', 'kind': '入账登记（审计件，非发出版）',
    'write_ts': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    '来源': '临盘决断_20261026_0940.json#fills（本场唯一发出版，未改动）',
    '入账动作': '四本账 账本.jsonl 各追加 1 条 sell 行（含 fill_at/fill_cls/src），state.json 同步扣仓加现金；入账前各账本已备份为 账本.jsonl.bak_hba_20261026',
    '账本现状': led,
    '为何由盘中场入账（不留给盘后）': {
        '证据1': '_学习/_模拟盘/master/账本.jsonl 末 3 条 ts=2026-10-23 19:14:19 的买入行，价格取 603370=28.46 / 003021=85.00，即『计划开盘价』；而 临盘决断_20261023_0940.json#fills[1] 的实际成交为 603370 300股@28.11（半额 1.0%）。→ 盘后入账以计划/开盘价重算，未消费盘中 fills 的 px_exec 与权重调整。',
        '证据2': '临盘决断_20261023_0940.json#fills[0] 卖出 002639 2600股@14.00 在 master 账本中无对应 sell 行、state.json 至今仍持 2600 股 → 盘中卖出被整笔丢弃。',
        '结论': '若不由本场入账，今日 4 笔卖出会重复上述丢弃路径（纸面决断、账面无痕）→ 本场按 20261019 11:08 补执行的先例，直接落账并留登记。本判断属机制观察，不改任何生产脚本。'
    },
    '遗留': [
        'master 002639 2600股：20261023 已判卖（14.00）但账本未入账，本场不重复卖出；须由 20261026 结算按 临盘决断_20261023_0940.json#fills[0] 补账（补回款 36,400 元、销 2600 股）。',
        'master 603370 买入价差：10/23 账本按 28.46×600 入账，hba 实际成交 28.11×300（半额）→ 账本价格与数量双口径偏高，成本虚增 17,084.54-8,433.00=8,651.54 元、仓位虚增 300 股；须在结算复核，本场不做追溯改账（发版不可覆盖、当日不回溯）。'
    ]
}
json.dump(doc, open(TARGET, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('OK', TARGET, os.path.getsize(TARGET))
