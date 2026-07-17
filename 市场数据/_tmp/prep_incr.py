# -*- coding: utf-8 -*-
"""增量prep: 老_P_stage.pkl(至0715) + 20260716新行(与_factor_table同口径正向重推)"""
import json,os,glob
import pandas as pd
L='_学习'; d='20260716'
P=pd.read_pickle(L+'/_P_stage.pkl')
P=P[P['日']!=d].copy()
df=pd.read_csv(f'{d}/zt_pool.csv',dtype={'代码':str}); df['代码']=df['代码'].str.zfill(6)
df=df[~df['名称'].astype(str).str.contains('退')]
rows=[]
for _,r in df.iterrows():
    mv=pd.to_numeric(r.get('流通市值'),errors='coerce'); fj=pd.to_numeric(r.get('封板资金'),errors='coerce')
    fb=str(r['首次封板时间']).split('.')[0].zfill(6)
    rows.append(dict(日=d,代码=r['代码'],名称=r.get('名称'),
        封额亿=round(float(fj)/1e8,2) if fj==fj else None,
        封单比=round(float(fj)/float(mv)*100,3) if (mv and mv>0 and fj==fj) else None,
        首封=fb[:2]+':'+fb[2:4],
        连板=int(pd.to_numeric(r.get('连板数',1),errors='coerce') or 1),
        开板=int(pd.to_numeric(r.get('炸板次数',0),errors='coerce') or 0),
        换手=float(pd.to_numeric(r.get('换手率'),errors='coerce')),
        市值亿=float(mv)/1e8 if mv==mv else None,
        股价=float(pd.to_numeric(r.get('最新价'),errors='coerce')),
        行业=str(r.get('所属行业'))))
N=pd.DataFrame(rows)
N['涨停总数']=len(N)
N['行业家数']=N.groupby('行业')['代码'].transform('size')
# 基因: 近10交易日该股涨停次数(全表口径)
all_days=sorted(set(P['日'].unique())|{d}); di={x:i for i,x in enumerate(all_days)}
occ={}
for c,dd in zip(P['代码'],P['日']): occ.setdefault(c,[]).append(di[dd])
N['基因']=[sum(1 for j in occ.get(c,[]) if di[d]-10<=j<di[d]) for c in N['代码']]
# 题材家数: 涨停对链条_{d}.json
j=json.load(open(f'{L}/涨停对链条_{d}.json',encoding='utf-8'))
mp={}
for t in j.get('题材线',[]):
    for s in t.get('环节',[]):
        for g in s.get('个股',[]): mp[g['代码']]=t['大方向']
cnt={}
for v in mp.values(): cnt[v]=cnt.get(v,0)+1
N['题材家数']=[cnt.get(mp.get(c)) if mp.get(c) else None for c in N['代码']]
wt=json.load(open(L+'/_市场温度表.json',encoding='utf-8'))
N['温度']=(wt.get(d) or {}).get('温度')
P2=pd.concat([P,N[P.columns]],ignore_index=True)
P2.to_pickle(L+'/_P_stage.pkl')
print('PREP_OK 样本行',len(P2),'新增',len(N))
