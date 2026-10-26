# -*- coding: utf-8 -*-
"""hb-a 20261026 场 → 四本账入账（账本 append + state 更新）。只动 master/auction/lhb/limitup 四本，
不动 logic（本场未决断）。入账前备份 .bak_hba_20261026；幂等：已存在同 (ev,d,code,fill_at) 则跳过。"""
import json, os, shutil, datetime

BASE = r'D:\股票数据\市场数据\_学习\_模拟盘'
FILL_AT = '2026-10-26 09:50:18'
SRC = '临盘决断_20261026_0940.json'

BOOKS = {
    'auction': [dict(code='002626', name='金达威', shares=1000, px_exec=18.53, buy_px=18.33, buy_date='20261020',
                     cost=18339.16, plan='_学习/交易计划_master_20261023.json#sells[0] leg=open')],
    'lhb': [dict(code='002639', name='雪人集团', shares=4000, px_exec=13.70, buy_px=14.78, buy_date='20261022',
                 cost=59149.56, plan='_学习/交易计划_master_20261023.json#sells[1] leg=open')],
    'master': [dict(code='603370', name='华新精科', shares=600, px_exec=28.27, buy_px=28.46, buy_date='20261023',
                    cost=17084.54, plan='B级·预案外防守（自身理由：只做当日价差、不留隔夜）')],
    'limitup': [dict(code='603370', name='华新精科', shares=600, px_exec=28.27, buy_px=28.46, buy_date='20261023',
                     cost=17084.54, plan='B级·预案外防守（自身理由：只做当日价差、不留隔夜）')],
}

report = {}
for book, rows in BOOKS.items():
    led = os.path.join(BASE, book, '账本.jsonl')
    stp = os.path.join(BASE, book, 'state.json')
    bak = led + '.bak_hba_20261026'
    if not os.path.exists(bak):
        shutil.copy2(led, bak)
    existing = open(led, encoding='utf-8').read()
    st = json.load(open(stp, encoding='utf-8'))
    pos = st.get('positions', [])
    cash = float(st.get('cash', 0))
    done = []
    for r in rows:
        key_code = r['code']
        p = next((x for x in pos if x['code'] == key_code), None)
        if p is None:
            report.setdefault(book, []).append(f'{key_code} 无持仓，跳过')
            continue
        if p['shares'] < r['shares']:
            report.setdefault(book, []).append(f'{key_code} 持仓 {p["shares"]} < 卖出 {r["shares"]}，跳过')
            continue
        # 幂等检查
        probe = f'"ev": "sell", "d": "20261026", "code": "{key_code}"'
        if probe in existing:
            report.setdefault(book, []).append(f'{key_code} 已入账，跳过')
            continue
        proceeds = round(r['px_exec'] * r['shares'], 2)
        pnl = round(proceeds - (r['cost'] / (p['shares'] or 1)) * r['shares'], 2)
        row = {
            'ev': 'sell', 'd': '20261026', 'code': key_code, 'name': r['name'], 'shares': r['shares'],
            'plan_date': r['buy_date'], 'buy_date': r['buy_date'], 'buy_px': r['buy_px'],
            'sell_date': '20261026', 'sell_px': r['px_exec'], 'leg': 'hb_a_catchup_or_defense',
            'defers': 0, 'switched': False, 'pnl': pnl,
            'ret_pct': round((r['px_exec'] / r['buy_px'] - 1) * 100, 2),
            'reason': f"hb-a 09:40 场：{r['plan']}；引擎零执行(执行流水缺件)→本场补执行/防守清出｜证据 {SRC}",
            'pnl_note': '毛差(未扣费用)，成交价=决断后下一帧留档价±滑点0.10%',
            'fill_at': FILL_AT, 'fill_cls': 'A' if 'B级' not in r['plan'] else 'B', 'src': SRC,
            'ts': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        with open(led, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + '\n')
        # state 更新
        cash = round(cash + proceeds, 2)
        left = p['shares'] - r['shares']
        if left == 0:
            pos = [x for x in pos if x['code'] != key_code]
        else:
            p['shares'] = left
        done.append((key_code, r['shares'], r['px_exec'], proceeds, pnl))
    st['cash'] = cash
    st['positions'] = pos
    json.dump(st, open(stp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    report.setdefault(book, []).extend([f'{c} 卖 {s}@{p} 回款 {pr} pnl {pnl}' for c, s, p, pr, pnl in done])
    if not done:
        # 未成交易不写 state（避免无谓改动）
        pass

print(json.dumps(report, ensure_ascii=False, indent=1))
