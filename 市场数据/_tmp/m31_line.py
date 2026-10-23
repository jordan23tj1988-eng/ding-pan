# -*- coding: utf-8 -*-
import csv, json, statistics as st
g=json.load(open('_学习/题材归位_20261023.json',encoding='utf-8'))['映射']
rows=list(csv.DictReader(open('20261023/zt_pool.csv',encoding='utf-8-sig')))
def f(x):
    try: return float(str(x).replace('%',''))
    except: return 0.0
line=[r for r in rows if g.get(r['代码'],{}).get('大方向')=='机器人']
print('线内只数', len(line), '全池', len(rows))
fb=[int(r['首次封板时间']) for r in line if r['首次封板时间'].strip()]
late=[x for x in fb if x>=130000]; early=[x for x in fb if x<=93600]
print('首封≥13:00 %d/%d=%.4f'%(len(late),len(line),len(late)/len(line)))
print('首封<=09:36 %d/%d=%.4f'%(len(early),len(line),len(early)/len(line)))
r_float=[f(r['封板资金'])/f(r['流通市值'])*100 for r in line if f(r['流通市值'])>0]
print('封单/流通 median %.4f%% mean %.4f%%'%(st.median(r_float), sum(r_float)/len(r_float)))
print('封单率<1% 只数', sum(1 for x in r_float if x<1), '占比 %.2f'%(sum(1 for x in r_float if x<1)/len(r_float)))
print('炸板合计', sum(int(r['炸板次数']) for r in line), '炸>0只数', sum(1 for r in line if int(r['炸板次数'])>0),
      '开板占比 %.2f'%(sum(1 for r in line if int(r['炸板次数'])>0)/len(line)))
print('二板', sum(1 for r in line if int(r['连板数'])==2), '连板分布', {k:sum(1 for r in line if int(r['连板数'])==k) for k in sorted({int(r['连板数']) for r in line})})
print('代码', [r['代码'] for r in line])
