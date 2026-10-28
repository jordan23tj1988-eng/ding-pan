# -*- coding: utf-8 -*-
"""1027 收尾：把 lhb/logic 的汇总状态对齐到引擎净值真值(20261027)，供看板与 C2 同源。

原则：只搬引擎已算出的数（净值.json[20261027].nav），不重算、不补造。
若 状态.json 已推进到 >= 20261027 则跳过（幂等，防覆盖 1028 结算）。
"""
import json, os, shutil, datetime

L = '_学习/_模拟盘/'
TARGET = '20261027'
for route in ('lhb', 'logic'):
    sp = os.path.join(L, route, '状态.json')
    np_ = os.path.join(L, route, '净值.json')
    st = json.load(open(sp, encoding='utf-8'))
    nav = json.load(open(np_, encoding='utf-8'))
    if TARGET not in nav:
        print('%-6s 净值缺 %s，跳过' % (route, TARGET))
        continue
    if str(st.get('date') or '') > TARGET:
        print('%-6s 状态已到 %s（>目标日），不覆盖' % (route, st.get('date')))
        continue
    if str(st.get('date') or '') == TARGET:
        print('%-6s 状态已是 %s，无需改动' % (route, TARGET))
        continue
    bak = sp + '.bak_1027align'
    if not os.path.exists(bak):
        shutil.copy2(sp, bak)
    row = nav[TARGET]
    cum = round((float(row['nav']) - 1) * 100, 4)
    st['date'] = TARGET
    st['nav'] = row['nav']
    st['累计pct'] = cum
    st.setdefault('对齐说明', '由 净值.json[%s].nav=%.6f 回填(引擎真值, 未重算)' % (TARGET, row['nav']))
    json.dump(st, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('%-6s 状态已对齐: date=%s nav=%.6f 累计pct=%.4f（备份 %s）' % (route, TARGET, row['nav'], cum, os.path.basename(bak)))
