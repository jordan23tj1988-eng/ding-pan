# -*- coding: utf-8 -*-
import sys, json, time
sys.path.insert(0, r"D:/股票数据/市场数据")
import 涨停质量训练 as M
import pandas as pd

t0=time.time()
D=M._enrich(M._factor_table()).copy()
D['E1']=pd.to_numeric(D['E1'],errors='coerce')*100
D['E2']=pd.to_numeric(D['E2'],errors='coerce')*100
D['温度b']=pd.to_numeric(D['温度'],errors='coerce')
D['首封']=D['首封'].astype(str)
out={}

TAG="羊阳扬洋佯"
def gap_of(code, d):
    b=M._bars(code)
    if b is None: return None
    idx=b.index[b['date']==d]
    if not len(idx): return None
    i=idx[0]
    if i+1>=len(b): return None
    tc=float(b.loc[i,'close']); o1=float(b.loc[i+1,'open'])
    if tc<=0 or o1<=0: return None
    return (o1/tc-1)*100

def stat(x, name, with_gap=True, minn=0):
    e1=x['E1'].dropna(); e2=x['E2'].dropna()
    d=dict(n=int(len(x)), 执1n=int(len(e1)), 执2n=int(len(e2)),
           执1胜率=round(float((e1>0).mean()*100),1) if len(e1) else None,
           执1均收=round(float(e1.mean()),3) if len(e1) else None,
           执2胜率=round(float((e2>0).mean()*100),1) if len(e2) else None,
           执2均收=round(float(e2.mean()),3) if len(e2) else None)
    if with_gap:
        g=[]
        for _,r in x.iterrows():
            v=gap_of(r['代码'], r['日'])
            if v is not None: g.append(v)
        s=pd.Series(g) if g else pd.Series(dtype=float)
        d['gapn']=int(len(s))
        if len(s):
            d['gap中位']=round(float(s.median()),2); d['gap均值']=round(float(s.mean()),2)
            d['gap_le-3']=round(float((s<=-3).mean()*100),1)
            d['gap_m3_0']=round(float(((s>-3)&(s<=0)).mean()*100),1)
            d['gap_0_15']=round(float(((s>0)&(s<=1.5)).mean()*100),1)
            d['gap_15_3']=round(float(((s>1.5)&(s<=3)).mean()*100),1)
            d['gap_gt3']=round(float((s>3).mean()*100),1)
            d['gate[-3,1.5]触发率']=round(float(((s>-3)&(s<=1.5)).mean()*100),1)
            d['gate[-3,3]触发率']=round(float(((s>-3)&(s<=3)).mean()*100),1)
    out[name]=d
    return d

cellmask=(D['温度b']<25)&(D['首封']>='14:00')&(D['连板']==1)&(D['换手']>=10)
C=D[cellmask].copy()
C['tag']=C['名称'].astype(str).str.contains('['+TAG+']')
print("CELL n=", len(C), "窗口", D['日'].min(), D['日'].max(), "总样本", len(D))
e1=C['E1'].dropna(); e2=C['E2'].dropna()
print("ALL 执1 %.1f%% %+.2f%% n=%d | 执2 %.1f%% %+.2f%% n=%d" % ((e1>0).mean()*100, e1.mean(), len(e1), (e2>0).mean()*100, e2.mean(), len(e2)))
stat(C,"格_冰点×尾盘首板×换手≥10")
sub=C[~C['tag']]; e1s=sub['E1'].dropna(); e2s=sub['E2'].dropna()
print("NO-TAG n=%d 执1 %.1f%% %+.2f%% | 执2 %.1f%% %+.2f%%" % (len(sub),(e1s>0).mean()*100,e1s.mean(),(e2s>0).mean()*100,e2s.mean()))
print("TAG名单:", [(r['日'],r['代码'],r['名称'],round(r['E1'],2) if r['E1']==r['E1'] else None, round(r['E2'],2) if r['E2']==r['E2'] else None) for _,r in C[C['tag']].iterrows()])
stat(sub,"格_正交检验_剔谐音")
stat(C[C['tag']],"格_仅谐音")
# 宽松谐音: 催化也含 -> 用名称已够; 另给"全窗同名族"
print("elapsed %.1fs"%(time.time()-t0))
json.dump(out, open(r"D:/股票数据/市场数据/_学习/_tmp_limitup_20261104_cell.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
