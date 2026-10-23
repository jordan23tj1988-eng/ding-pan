# -*- coding: utf-8 -*-
import os, sys, json, importlib.util
import pandas as pd, numpy as np
BASE=r"D:\股票数据\市场数据"; L=os.path.join(BASE,"_学习")
spec=importlib.util.spec_from_file_location("zjzl", os.path.join(BASE,"涨停质量训练.py"))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
P=m._factor_table(); P=m._enrich(P,forward=True); P=P[P['E1'].notna()].copy()
P['温度']=pd.to_numeric(P['温度'],errors='coerce')
P=P[(P['温度']>=25)&(P['温度']<35)].copy()   # 温度29.1 → 25-35 连续档
print("25-35 档 n=",len(P), " 执1 %.2f%% 胜率%.1f%%"%(P['E1'].mean()*100,(P['E1']>0).mean()*100))
def hb(x): return "<3%" if x<3 else ("3-10%" if x<10 else ("10-20%" if x<20 else "≥20%"))
P['换手桶']=P['换手'].map(hb)
P['连板档']=P['连板'].map(lambda x: "首板" if x<=1 else ("2板" if x==2 else ("3板" if x==3 else "4板+")))
P['开板档']=P['开板'].map(lambda x:"未开板" if x==0 else ("开1次" if x==1 else "开2次+"))
P['封单档']=P['封单比'].map(lambda x:"<2%" if (x is not None and x==x and x<2) else "≥2%")
def st(g):
    if not len(g): return {"n":0}
    return dict(n=int(len(g)),胜率=round(float((g['E1']>0).mean()*100),1),执1=round(float(g['E1'].mean()*100),2),
                执2=round(float(g['E2'].mean()*100),2) if g['E2'].notna().any() else None)
cells={}
for (a,b,c) in [("首板","开2次+","10-20%"),("首板","开2次+","≥20%"),("首板","开2次+","3-10%"),
                ("首板","开1次","10-20%"),("首板","开1次","3-10%"),("首板","未开板","10-20%"),
                ("首板","未开板","3-10%"),("首板","开2次+","<3%"),("首板","开1次","<3%"),
                ("2板","开2次+","10-20%"),("2板","开2次+","≥20%"),("2板","开2次+","3-10%"),("2板","开1次","3-10%"),
                ("3板","开2次+","3-10%"),("3板","开1次","3-10%"),("3板","未开板","3-10%"),
                ("4板+","未开板","<3%"),("4板+","未开板","3-10%"),("4板+","开2次+","3-10%"),("4板+","开2次+","≥20%")]:
    g=P[(P['连板档']==a)&(P['开板档']==b)&(P['换手桶']==c)]
    cells[f"{a}×{b}×{c}"]=st(g)
json.dump(cells,open(os.path.join(L,"_limitup_桶_2535_20261016.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("\n=== 25-35 档 × 连板×开板×换手 单元格 ===")
for k,v in sorted(cells.items(), key=lambda x:-x[1].get("n",0)):
    print(" ",k,v)
# 封单档 × 连板
print("\n=== 25-35 档 连板 × 封单 ===")
for a in ["首板","2板","3板","4板+"]:
    for b in ["<2%","≥2%"]:
        print("  ",a,"×",b,st(P[(P['连板档']==a)&(P['封单档']==b)]))
# 今日 61 只落格
q=json.load(open(os.path.join(L,"涨停质量荐票_20261016.json"),encoding="utf-8"))
print("\n=== 今日 61 只 → 单元格归属 ===")
rows=[]
for r in q["明细"]:
    lb="首板" if r["连板"]<=1 else ("2板" if r["连板"]==2 else ("3板" if r["连板"]==3 else "4板+"))
    ob="未开板" if r["开板次数"]==0 else ("开1次" if r["开板次数"]==1 else "开2次+")
    hs=hb(r["换手"]); key=f"{lb}×{ob}×{hs}"
    c=cells.get(key,{"n":0})
    rows.append((c.get("n",0), c.get("执1"), r["代码"], r["名称"], lb, ob, round(r["换手"],2), r["封单比"], key))
rows.sort(key=lambda x:(-(x[0] or 0), -(x[1] or -9)))
for x in rows:
    print("  n=%-4s 执1=%-6s %s %s %s/%s 换手%.2f 封单比%s [%s]"%(x[0],x[1],x[2],x[3],x[4],x[5],x[6],x[7],x[8]))
