# -*- coding: utf-8 -*-
import os, json, importlib.util
import pandas as pd, numpy as np
BASE=r"D:\股票数据\市场数据"; L=os.path.join(BASE,"_学习")
spec=importlib.util.spec_from_file_location("zjzl", os.path.join(BASE,"涨停质量训练.py"))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
P=m._factor_table(); P=m._enrich(P,forward=True); P=P[P['E1'].notna()].copy()
P['温度']=pd.to_numeric(P['温度'],errors='coerce')
def st(g):
    if not len(g): return {"n":0}
    return dict(n=int(len(g)),胜率=round(float((g['E1']>0).mean()*100),1),执1=round(float(g['E1'].mean()*100),2),
                执2胜率=round(float((g['E2']>0).mean()*100),1) if g['E2'].notna().any() else None,
                执2=round(float(g['E2'].mean()*100),2) if g['E2'].notna().any() else None)
bands=[("<25",-1,25),("25-35",25,35),("35-40",35,40),("40-65",40,65),(">=65",65,999)]
out={}
print("总样本",len(P))
for lab,lo,hi in bands:
    g=P[(P['温度']>=lo)&(P['温度']<hi)]; out[lab]=st(g)
    print(lab,out[lab]," 首板",st(g[g['连板']<=1]))
# 冰点 未开板 / 开板桶
S=P[P['温度']<25]
print("\n冰点 未开板",st(S[S['开板']==0]),"开1",st(S[S['开板']==1]),"开2+",st(S[S['开板']>=2]))
print("冰点<3%合计 n=",len(S[S['换手']<3]))
print("全库",st(P))
# 25-40 封单<2% / >=2%
B=P[(P['温度']>=25)&(P['温度']<40)]
print("\n25-40 封单<2%",st(B[B['封单比']<2])," >=2%",st(B[B['封单比']>=2]))
d=json.load(open(os.path.join(L,"_limitup_MA01_20261016.json"),encoding="utf-8"))
d["结果"]["温度连续档"]=out
d["结果"]["冰点_开板桶"]={"未开板":st(S[S['开板']==0]),"开1次":st(S[S['开板']==1]),"开2次+":st(S[S['开板']>=2])}
d["结果"]["B25_40_封单桶"]={"<2%":st(B[B['封单比']<2]),">=2%":st(B[B['封单比']>=2])}
d["结果"]["全库"]=st(P)
json.dump(d,open(os.path.join(L,"_limitup_MA01_20261016.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("\nappended 温度连续档/冰点_开板桶/B25_40_封单桶/全库")
