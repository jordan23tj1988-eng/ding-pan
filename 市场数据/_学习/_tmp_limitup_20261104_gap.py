# -*- coding: utf-8 -*-
import sys, json, time
sys.path.insert(0, r"D:/股票数据/市场数据")
import 涨停质量训练 as M
import pandas as pd, numpy as np

t0=time.time()
D=M._enrich(M._factor_table()).copy()
D['E1']=pd.to_numeric(D['E1'],errors='coerce')*100
D['E2']=pd.to_numeric(D['E2'],errors='coerce')*100
D['温度b']=pd.to_numeric(D['温度'],errors='coerce')
D['首封']=D['首封'].astype(str)
D['名称']=D['名称'].astype(str)

gaps=[]
for i,r in D.iterrows():
    b=M._bars(r['代码'])
    if b is None: gaps.append(np.nan); continue
    idx=b.index[b['date']==r['日']]
    if not len(idx): gaps.append(np.nan); continue
    i2=idx[0]
    if i2+1>=len(b): gaps.append(np.nan); continue
    tc=float(b.loc[i2,'close']); o1=float(b.loc[i2+1,'open'])
    gaps.append((o1/tc-1)*100 if (tc>0 and o1>0) else np.nan)
D['GAP']=gaps
D[['日','代码','名称','首封','连板','开板','换手','封单比','温度','E1','E2','GAP']].to_csv(r"D:/股票数据/市场数据/_学习/_tmp_limitup_gapcache_20261104.csv",index=False,encoding="utf-8-sig")
print("rows",len(D),"gap有效",int(D['GAP'].notna().sum()),"%.1fs"%(time.time()-t0))

out={}
TAG='羊阳扬洋佯'
D['tag']=D['名称'].str.contains('['+TAG+']')
def S(x,name):
    e1=x['E1'].dropna(); e2=x['E2'].dropna(); g=x['GAP'].dropna()
    out[name]=dict(n=int(len(x)),执1胜率=round(float((e1>0).mean()*100),1) if len(e1) else None,
      执1均收=round(float(e1.mean()),3) if len(e1) else None,执1n=int(len(e1)),
      执2胜率=round(float((e2>0).mean()*100),1) if len(e2) else None,
      执2均收=round(float(e2.mean()),3) if len(e2) else None,执2n=int(len(e2)),
      gapn=int(len(g)),gap中位=round(float(g.median()),2) if len(g) else None,
      gate_neg3_15=round(float(((g>-3)&(g<=1.5)).mean()*100),1) if len(g) else None,
      gate_neg3_3=round(float(((g>-3)&(g<=3)).mean()*100),1) if len(g) else None,
      gap_gt3=round(float((g>3).mean()*100),1) if len(g) else None,
      gap_le_neg3=round(float((g<=-3).mean()*100),1) if len(g) else None)
# 标签正交：全库
S(D,"全库"); S(D[~D['tag']],"全库_非谐音"); S(D[D['tag']],"全库_谐音")
S(D[D['温度b']<25],"冰点档"); S(D[(D['温度b']<25)&(~D['tag'])],"冰点档_非谐音"); S(D[(D['温度b']<25)&(D['tag'])],"冰点档_谐音")
cell=(D['温度b']<25)&(D['首封']>='14:00')&(D['连板']==1)&(D['换手']>=10)
S(D[cell],"格"); S(D[cell&~D['tag']],"格_剔谐音"); S(D[cell&D['tag']],"格_仅谐音")
# 逐桶
S(D[cell&(D['换手']>=20)],"格内换手≥20"); S(D[cell&(D['换手']>=10)&(D['换手']<20)],"格内换手10-20")
S(D[(D['首封']>='14:00')&(D['连板']==1)&(D['温度b']<25)],"上一层_冰点尾盘首板")
json.dump(out,open(r"D:/股票数据/市场数据/_学习/_tmp_limitup_20261104_tagorth.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
