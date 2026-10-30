# -*- coding: utf-8 -*-
import sys, io, json, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/_学习/'
ok = True
# A
a = json.load(open(B + 'logic判断_20261029.json', encoding='utf-8'))
assert set(a) == {'日期', '路', '判断', '荐票', '认知迭代', '深挖'}, set(a)
assert set(a['判断']) == {'结论', '证据', '档位', '置信度', '可证伪条件', '独立盲区声明'}, set(a['判断'])
assert a['路'] == 'logic' and a['日期'] == '20261029'
print('A ok: 证据', len(a['判断']['证据']), '条 | 可证伪', len(a['判断']['可证伪条件']), '| 盲区', len(a['判断']['独立盲区声明']),
      '| 档位', a['判断']['档位'], '置信度', a['判断']['置信度'], '| 荐票', len(a['荐票']['标的']),
      '| 认知迭代', len(a['认知迭代']), '| 深挖', len(a['深挖']))
# 标的∈zt_pool
zt = {r['代码'] for r in csv.DictReader(open('D:/股票数据/市场数据/20261029/zt_pool.csv', encoding='utf-8-sig'))}
for s in a['荐票']['标的']:
    assert set(s) == {'代码', '名称', '类型', '历史对照', '理由'}, set(s)
    assert s['代码'] in zt, s['代码'] + ' 不在zt_pool'
    print('  标的', s['代码'], s['名称'], s['类型'], '∈zt_pool ✓')
# C
c = json.load(open(B + '交易计划_logic_20261029.json', encoding='utf-8'))
assert set(c) == {'日期', '路', 'buys', 'sells', 'notes'}
print('C ok: buys', len(c['buys']), 'sells', len(c['sells']), 'weights', [b['权重%'] for b in c['buys']])
for b in c['buys']:
    assert b['代码'] in zt, b['代码']
    assert set(b) >= {'代码', '名称', '权重%', '理由'}
    print('   buy', b['代码'], b['名称'], b['权重%'], '%', 'gate' in str(b.keys()) or 'buy_gate' in b)
# 状态.json 持仓逐票
st = json.load(open('D:/股票数据/市场数据/_学习/_模拟盘/logic/状态.json', encoding='utf-8'))
print('状态 持仓:', st['持仓'], 'nav', st['nav'], '现金', st['现金'])
assert st['持仓'] == [] and c['sells'] == []
# D
d = json.load(open(B + '_能力回执片段_logic_20261029.json', encoding='utf-8'))
assert set(d) == {'日期', 'route', '采用', '拒绝', 'note'}
print('D ok: 采用', len(d['采用']), '拒绝', len(d['拒绝']))
# B html 配平 + 禁裸null
h = open(B + 'logic_body_20261029.html', encoding='utf-8').read()
h2 = re.findall(r'<h2>(.*?)</h2>', h)
print('B h2:', h2)
for t in ['div', 'table', 'tr', 'td', 'th', 'p']:
    o = len(re.findall(r'<%s[ >]' % t, h)); cl = len(re.findall(r'</%s>' % t, h))
    print(f'  <{t}> open={o} close={cl} {"OK" if o == cl else "MISMATCH"}')
assert 'None' not in h and 'null' not in h.lower().replace('nulls', '')
assert len(h2) == 6
assert all(('一 产业逻辑核心判断' == x or '二 链条纵深与环节卡位' == x or '三 中报预增双源交叉' == x
            or '四 风险日历与踩窗处置' == x or '五 深挖' == x or '六 认知迭代' == x) for x in h2)
print('ALL CHECKS PASSED')
