# -*- coding: utf-8 -*-
import sys, json, io, csv, statistics
import pandas as pd
B=r"D:/股票数据/市场数据"
S=json.load(io.open(B+"/_学习/_tmp_limitup_20261104_stats.json",encoding="utf-8"))
cands=S['今日候选格']
out={}
pos=[c for c in cands if c['可兑现'] is not None]
out['全池可兑现']=dict(n=len(pos),正=sum(1 for c in pos if c['可兑现']>0),负=sum(1 for c in pos if c['可兑现']<0),
   合计pp=round(sum(c['可兑现'] for c in pos),3),均=round(statistics.mean([c['可兑现'] for c in pos]),3),
   max=round(max(c['可兑现'] for c in pos),3),min=round(min(c['可兑现'] for c in pos),3))
print(json.dumps(out,ensure_ascii=False))
# 尾盘族/其它族 整体
df=pd.read_csv(B+"/_学习/_tmp_limitup_gapcache_20261104.csv",encoding="utf-8-sig",dtype={'代码':str})
df['首封']=df['首封'].astype(str)
for name,m in [('尾盘>14',df['首封']>='14:00'),('非尾盘',df['首封']<'14:00'),('炸板回封',df['开板']>0),('未开板',df['开板']==0)]:
    x=df[m]; e1=x['E1'].dropna(); e2=x['E2'].dropna()
    g=x['GAP'].dropna()
    out[name]=dict(n=len(x),执1胜率=round(float((e1>0).mean()*100),1),执1均收=round(float(e1.mean()),3),
        执2胜率=round(float((e2>0).mean()*100),1),执2均收=round(float(e2.mean()),3),
        gate=round(float(((g>-3)&(g<=1.5)).mean()*100),1))
    print(name,json.dumps(out[name],ensure_ascii=False))
# 今日 zt_pool 炸板后回封数
zt4=list(csv.DictReader(io.open(B+"/20261104/zt_pool.csv",encoding="utf-8-sig")))
out['回封只数']=sum(1 for r in zt4 if int(float(r['炸板次数']))>0)
out['回封中尾盘']=sum(1 for r in zt4 if int(float(r['炸板次数']))>0 and str(r['首次封板时间']).zfill(6)>='140000')
out['末封>14:30']=sum(1 for r in zt4 if str(r['最后封板时间']).zfill(6)>='143000')
print('回封',out['回封只数'],out['末封>14:30'])
# 大票占比
big=sum(1 for r in zt4 if float(r['流通市值'])/1e8>=100)
print('≥100亿',big,round(big/len(zt4)*100,1))
# 行业家数
from collections import Counter
ind=Counter(r['所属行业'] for r in zt4).most_common(8)
print(ind)
out['行业top']=ind
out['大票只数']=big
json.dump(out,open(B+"/_学习/_tmp_limitup_20261104_agg.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
