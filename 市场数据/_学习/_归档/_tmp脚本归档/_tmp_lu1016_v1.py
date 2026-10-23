# -*- coding: utf-8 -*-
import os, json, csv
import pandas as pd, numpy as np
B=r"D:\股票数据\市场数据\_学习"; CD=os.path.join(B,"_bars_cache")
def bars(c):
    f=os.path.join(CD,c+".csv")
    if not os.path.isfile(f): return None
    b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-',''); return b
def e1(c,d):
    b=bars(c)
    if b is None: return None
    idx=b.index[b['date']==d]
    if not len(idx): return None
    i=idx[0]
    if i+1>=len(b): return None
    o=float(b.loc[i+1,'open']); cl=float(b.loc[i+1,'close']); tc=float(b.loc[i,'close'])
    return dict(T1开=round(o,2),T1收=round(cl,2),T1高开=round((o/tc-1)*100,2),执1=round((cl/o-1)*100,2))
q=json.load(open(os.path.join(B,"涨停质量荐票_20261015.json"),encoding="utf-8"))
rows=[]
for r in q["明细"]:
    x=e1(r["代码"],"20261015")
    if x is None: print("MISS",r["代码"],r["名称"]); continue
    rows.append((r["代码"],r["名称"],round(r["换手"],2),r["连板"],x["T1高开"],x["执1"],r["首封"]))
print("n=",len(rows))
e=[x[5] for x in rows]
print("池均执1 %.2f%% 胜率%d/%d=%.1f%% T1高开均%.2f%% 高开为正%d"%(np.mean(e),sum(1 for v in e if v>0),len(e),sum(1 for v in e if v>0)/len(e)*100,np.mean([x[4] for x in rows]),sum(1 for x in rows if x[4]>0)))
for lo,hi,lab in [(0,3,"<3"),(3,10,"3-10"),(10,20,"10-20"),(20,999,">=20")]:
    g=[x for x in rows if lo<=x[2]<hi]
    if g: print("换手%s n=%d 执1均%.2f%% 胜率%.1f%% | %s"%(lab,len(g),np.mean([y[5] for y in g]),sum(1 for y in g if y[5]>0)/len(g)*100,[(y[0],y[1],y[2],y[5]) for y in g]))
print("\n-- 首封<=09:31 明细")
for x in rows:
    if str(x[6])[:5]<="09:31":
        cap=0.30 if x[0].startswith("92") or x[0][0]=="8" else (0.20 if x[0][0]=="3" or x[0].startswith("688") else 0.10)
        print("  %s %s 首封%s 高开%+.2f%% 板幅%.0f%% 执1%+.2f%% %s"%(x[0],x[1],x[6],x[4],cap*100,x[5],"追不进" if x[4]>=cap*100-0.2 else "可成交"))
print("\n-- 002815 / 605003 / 000530")
for c in ["002815","605003","000530"]:
    print(" ",c,e1(c,"20261015"))
