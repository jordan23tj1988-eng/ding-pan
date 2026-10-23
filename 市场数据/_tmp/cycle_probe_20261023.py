# -*- coding: utf-8 -*-
import csv, json, statistics as st
from collections import Counter

B='D:/股票数据/市场数据'
def zt(d):
    return list(csv.DictReader(open('%s/%s/zt_pool.csv'%(B,d),encoding='utf-8-sig')))
y=zt('20261022'); t=zt('20261023')
def lb(rows): return Counter(int(float(r['连板数'])) for r in rows)
print('昨梯队',dict(sorted(lb(y).items())))
print('今梯队',dict(sorted(lb(t).items())))
# 逐码晋级
ym={r['代码']:r for r in y}; tm={r['代码']:r for r in t}
live=[c for c in ym if c in tm]
print('昨涨停今日仍涨停 %d/%d=%.3f'%(len(live),len(ym),len(live)/len(ym)))
# 各档晋级率
from collections import defaultdict
base=defaultdict(list); hit=Counter()
for c,r in ym.items():
    n=int(float(r['连板数'])); base[n].append(c)
    if c in tm and int(float(tm[c]['连板数']))==n+1: hit[n]+=1
for n in sorted(base): print('  %d进%d: %d/%d=%.3f'%(n,n+1,hit[n],len(base[n]),hit[n]/len(base[n])))
# 首封时间分布
def hhmm(r):
    s=r['首次封板时间'].strip().zfill(6); return s[:2]+':'+s[2:4]
buckets=Counter()
for r in t:
    hm=hhmm(r); buckets[hm[:5] if hm<'10:00' else ('<=10:00' if hm<='10:00' else ('<=11:30' if hm<='11:30' else ('<=13:00' if hm<='13:00' else ('<=14:00' if hm<='14:00' else '>14:00'))))]+=1
early=[r for r in t if hhmm(r)<='09:36']
print('首封<=09:36 %d/%d=%.3f'%(len(early),len(t),len(early)/len(t)))
late=[r for r in t if hhmm(r)>='13:01']
print('首封>=13:01 %d/%d=%.3f'%(len(late),len(t),len(late)/len(t)))
# 封单
def num(x):
    try: return float(str(x).replace(',',''))
    except: return 0.0
feng=[(r['名称'],num(r['封板资金'])/1e8,num(r['封板资金'])/num(r['成交额'])*100,num(r['封板资金'])/num(r['流通市值'])*100,int(float(r['炸板次数']))) for r in t]
print('封单总额亿 %.2f'%(sum(f[1] for f in feng)))
print('封单/成交 中位 %.3f%%  封单/流通 中位 %.3f%%'%(st.median([f[2] for f in feng]),st.median([f[3] for f in feng])))
print('炸板次数合计',sum(f[4] for f in feng),' 炸0只数',sum(1 for f in feng if f[4]==0))
# 高标
print('--- 6板/3板/2板 ---')
for r in sorted(t,key=lambda r:-int(float(r['连板数']))):
    n=int(float(r['连板数']))
    if n>=2: print(n,r['代码'],r['名称'],r['所属行业'],'封单亿%.2f'%(num(r['封板资金'])/1e8),'炸%d'%int(float(r['炸板次数'])),'首封',r['首次封板时间'],'换手',r['换手率'])
print('--- 换手/流通分布 ---')
print('流通市值中位亿 %.1f'%st.median([num(r['流通市值'])/1e8 for r in t]))
