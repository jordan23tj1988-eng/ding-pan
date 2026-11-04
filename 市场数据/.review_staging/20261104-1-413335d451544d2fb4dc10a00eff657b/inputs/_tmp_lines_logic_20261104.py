# -*- coding: utf-8 -*-
import json, io, sys, collections, statistics as st
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import os
os.chdir(r'D:\股票数据\市场数据')
q = {x['代码']: x for x in json.load(open('_学习/_q3full_logic_20261104.json', encoding='utf-8'))}
d = json.load(open('_学习/涨停对链条_20261104.json', encoding='utf-8'))

print('%-22s %-4s %-4s %-6s %-6s %-8s %-6s %-6s' % ('大方向', '家数', '真增', '真增率', '环节数', '最高板', '营收中位', '归母中位'))
rows = []
for line in d['题材线']:
    codes = [s['代码'] for env in line['环节'] for s in env['个股']]
    zz = [q[c] for c in codes if c in q and q[c]['档'] == '真增长']
    ysz = [q[c]['营收按年'] for c in codes if c in q and q[c]['营收按年'] is not None]
    gmy = [q[c]['归母亿'] for c in codes if c in q and q[c]['归母亿'] is not None]
    n = len(codes)
    rows.append((line['大方向'], n, len(zz), round(len(zz) / n * 100, 1), len(line['环节']),
                 line.get('最高连板'), round(st.median(ysz), 1), round(st.median(gmy), 2)))
for r in sorted(rows, key=lambda x: -x[1]):
    print('%-22s %-4d %-4d %-6s %-6d %-8s %-6s %-6s' % r)

print('\n=== 半导体/芯片 环节级 ===')
for line in d['题材线']:
    if line['大方向'] != '半导体/芯片':
        continue
    for env in line['环节']:
        print('--', env['环节'], 'n=%d' % env['家数'], '首封', env['最早封板'], '开板占比', env['开板占比'])
        for s in env['个股']:
            x = q.get(s['代码'], {})
            print('   %-6s %-6s %-8s 营收%-7s 归母%-6s 基期%-6s 封单比%-5s 换手%-5s 炸%s' % (
                s['代码'], s['名称'], x.get('档'), x.get('营收按年'), x.get('归母亿'), x.get('基期归母亿'),
                x.get('封单比'), x.get('换手'), x.get('炸')))

print('\n=== PCB/覆铜板/材料 环节级（AI算力线）===')
for line in d['题材线']:
    if 'PCB' not in line['大方向'] and line['大方向'] != 'AI算力/数据中心':
        continue
    print('##', line['大方向'], line['家数'])
    for env in line['环节']:
        print('--', env['环节'], 'n=%d' % env['家数'], '开板占比', env['开板占比'])
        for s in env['个股']:
            x = q.get(s['代码'], {})
            print('   %-6s %-6s %-8s 营收%-7s 归母%-6s 基期%-6s 封单比%-5s 换手%-5s 炸%s 催化%s' % (
                s['代码'], s['名称'], x.get('档'), x.get('营收按年'), x.get('归母亿'), x.get('基期归母亿'),
                x.get('封单比'), x.get('换手'), x.get('炸'), s.get('催化')))

print('\n=== 贵金属/黄金 环节级 ===')
for line in d['题材线']:
    if '贵金属' in line['大方向']:
        for env in line['环节']:
            print('--', env['环节'], 'n=%d' % env['家数'], '首封', env['最早封板'], '开板占比', env['开板占比'])
            for s in env['个股']:
                x = q.get(s['代码'], {})
                print('   %-6s %-6s %-8s 营收%-7s 归母%-6s 基期%-6s 封单比%-5s 炸%s' % (
                    s['代码'], s['名称'], x.get('档'), x.get('营收按年'), x.get('归母亿'), x.get('基期归母亿'),
                    x.get('封单比'), x.get('炸')))
