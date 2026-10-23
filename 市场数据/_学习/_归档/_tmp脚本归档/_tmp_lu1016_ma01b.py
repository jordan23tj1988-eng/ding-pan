# -*- coding: utf-8 -*-
import os, sys, json, importlib.util
import pandas as pd, numpy as np
BASE=r"D:\股票数据\市场数据"; L=os.path.join(BASE,"_学习")
spec=importlib.util.spec_from_file_location("zjzl", os.path.join(BASE,"涨停质量训练.py"))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
P=m._factor_table(); P=m._enrich(P,forward=True)
P=P[P['E1'].notna()].copy()
P['温度']=pd.to_numeric(P['温度'],errors='coerce')
P['温档']=P['温度'].map(lambda t: None if pd.isna(t) else ("A_<25" if t<25 else ("B_25-40" if t<40 else ("C_40-65" if t<65 else "D_≥65"))))
def hb(x):
    if pd.isna(x): return None
    return "<3%" if x<3 else ("3-10%" if x<10 else ("10-20%" if x<20 else "≥20%"))
P['换手桶']=P['换手'].map(hb)
def st(g):
    if not len(g): return {"n":0}
    return dict(n=int(len(g)),胜率=round(float((g['E1']>0).mean()*100),1),执1均涨=round(float(g['E1'].mean()*100),2),
                执2胜率=round(float((g['E2']>0).mean()*100),1) if g['E2'].notna().any() else None,
                执2均涨=round(float(g['E2'].mean()*100),2) if g['E2'].notna().any() else None)
S=P[P['温档']=="B_25-40"]
print("=== 冷档 25-40 全样本 n=%d ==="%len(S), st(S))
print("\n-- 连板档")
for lab,f in [("首板",lambda s:s['连板']<=1),("2板",lambda s:s['连板']==2),("3板",lambda s:s['连板']==3),("4板+",lambda s:s['连板']>=4)]:
    g=S[f(S)]; print(" ",lab,st(g))
print("\n-- 开板档")
for lab,f in [("未开板",lambda s:s['开板']==0),("开1次",lambda s:s['开板']==1),("开2次+",lambda s:s['开板']>=2)]:
    g=S[f(S)]; print(" ",lab,st(g))
print("\n-- 换手≥20% × 开板")
H=S[S['换手桶']=="≥20%"]
for lab,f in [("未开板",lambda s:s['开板']==0),("开1次",lambda s:s['开板']==1),("开2次+",lambda s:s['开板']>=2)]:
    print("  换手≥20%×"+lab, st(H[f(H)]))
print("\n-- 换手≥20% × 连板")
for lab,f in [("首板",lambda s:s['连板']<=1),("2板",lambda s:s['连板']==2),("3板",lambda s:s['连板']==3),("4板+",lambda s:s['连板']>=4)]:
    print("  换手≥20%×"+lab, st(H[f(H)]))
print("\n-- 4板+ × 封单<2% × 冷档")
g=S[(S['连板']>=4)&(S['封单比']<2)]
print("  ",st(g))
print("-- 4板+ × 封单<2% × 冷档 × 换手≥20%")
print("  ",st(g[g['换手桶']=="≥20%"]))
print("-- 4板+ × 封单<2% × 冷档 × 换手10-20%")
print("  ",st(g[g['换手桶']=="10-20%"]))
print("\n-- 封单比<2% × 冷档")
print("  ",st(S[S['封单比']<2]))
print("-- 封单比≥2% × 冷档")
print("  ",st(S[S['封单比']>=2]))
print("\n-- 冷档 × 首封桶")
def fb(x):
    t=str(x)[:5]
    return "一字≤9:25" if t<="09:25" else ("秒板≤9:31" if t<="09:31" else ("早盘≤10:00" if t<="10:00" else ("盘中10-14" if t<="14:00" else "尾盘>14")))
P['首封桶']=P['首封'].map(fb); S=P[P['温档']=="B_25-40"]
for k in ["一字≤9:25","秒板≤9:31","早盘≤10:00","盘中10-14","尾盘>14"]:
    print("  ",k,st(S[S['首封桶']==k]))
print("\n-- 冷档 × 首封 × 换手≥10%")
for k in ["一字≤9:25","秒板≤9:31","早盘≤10:00","盘中10-14","尾盘>14"]:
    g=S[(S['首封桶']==k)&(S['换手']>=10)]; print("  ",k,st(g))
print("\n-- 温度连续临近档 25-35 / 35-40")
P['细档']=P['温度'].map(lambda t: None if pd.isna(t) else ("<25" if t<25 else ("25-35" if t<35 else ("35-40" if t<40 else ("40-65" if t<65 else "≥65")))))
for b in ["<25","25-35","35-40","40-65","≥65"]:
    s=P[P['细档']==b]; print("  ",b,st(s), " 首板",st(s[s['连板']<=1]))
