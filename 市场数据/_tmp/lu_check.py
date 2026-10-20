# -*- coding: utf-8 -*-
import json, re, io
B = "D:/股票数据/市场数据/_学习"

for p in (f"{B}/limitup判断_20261020.json", f"{B}/交易计划_limitup_20261020.json"):
    d = json.load(open(p, encoding='utf-8'))
    print("OK json", p, list(d.keys()))
    if '判断' in d:
        print("  档位", d['判断']['档位'], "置信度", d['判断']['置信度'], "证据条数", len(d['判断']['证据']))
        print("  荐票标的", [(x['代码'], x['类型']) for x in d['荐票']['标的']])
        print("  认知迭代", len(d['认知迭代']), [x['标题'][:14] for x in d['认知迭代']])
        print("  深挖字数", len(d['深挖']))
    if 'buys' in d:
        print("  buys", len(d['buys']), "sells", [(x['代码'], x['腿']) for x in d['sells']])

h = open(f"{B}/limitup_body_20261020.html", encoding='utf-8').read()
print("HTML 字数", len(h))
print("h2:", re.findall(r'<h2>(.*?)</h2>', h))
print("LEDGER:", h.count('<!--LEDGER-->'), h.count('<!--/LEDGER-->'))
print("script/style:", h.lower().count('<script'), h.lower().count('<style'))
print("div open/close:", len(re.findall(r'<div\b', h)), h.count('</div>'))
print("表格 open/close:", h.count('<table'), h.count('</table>'))
print("禁词 '认知迭代：'", h.count('认知迭代：'))
print("禁词 '认知迭代:'", h.count('认知迭代:'))
# 简易嵌套检查
depth = 0; bad = None
for m in re.finditer(r'<div\b[^>]*>|</div>', h):
    if m.group(0).startswith('</'):
        depth -= 1
        if depth < 0 and bad is None: bad = m.start()
    else:
        depth += 1
print("div 最终深度", depth, "提前闭合位置", bad)
