# -*- coding: utf-8 -*-
"""坑18替代路v2: 用bars_cache(已补齐0716)重建spot同构DataFrame(今开/最新价/涨跌幅), monkeypatch重跑先行指标"""
import sys,os,json
import pandas as pd
z=pd.read_csv('20260715/zt_pool.csv',dtype={'代码':str})
codes=[c.zfill(6) for c in z['代码']]
rows=[]
for c in codes:
    f='_学习/_bars_cache/'+c+'.csv'
    if not os.path.isfile(f): continue
    b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
    b=b.reset_index(drop=True)
    idx=b.index[b['date']=='20260716']
    if not len(idx): continue
    i=idx[0]
    if i==0: continue
    o=float(b.loc[i,'open']); cl=float(b.loc[i,'close']); pv=float(b.loc[i-1,'close'])
    rows.append({'代码':c,'名称':'','今开':o,'最新价':cl,'涨跌幅':round((cl/pv-1)*100,2) if pv>0 else None})
SP=pd.DataFrame(rows)
print('bars重建spot:',len(SP),'/',len(codes))
import akshare
akshare.stock_zh_a_spot_em=lambda: SP.copy()
import importlib.util
spec=importlib.util.spec_from_file_location('lead','情绪先行指标.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ths=m.load_ths(); t=m.load_out()
row=m.run_day('20260716',ths,t,with_spot=True)
m.save_out(t)
m.summary_line('20260716',row)
print(json.dumps(t['20260716'].get('昨日涨停溢价'),ensure_ascii=False))
