# -*- coding: utf-8 -*-
import sys, json, io, csv
sys.path.insert(0, r"D:/股票数据/市场数据")
import pandas as pd, numpy as np
df=pd.read_csv(r"D:/股票数据/市场数据/_学习/_tmp_limitup_gapcache_20261104.csv",encoding="utf-8-sig",dtype={'代码':str})
df['首封']=df['首封'].astype(str)
def fb(v): return '一字≤9:25' if v<='09:25' else '秒板≤9:31' if v<='09:31' else '早盘≤10:00' if v<='10:00' else ('盘中10-14' if v<='14:00' else '尾盘>14')
def lb(v): return '首板' if v<=1 else ('2板' if v==2 else ('3板' if v==3 else '4板+'))
def th(v): return '<3%' if v<10 and v<3 else ('3-10%' if v<10 else ('10-20%' if v<20 else '≥20%'))
df['cell']=df['连板'].map(lb)+'|'+df['首封'].map(fb)+'|'+df['换手'].map(th)
G=df.dropna(subset=['GAP'])
cells={}
for k,x in G.groupby('cell'):
    cells[k]=dict(n=len(x),gate=round(float(((x['GAP']>-3)&(x['GAP']<=1.5)).mean()*100),1),
                  med=round(float(x['GAP'].median()),2),
                  e1=round(float(x['E1'].mean()),3) if x['E1'].notna().any() else None,
                  w1=round(float((x['E1']>0).mean()*100),1) if x['E1'].notna().any() else None)
def row(d,codes):
    zt={r['代码']:r for r in csv.DictReader(io.open(r"D:/股票数据/市场数据/%s/zt_pool.csv"%d,encoding="utf-8-sig"))}
    res=[]
    for c in codes:
        r=zt.get(c)
        if not r: res.append(dict(代码=c,备注="不在当日zt_pool")); continue
        k=lb(int(float(r['连板数'])))+'|'+fb(str(r['首次封板时间']).zfill(6)[:4].rjust(4,'0')[:2]+':'+str(r['首次封板时间']).zfill(6)[2:4])+'|'+th(float(r['换手率']))
        cell=cells.get(k,{})
        res.append(dict(代码=c,名称=r['名称'],连板=int(float(r['连板数'])),首封=str(r['首次封板时间']).zfill(6),
                        换手=round(float(r['换手率']),2),cell=k,cell_n=cell.get('n'),cell_gate=cell.get('gate'),
                        cell_执1均收=cell.get('e1'),cell_执1胜率=cell.get('w1')))
    return res
out={}
out['A_cells']=row('20261102',['002827','600261','001230','002275','600259'])
out['B_cells']=row('20261103',['600261','002652','603906','002292'])
# 一字 vs 非一字 gate
yz=G[G['首封']<='09:25']; ny=G[G['首封']>='14:00']
out['一字族gate']=dict(n=len(yz),gate=round(float(((yz['GAP']>-3)&(yz['GAP']<=1.5)).mean()*100),1),med=round(float(yz['GAP'].median()),2))
out['尾盘族gate']=dict(n=len(ny),gate=round(float(((ny['GAP']>-3)&(ny['GAP']<=1.5)).mean()*100),1),med=round(float(ny['GAP'].median()),2))
out['首封桶gate']={k:dict(n=len(x),gate=round(float(((x['GAP']>-3)&(x['GAP']<=1.5)).mean()*100),1),med=round(float(x['GAP'].median()),2)) for k,x in G.groupby(G['首封'].map(fb))}
json.dump(out,open(r"D:/股票数据/市场数据/_学习/_tmp_limitup_20261104_exec.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
