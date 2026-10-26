# -*- coding: utf-8 -*-
"""hb-e 14:30 入账：logic 账本 append sell + state.json 同步（先备份，写后复算校验）。"""
import json, os, shutil, datetime, hashlib

B = r'D:\股票数据\市场数据\_学习\_模拟盘\logic'
D = os.path.dirname(os.path.abspath(__file__))
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 备份
for fn in ('账本.jsonl', 'state.json'):
    src = os.path.join(B, fn)
    shutil.copy2(src, src + '.bak_hbe_20261026')
    print('backup', fn, os.path.getsize(src + '.bak_hbe_20261026'))

st = json.load(open(os.path.join(B, 'state.json'), encoding='utf-8'))
pos = [p for p in st['positions'] if p['code'] == '600487']
assert len(pos) == 1, pos
p0 = pos[0]
SELL_PX, QTY, FEE = 48.62, 1000, 0.0005

proceeds = round(SELL_PX * QTY, 2)
pnl = round(proceeds - p0['cost'], 2)
ret = round(pnl / p0['cost'] * 100, 2)

row = {
 "ev": "sell", "d": "20261026", "code": "600487", "name": "亨通光电",
 "shares": QTY, "plan_date": p0['plan_date'], "buy_date": p0['buy_date'],
 "buy_px": p0['buy_px'], "sell_date": "20261026", "sell_px": SELL_PX,
 "leg": "hb_e_price_leg_defense", "hold_days": 4, "defers": 0, "switched": False,
 "pnl": pnl, "ret_pct": ret,
 "reason": "hb-e 14:30 场：价格腿硬线触发（决断帧 48.70 < 成本硬线 50.00，依 1030 补正1『不得再顺延』+ 1330『14:30 场硬核 50.00』）→ 清仓；量能腿不引用、不改判｜证据 临盘决断_20261026_1430.json#fills[0]",
 "pnl_note": "毛差(未扣费)，成交价=决断后下一tick留档价48.67×(1-0.10%)=48.62",
 "fill_at": "2026-10-26 14:32:07", "fill_cls": "A",
 "src": "临盘决断_20261026_1430.json", "ts": now,
}
with open(os.path.join(B, '账本.jsonl'), 'a', encoding='utf-8') as f:
    f.write(json.dumps(row, ensure_ascii=False) + '\n')

st['cash'] = round(st['cash'] + proceeds, 2)
st['positions'] = [p for p in st['positions'] if p['code'] != '600487']
json.dump(st, open(os.path.join(B, 'state.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# 写后复算校验
st2 = json.load(open(os.path.join(B, 'state.json'), encoding='utf-8'))
last = json.loads(open(os.path.join(B, '账本.jsonl'), encoding='utf-8').read().strip().split('\n')[-1])
mv = sum(p['shares'] * 48.67 for p in st2['positions'])
print('cash_after', st2['cash'], 'positions', [(p['code'], p['shares']) for p in st2['positions']],
      'mv', round(mv, 2), 'nav', round(st2['cash'] + mv, 2))
print('ledger_last', last['code'], last['ev'], last['sell_px'], last['shares'], last['pnl'], last['ret_pct'])
assert last['ev'] == 'sell' and last['code'] == '600487' and st2['cash'] == 1010775.37 and st2['positions'] == []

sha = hashlib.sha256(open(os.path.join(D, '临盘决断_20261026_1430.json'), 'rb').read()).hexdigest()
audit = {
 "date": "20261026", "session": "hb-e", "kind": "入账登记（审计件，非发出版）",
 "write_ts": now,
 "来源": "临盘决断_20261026_1430.json#fills（本场唯一发出版，未改动）",
 "发出版sha256": sha,
 "入账动作": "logic 账本.jsonl 追加 1 条 sell 行（含 fill_at/fill_cls/src/hold_days），state.json 同步扣仓加现金；入账前已备份 账本.jsonl.bak_hbe_20261026 / state.json.bak_hbe_20261026",
 "账本现状": {
  "logic": {
   "rows_20261026": [row],
   "cash_after": st2['cash'],
   "positions_after": [],
   "nav_after": round(st2['cash'] + mv, 2),
   "复算": f"962155.37 + {proceeds:,.2f} = {st2['cash']:,.2f}；持仓 0，nav=cash"
  }
 },
 "未动账本": "master / auction / limitup / lhb 本场 0 动作、未写入（本场仅 logic 一条价格腿触发）",
 "遗留": [
  "欠账① master 002639 2600 股：20261023 已判卖(14.00)未入账，须结算补账；本场不重复卖出。",
  "欠账② master 603370 买入价差 8,651.54 元/300 股虚增，须结算复核；本场不追溯改账。",
  "欠账③ 600487 hold_days 按交易日计（20261020 买 → 20261026 卖，间隔 20/21/22/23/26 共 4 个交易日），已落账，供结算口径对齐。"
 ],
 "口径": "①本件不产生任何额外撮合数字，全部数值来自发出版 fills；②入库为 append-only，未改写任何历史行；③本文件对用户=参考，不是操盘指令。"
}
p = os.path.join(D, '入账_20261026_1430.json')
json.dump(audit, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('audit written', p, os.path.getsize(p))
print('sha256', sha)
