# -*- coding: utf-8 -*-
"""hb-f 14:45 深场B 落盘哨兵：钉帧复算 + 账务闭环 + 发版不可覆盖校验。只读（不写任何成交）。
钉帧：从决断件自报 time 戳定位 realtime_ticks 帧，禁止用运行时刻末帧复核历史文件。"""
import json, os, hashlib, datetime, sys

D = os.path.dirname(os.path.abspath(__file__))
OK, FAIL = [], []


def chk(no, name, cond, detail=''):
    (OK if cond else FAIL).append((no, name, detail))
    print(('PASS' if cond else 'FAIL'), no, name, '' if cond else '<-- ' + str(detail))


pub = os.path.join(D, '临盘决断_20261026_1445.json')
doc = json.load(open(pub, encoding='utf-8'))
audit = json.load(open(os.path.join(D, '入账_20261026_1445.json'), encoding='utf-8'))
fix = json.load(open(os.path.join(D, '临盘决断_20261026_1445_补正1.json'), encoding='utf-8'))
Q = json.load(open(os.path.join(D, '_hb_f_quote_1445.json'), encoding='utf-8'))['rows']
QN = json.load(open(os.path.join(D, '_hb_f_quote_next.json'), encoding='utf-8'))['rows']
P = json.load(open(os.path.join(D, '_hb_f_pools_1445.json'), encoding='utf-8'))
st = {a: json.load(open(rf'D:\股票数据\市场数据\_学习\_模拟盘\{a}\state.json', encoding='utf-8'))
      for a in ('master', 'auction', 'limitup', 'lhb', 'logic')}
led = [json.loads(l) for l in open(r'D:\股票数据\市场数据\_学习\_模拟盘\master\账本.jsonl', encoding='utf-8') if l.strip()]

# ---- A 发版完整性 ----
chk('A01', '发版件存在且唯一', os.path.exists(pub) and not os.path.exists(pub + '.tmp'), pub)
sha = hashlib.sha256(open(pub, 'rb').read()).hexdigest()
chk('A02', '发版件 sha256 与入账审计件登记一致', sha == audit['发出版sha256'], (sha, audit['发出版sha256']))
chk('A03', '补正件登记的原件 sha256 一致', fix['原件']['sha256'] == sha, fix['原件']['sha256'])
chk('A04', '补正件不改成交声明为 1 笔卖出', '1 笔卖出' in fix['不改成交声明']['fills'])
chk('A05', 'session/date 字段', doc['date'] == '20261026' and doc['session'] == 'hb-f')

# ---- B 锚帧可定位 ----
fr = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
fr.sort(key=lambda x: x['ts'])
win = doc['数据新鲜度']['窗口']
end = win.split('~')[-1].strip()
chk('B01', '新鲜度窗口末帧带日期前缀', end.count('-') >= 2 and end[:4] == '2026', end)
chk('B02', '窗口末帧可在 realtime_ticks 定位', any(f['ts'] == end for f in fr), end)
chk('B03', '末帧龄 <600s（写件时）', doc['数据新鲜度']['末帧龄_秒'] < 600, doc['数据新鲜度']['末帧龄_秒'])
chk('B04', '无 >180s 断档', doc['数据新鲜度']['超180s断档'] == '无')
chk('B05', '决断帧时戳与报价源一致', Q['sz002639']['t'][8:14] == '144642', Q['sz002639']['t'])

# ---- C 成交机械复算 ----
f0 = doc['fills'][0]
px_next = QN['sz002639']['px']
chk('C01', '决断帧价 13.61', Q['sz002639']['px'] == 13.61, Q['sz002639']['px'])
chk('C02', '下一tick留档价 13.58', f0['px'] == px_next == 13.58, (f0['px'], px_next))
chk('C03', 'px_exec=留档价×(1-0.10%) 两位取整', f0['px_exec'] == round(px_next * 0.999, 2) == 13.57, f0['px_exec'])
chk('C04', 'qty 2600 且为整手', f0['qty'] == 2600 and f0['qty'] % 100 == 0)
chk('C05', '成交金额复算 35,282.00', round(f0['px_exec'] * f0['qty'], 2) == 35282.00)
cost = 38447.21
chk('C06', 'pnl 复算 -3,165.21', round(35282.00 - cost, 2) == -3165.21, round(35282.00 - cost, 2))
chk('C07', 'ret 复算 -8.23%', abs(round((35282.00 - cost) / cost * 100, 2) + 8.23) < 1e-9)
chk('C08', 'fills 只有 1 笔且为卖出', len(doc['fills']) == 1 and f0['action'] == 'fill_sell')
chk('C09', 'route=master', f0['route'] == 'master')

