# -*- coding: utf-8 -*-
"""20261012 出页门禁阻断项的数据层修正（最小改动, 全部可回源）。
1) limitup <p> 首现温度须为当日值: 温度49.6→32.4  -> 温度32.4（前值49.6）
2) theme 生命周期判断 json / body 内 "环比None" -> "环比—"（禁词 None）
3) theme body 现金金额避免被 \\d{6} 误抓为代码: 1019994.06 -> 1,019,994.06
4) logic "昨日涨停溢价null" -> "昨日涨停溢价缺源"（C1 缺口叙述词）
5) judgment 一句话 补写（取自总审_20261012.json 五路裁决/总裁决, 不新增判断）
"""
import json, os

BASE = r'D:\股票数据\市场数据'
L = os.path.join(BASE, '_学习')
D = '20261012'
log = []


def edit(path, pairs, required=True):
    t = open(path, encoding='utf-8').read()
    for old, new in pairs:
        n = t.count(old)
        if n == 0:
            if required:
                raise SystemExit('MISS in %s: %r' % (path, old[:60]))
            continue
        t = t.replace(old, new)
        log.append('  %s: %r x%d' % (os.path.basename(path), old[:46], n))
    open(path, 'w', encoding='utf-8').write(t)


# 1) limitup 温度首现
edit(os.path.join(L, 'limitup_body_%s.html' % D),
     [('温度49.6→32.4转偏冷', '温度32.4（前值49.6）转偏冷')], required=False)

# 2) theme 环比None
edit(os.path.join(L, '题材生命周期判断_%s.json' % D),
     [('环比None', '环比—')], required=False)
edit(os.path.join(L, 'theme_body_%s.html' % D),
     [('环比None', '环比—')], required=False)

# 3) theme 现金金额
edit(os.path.join(L, 'theme_body_%s.html' % D),
     [('现金1019994.06', '现金1,019,994.06元')], required=False)

# 4) logic 溢价null
for f in ('logic判断_%s.json' % D, 'logic_body_%s.html' % D):
    edit(os.path.join(L, f), [('昨日涨停溢价null', '昨日涨停溢价缺源')], required=False)

# 5) judgment bodies 同步(以文件为准, 但保留台账注入段: 逐条替换而非整段覆盖)
jp = os.path.join(L, 'judgment_%s.json' % D)
J = json.load(open(jp, encoding='utf-8'))
REPL = [
    ('温度49.6→32.4转偏冷', '温度32.4（前值49.6）转偏冷'),
    ('环比None', '环比—'),
    ('现金1019994.06', '现金1,019,994.06元'),
    ('昨日涨停溢价null', '昨日涨停溢价缺源'),
]
for r in ('limitup', 'theme', 'logic'):
    b = J['bodies'][r]
    for old, new in REPL:
        if old in b:
            J['bodies'][r] = b = b.replace(old, new)
            log.append('  judgment.bodies.%s: %r' % (r, old[:40]))
if not (J.get('一句话') or '').strip():
    J['一句话'] = ('五路B、C、C、C、C；总档C防守（置信度76）；正式荐票并集0只、条件观察3只；空仓。')
    log.append('  judgment.一句话 已补写')
json.dump(J, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('\n'.join(log) if log else '无改动')
# 复核
for f in ('limitup_body_%s.html' % D, 'theme_body_%s.html' % D, 'logic_body_%s.html' % D):
    t = open(os.path.join(L, f), encoding='utf-8').read()
    print('残查 %s: None=%d 溢价null=%d 1019994=%d'
          % (f, t.count('None'), t.count('溢价null'), t.count('1019994')))
print('题材生命周期 None:', open(os.path.join(L, '题材生命周期判断_%s.json' % D), encoding='utf-8').read().count('None'))
