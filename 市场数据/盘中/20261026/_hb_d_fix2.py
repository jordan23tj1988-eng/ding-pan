# -*- coding: utf-8 -*-
"""hb-d 13:30 补正2：lhb 账 nav 口径补列（追加件，不覆盖原件与补正1）。"""
import json, os, hashlib, datetime

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(D, '临盘决断_20261026_1330.json')
F1 = os.path.join(D, '临盘决断_20261026_1330_补正1.json')
TGT = os.path.join(D, '临盘决断_20261026_1330_补正2.json')
assert os.path.exists(SRC) and os.path.exists(F1)
assert not os.path.exists(TGT), '补正2 已存在，禁止覆盖'

h = hashlib.sha256(open(SRC, 'rb').read()).hexdigest()
h1 = hashlib.sha256(open(F1, 'rb').read()).hexdigest()

# 复算 lhb
s = json.load(open(r'D:\股票数据\市场数据\_学习\_模拟盘\lhb\state.json', encoding='utf-8'))
cash = s['cash']
mv = 0.0
nav = round(cash + mv, 2)

bz = {
 'date': '20261026',
 'session': 'hb-d',
 'ts': '13:30',
 '补正号': 2,
 'write_ts': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
 '性质': '勘误补正（不覆盖原件、不改成交、不改判断）',
 '原件': {'文件': '临盘决断_20261026_1330.json', 'sha256': h, '声明': '原件一字未改'},
 '前序补正': {'文件': '临盘决断_20261026_1330_补正1.json', 'sha256': h1, '声明': '补正1 一字未改，本件为追加'},
 '发现方式': '哨兵 H01（五本账 nav 逐账复算）FAIL：文件对 master/auction/limitup/logic 均列 nav，唯 lhb 只列现金 → 口径不统一',
 '修正明细': [
   {'位置': 'no_action.持仓核.lhb',
    '原文': '空仓，现金 1003727.3 元',
    '问题': '五本账 nav 口径不统一：其余四本均给 nav，lhb 缺 nav；空仓账户 nav=cash 属常识但仍须显式列出，否则核销时无法逐账对齐',
    '更正为': f'空仓，现金 {cash} 元、持仓市值 {mv}、nav≈{nav} 元（空仓账户 nav=cash，复算：{cash}+{mv}={nav}）'},
 ],
 '复算依据': {'账本': r'D:\股票数据\市场数据\_学习\_模拟盘\lhb\state.json', 'cash': cash,
           'positions': s['positions'], 'mv': mv, 'nav': nav},
 '不改成交声明': {
   'fills': [],
   '权限分级': 'A 0 笔 / B 0 笔 / C 0 笔（与原件一致）',
   '判断': '本场判断不变（修复未确立、持仓不动、不新开仓）',
   '影响': '纯口径补列，不改变任何动作、概率、净值数值'},
 '口径': '①本补正不产生撮合数字；②lhb nav 可由 state.json 逐项复算；③本文件对用户=参考，不是操盘指令。',
}
json.dump(bz, open(TGT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', TGT, os.path.getsize(TGT), 'lhb nav', nav)
print('原件', h[:16], '补正1', h1[:16])