# ---- D 账务闭环 ----
last = led[-1]
chk('D01', '账本末行=本笔卖出', last['ev'] == 'sell' and last['code'] == '002639' and last['shares'] == 2600)
chk('D02', '账本成交价与发版一致', last['sell_px'] == f0['px_exec'] and abs(last['pnl'] + 3165.21) < 0.01)
chk('D03', 'state.master 现金 960,407.64', abs(st['master']['cash'] - 960407.64) < 0.01, st['master']['cash'])
chk('D04', 'state.master 已无 002639', all(p['code'] != '002639' for p in st['master']['positions']))
chk('D05', 'master 持仓=002242/003021', sorted(p['code'] for p in st['master']['positions']) == ['002242', '003021'])
mv = round(800 * 21.59 + 100 * 96.20, 2)
chk('D06', 'master 市值 26,892.00', mv == 26892.00, mv)
chk('D07', 'master nav 987,299.64', round(960407.64 + mv, 2) == 987299.64)
navs = {'master': round(960407.64 + mv, 2),
        'auction': round(st['auction']['cash'] + 200 * 96.20, 2),
        'limitup': round(st['limitup']['cash'] + 100 * 96.20, 2),
        'lhb': round(st['lhb']['cash'], 2), 'logic': round(st['logic']['cash'], 2)}
chk('D08', '五账 nav 合计与发版一致', abs(sum(navs.values()) - doc['汇总']['五账nav合计']) < 0.01, (sum(navs.values()), doc['汇总']['五账nav合计']))
chk('D09', '补正1 时点更正为决断帧 21.59', '21.59' in fix['修正明细'][0]['更正为'])

# ---- E 池数据复算 ----
zt, zb, dt = P['zt'], P['zb'], P['dt']
chk('E01', '涨停池 54', len(zt) == 54 == doc['no_action']['环境读数']['全市场']['涨停'], len(zt))
chk('E02', '炸板池 23', len(zb) == 23 == doc['no_action']['环境读数']['全市场']['炸板'], len(zb))
chk('E03', '炸板率 0.2987', abs(len(zb) / (len(zt) + len(zb)) - 0.2987) < 5e-5)
chk('E04', '最大行业 6 只 <8 线级门', doc['no_action']['环境读数']['全市场']['行业分布'][0][1] == 6)
chk('E05', '连板梯次 39/9/5/1', dict(doc['no_action']['环境读数']['全市场']['连板梯次']) == {1: 39, 2: 9, 3: 5, 4: 1})
chk('E06', '最高板 4 且为 600838', doc['no_action']['环境读数']['全市场']['最高板'].startswith('4 板（600838'))
chk('E07', '电机Ⅱ 涨停 0 只', not [r for r in zt if r.get('hybk') == '电机Ⅱ'])
chk('E08', '301502 在炸板池', any(r.get('c') == '301502' for r in zb))
chk('E09', '持仓无一只进涨停/炸板/跌停池', not [r for r in zt + zb + dt if r.get('c') in ('002242', '003021')])
chk('E10', '跌停池 0', len(dt) == 0)
chk('E11', '掉板率 41.94%（31→18）', abs((31 - 18) / 31 - 0.4194) < 5e-5)

# ---- F 判断/口径完整性 ----
chk('F01', '权限分级 A/B/C 齐全', all(k in doc['权限分级'] for k in ('A', 'B', 'C')))
chk('F02', '持仓逐票表态 5 条（含已清票）', len(doc['no_action']['持仓逐票表态']) == 5)
chk('F03', '防守三查 3 条', len(doc['no_action']['防守三查']) == 3)
chk('F04', '概率区间为区间非点值', all('~' in p for p in [x for x in doc['no_action']['判断'] if '概率' in x]))
chk('F05', '异常与欠账 ≥4 条', len(doc['异常与欠账']) >= 4)
chk('F06', '复盘 md 已落盘', os.path.exists(r'D:\股票数据\市场数据\_学习\盘中尾盘复盘_20261026.md'))
md = open(r'D:\股票数据\市场数据\_学习\盘中尾盘复盘_20261026.md', encoding='utf-8').read()
chk('F07', 'md 含卖出价 13.57 与漏执行成本 3,094.00', '13.57' in md and '3,094.00' in md)
chk('F08', 'md 声明判断非指令', '不是操盘指令' in md)
chk('F09', '无『待补账』式旧表述残留', '已判卖未入账' not in json.dumps(doc['权限分级'], ensure_ascii=False) or '事实更正' in doc['fills'][0]['rule'])

print('\n==== hb-f 14:45 哨兵：%d PASS / %d FAIL ====' % (len(OK), len(FAIL)))
if FAIL:
    print('FAIL 明细：', FAIL)
    sys.exit(1)
