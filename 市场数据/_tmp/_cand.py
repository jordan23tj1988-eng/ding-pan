# -*- coding: utf-8 -*-
import sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/'
def J(p): return json.loads(open(p, encoding='utf-8-sig').read())
zt = {r['代码']: r for r in csv.DictReader(open(B+'20261029/zt_pool.csv', encoding='utf-8-sig'))}
cand = ['600592','600118','603703','301079','603131','600501','002149','605598','002526','601956','001219','002708','002943']
for c in cand:
    r = zt[c]
    print(c, r['名称'], '|连板', r['连板数'], '|首封', r['首次封板时间'], '|末封', r['最后封板时间'],
          '|炸', r['炸板次数'], '|封板资金', r['封板资金'], '|成交额', r['成交额'], '|流通市值', r['流通市值'],
          '|换手', r['换手率'], '|涨停统计', r['涨停统计'])
# 封单比 = 封板资金/成交额
print('\n封单/成交 比:')
for c in cand:
    r = zt[c]
    fb = float(r['封板资金']); amt = float(r['成交额'])
    print(f"  {c} {r['名称']:<6} {fb/1e8:.2f}亿/{amt/1e8:.2f}亿 = {fb/amt*100:.2f}%  流通{float(r['流通市值'])/1e8:.1f}亿 换手{r['换手率']}")
print('\n--- 涨停对链条 机器人/消费 环节 ---')
m = J(B+'_学习/涨停对链条_20261029.json')
for line in m['题材线']:
    if any(k in line['大方向'] for k in ['机器人','消费']):
        print('##', line['大方向'], line['家数'], '最高', line['最高连板'], line.get('强度画像'))
        for h in line['环节']:
            print('   -', h['环节'], h['家数'], h.get('快判'))
