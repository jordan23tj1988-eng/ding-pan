# -*- coding: utf-8 -*-
import csv, json, statistics as st
from collections import Counter
B='D:/股票数据/市场数据'
def zt(d): return list(csv.DictReader(open('%s/%s/zt_pool.csv'%(B,d),encoding='utf-8-sig')))
def num(x):
    try: return float(str(x).replace(',',''))
    except: return 0.0
for d in ['20261022','20261023']:
    rows=zt(d)
    fr=[num(r['封板资金'])/num(r['流通市值'])*100 for r in rows]
    fa=[num(r['封板资金'])/num(r['成交额'])*100 for r in rows]
    zha=sum(int(float(r['炸板次数'])) for r in rows)
    z0=sum(1 for r in rows if int(float(r['炸板次数']))==0)
    yz=sum(1 for r in rows if r['首次封板时间'].strip().zfill(6)[:4]=='0925' and int(float(r['炸板次数']))==0)
    print(d,'n=%d 封单/流通中位%.3f%% 封单/成交中位%.2f%% 炸合计%d 炸0=%d 一字(0925且炸0)=%d'%(len(rows),st.median(fr),st.median(fa),zha,z0,yz))
# 昨3板
y=zt('20261022')
print('昨3板:',[(r['代码'],r['名称'],r['所属行业']) for r in y if int(float(r['连板数']))==3])
print('昨5板:',[(r['代码'],r['名称']) for r in y if int(float(r['连板数']))==5])
# 今日题材归位机器人
try:
    g=json.load(open(B+'/_学习/题材归位_20261023.json',encoding='utf-8'))
    print('归位 keys',list(g.keys())[:6])
    mp=g.get('映射') or {}
    cnt=Counter()
    for k,v in mp.items():
        if isinstance(v,dict):
            line=v.get('题材') or v.get('线') or v.get('主题材')
            cnt[str(line)]+=1
        else: cnt[str(v)]+=1
    print('归位线计数 top8',cnt.most_common(8))
except Exception as e: print('归位ERR',e)
