# -*- coding: utf-8 -*-
"""hb-f 14:45 入账：master 账本 append sell(002639 2600股) + state.json 同步（先备份，写后复算校验）。"""
import json, os, shutil, datetime, hashlib

B = r'D:\股票数据\市场数据\_学习\_模拟盘\master'
D = os.path.dirname(os.path.abspath(__file__))
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

for fn in ('账本.jsonl', 'state.json'):
    src = os.path.join(B, fn)
    shutil.copy2(src, src + '.bak_hbf_20261026')
    print('backup', fn, os.path.getsize(src + '.bak_hbf_20261026'))

st = json.load(open(os.path.join(B, 'state.json'), encoding='utf-8'))
pos = [p for p in st['positions'] if p['code'] == '002639']
assert len(pos) == 1, pos
p0 = pos[0]
SELL_PX, QTY = 13.57, 2600
assert p0['shares'] == QTY and abs(p0['cost'] - 38447.21) < 0.01, p0

proceeds = round(SELL_PX * QTY, 2)
pnl = round(proceeds - p0['cost'], 2)
ret = round(pnl / p0['cost'] * 100, 2)

row = {
 "ev": "sell", "d": "20261026", "code": "002639", "name": "雪人集团",
 "shares": QTY, "plan_date": "20261021", "buy_date": "20261022",
 "buy_px": 14.78, "sell_date": "20261026", "sell_px": SELL_PX,
 "leg": "hb_f_master_catchup_open", "hold_days": 2, "defers": 1, "switched": False,
 "pnl": pnl, "ret_pct": ret,
 "reason": "hb-f 14:45 尾盘深场B：_学习/交易计划_master_20261023.json#sells[1] leg=open『在持仓 002639 表态=开盘平出、一笔不留』的 master 腿（2600股）漏执行 3 个交易日后补执行（09:40 场只覆盖 lhb 账 4000 股 @13.70）｜证据 临盘决断_20261026_1445.json#fills[0]",
 "pnl_note": "毛差(未扣费)，成交价=决断后下一tick留档价13.58×(1-0.10%)=13.57",
 "fill_at": "2026-10-26 14:48:12", "fill_cls": "A",
 "src": "临盘决断_20261026_1445.json", "ts": now,
}
with open(os.path.join(B, '账本.jsonl'), 'a', encoding='utf-8') as f:
    f.write(json.dumps(row, ensure_ascii=False) + '\n')

st['cash'] = round(st['cash'] + proceeds, 2)
st['positions'] = [p for p in st['positions'] if p['code'] != '002639']
json.dump(st, open(os.path.join(B, 'state.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

st2 = json.load(open(os.path.join(B, 'state.json'), encoding='utf-8'))
last = json.loads(open(os.path.join(B, '账本.jsonl'), encoding='utf-8').read().strip().split('\n')[-1])
PX = {'002242': 21.59, '003021': 96.20}
mv = round(sum(p['shares'] * PX[p['code']] for p in st2['positions']), 2)
print('cash_after', st2['cash'], 'positions', [(p['code'], p['shares']) for p in st2['positions']],
      'mv', mv, 'nav', round(st2['cash'] + mv, 2))
print('ledger_last', last['code'], last['ev'], last['sell_px'], last['shares'], last['pnl'], last['ret_pct'])
assert last['ev'] == 'sell' and last['code'] == '002639' and st2['cash'] == 960407.64
assert st2['positions'] == [p for p in st2['positions']] and all(p['code'] != '002639' for p in st2['positions'])

sha = hashlib.sha256(open(os.path.join(D, '临盘决断_20261026_1445.json'), 'rb').read()).hexdigest()
audit = {
 "date": "20261026", "session": "hb-f", "kind": "入账登记（审计件，非发出版）", "write_ts": now,
 "来源": "临盘决断_20261026_1445.json#fills（本场唯一发出版，未改动）",
 "发出版sha256": sha,
 "入账动作": "master 账本.jsonl 追加 1 条 sell 行（002639 2600 股 @13.57，含 fill_at/fill_cls/src/hold_days），state.json 同步扣仓加现金；入账前已备份 账本.jsonl.bak_hbf_20261026 / state.json.bak_hbf_20261026",
 "账本现状": {"master": {"rows_20261026": [row], "cash_after": st2['cash'],
                       "positions_after": [(p['code'], p['shares'], p['buy_px']) for p in st2['positions']],
                       "mv_frame": mv, "nav_frame": round(st2['cash'] + mv, 2),
                       "复算": f"925,125.64 + {proceeds:,.2f} = {st2['cash']:,.2f}；持仓 002242 800 + 003021 100，按 14:46:42 决断帧价 21.59 / 96.20 → 市值 {mv:,.2f}"}},
 "未动账本": "auction / limitup / lhb / logic 本场 0 动作、未写入",
 "遗留": [
  "欠账② master 603370 买入价差 8,651.54 元/300 股虚增，须结算复核；本场不追溯改账。",
  "漏执行成本登记：master 002639 按计划『开盘价』应在今开 14.76 出，实际 13.57 → 少收 3,094.00 元（(14.76-13.57)×2600）；根因=20261023 卖单只绑定 lhb 账、master 腿被误标为『待补账』。"
 ],
 "口径": "①本件不产生任何额外撮合数字，全部数值来自发出版 fills；②入库为 append-only，未改写任何历史行；③本文件对用户=参考，不是操盘指令。"
}
p = os.path.join(D, '入账_20261026_1445.json')
json.dump(audit, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('audit written', p, os.path.getsize(p))
print('sha256', sha)
print('漏执行成本', round((14.76 - 13.57) * 2600, 2))
