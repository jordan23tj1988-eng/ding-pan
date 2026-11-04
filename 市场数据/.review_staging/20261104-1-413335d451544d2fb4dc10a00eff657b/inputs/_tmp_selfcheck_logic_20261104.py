# -*- coding: utf-8 -*-
import json, io, sys, re, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import os
os.chdir(r'D:\股票数据\市场数据')

j = json.load(open('_学习/logic判断_20261104.json', encoding='utf-8'))
p = json.load(open('_学习/交易计划_logic_20261104.json', encoding='utf-8'))
print('JSON OK: 判断 keys=', list(j.keys()))
print('档位', j['判断']['档位'], '置信度', j['判断']['置信度'], '证伪条数', len(j['判断']['可证伪条件']),
      '证据条数', len(j['判断']['证据']), '认知', len(j['认知迭代']))
print('荐票', j['荐票']['结论'][:40], [ (x['代码'], x['类型']) for x in j['荐票']['标的']])
print('buys', len(p['buys']), 'sells', [(s['代码'], s['腿']) for s in p['sells']])
zt = {r['代码'] for r in csv.DictReader(open('20261104/zt_pool.csv', encoding='utf-8-sig'))}
for x in j['荐票']['标的']:
    print('  in zt_pool?', x['代码'], x['代码'] in zt, x['类型'] in ('荐票', '观察'))

h = open('_学习/logic_body_20261104.html', encoding='utf-8').read()
print('\nHTML bytes', len(h.encode('utf-8')), 'h2', h.count('<h2'))
print('裸 null:', re.findall(r'>\s*null\s*<', h)[:5], '| 文本 null:', h.count('null'))
print('style= 数量:', h.count('style='))
white = ['#fff', '#ffffff', 'background:#f', 'background: #f', 'rgba(255']
print('可疑浅底:', [w for w in white if w.lower() in h.lower()])
classes = set()
for m in re.finditer(r'class="([^"]+)"', h):
    classes.update(m.group(1).split())
allow = {'card', 'obs', 'obslist', 'obs-head', 'obs-nm', 'obs-pos', 'obs-watch', 'obs-lab', 'obs-lab2',
         'obs-rec', 'table', 'trow', 'd6', 'gauge', 'kpi', 'strip', 'hint', 'sup', 'details', 'chain', 'tli', 'tlfold'}
print('classes:', sorted(classes))
print('未授权 class:', sorted(classes - allow))
for kw in ['产业逻辑', '链条', '中报', '风险日历', '荐票', '自主深挖', '认知迭代']:
    print('  h2 含 %s :' % kw, any(kw in m for m in re.findall(r'<h2[^>]*>(.*?)</h2>', h, re.S)))
