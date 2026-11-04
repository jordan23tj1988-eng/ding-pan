# -*- coding: utf-8 -*-
import json, io, sys, csv, os, statistics as st, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.chdir(r'D:\股票数据\市场数据')
zt = list(csv.DictReader(open('20261104/zt_pool.csv', encoding='utf-8-sig')))
q = {x['代码']: x for x in json.load(open('_学习/_q3full_logic_20261104.json', encoding='utf-8'))}

def bars(code):
    p = '_学习/_bars_cache/%s.csv' % code
    if not os.path.exists(p): return None
    rows = [r for r in csv.DictReader(open(p, encoding='utf-8-sig')) if r['close'] and r['date'] <= '2026-11-04']
    return [float(r['close']) for r in rows] if len(rows) > 251 else None

r250 = {}
for r in zt:
    c = bars(r['代码'])
    if c:
        r250[r['代码']] = (c[-1] / c[-251] - 1) * 100

fb = [(float(r['封板资金']) / float(r['流通市值']) * 100) for r in zt]
first = [r['首次封板时间'] for r in zt]
print('封单比 中位 %.2f%%  <1%% %d 只  1-3%% %d   >=3%% %d' % (
    st.median(fb), sum(1 for x in fb if x < 1), sum(1 for x in fb if 1 <= x < 3), sum(1 for x in fb if x >= 3)))
print('首封 <=093500:', sum(1 for t in first if t <= '093500'), '; 0935-1100:', sum(1 for t in first if '093500' < t <= '110000'),
      '; >1100:', sum(1 for t in first if t > '110000'), '; >=130000:', sum(1 for t in first if t >= '130000'))
print('开板0次:', sum(1 for r in zt if r['炸板次数'] == '0'), '; >=2次:', sum(1 for r in zt if int(r['炸板次数']) >= 2))
print('连板分布:', collections.Counter(int(r['连板数']) for r in zt))
print('成交额 中位(亿):', round(st.median(float(r['成交额']) / 1e8 for r in zt), 2))

print('\nr250 可算 n=%d; r250>=100%% 共 %d 只' % (len(r250), sum(1 for v in r250.values() if v >= 100)))
zz = [x for x in q.values() if x['档'] == '真增长']
print('真增长中 r250>=100%:', [(x['代码'], x['名称'], round(r250[x['代码']], 1)) for x in zz if r250.get(x['代码'], 0) >= 100])
print('真增长且 r250<100% 且 归母>=5亿:')
for x in zz:
    v = r250.get(x['代码'])
    if v is not None and v < 100 and x['归母亿'] >= 5:
        print('   %-6s %-6s 归母%6.2f亿 营收%+7.2f%% 同比%+8.1f%% r250%+7.1f%% 封单比%.2f 炸%d 首封%s 换手%.2f' % (
            x['代码'], x['名称'], x['归母亿'], x['营收按年'], x['净利同比'], v, x['封单比'], x['炸'], x['首封'], x['换手']))

# 板块组计数
d = json.load(open('_学习/涨停对链条_20261104.json', encoding='utf-8'))
lines = {l['大方向']: l['家数'] for l in d['题材线']}
semi = lines.get('半导体/芯片', 0); pcb = lines.get('PCB/元件载板', 0); ai = lines.get('AI算力/数据中心', 0)
print('\n半导体 %d + PCB %d + AI算力 %d = %d (%.1f%%)' % (semi, pcb, ai, semi + pcb + ai, (semi + pcb + ai) / 118 * 100))
semi_real = sum(1 for l in d['题材线'] if l['大方向'] == '半导体/芯片' for e in l['环节'] for s in e['个股'] if q[s['代码']]['档'] == '真增长')
pcb_real = sum(1 for l in d['题材线'] if l['大方向'] == 'PCB/元件载板' for e in l['环节'] for s in e['个股'] if q[s['代码']]['档'] == '真增长')
print('半导体真增长 %d, PCB真增长 %d' % (semi_real, pcb_real))
# 半导体 环节 家数分布
for l in d['题材线']:
    if l['大方向'] == '半导体/芯片':
        sz = [e['家数'] for e in l['环节']]
        print('半导体 环节数 %d, 单票环节 %d, 平均%.2f' % (len(sz), sum(1 for x in sz if x == 1), len(sz) / sum(sz)))
        print('开板占比', l['开板占比'], '最早封板', l['最早封板'], '最高', l['最高连板'])
    if l['大方向'] == 'PCB/元件载板':
        print('PCB 环节:', [(e['环节'], e['家数'], e['最早封板'], e['开板占比']) for e in l['环节']])
