# -*- coding: utf-8 -*-
"""MA-20261015-01 承接：换手率<3%否决的机械判据/适用边界 + 温度子档单调性检验（零网络、只用本地缓存）"""
import os, sys, json, importlib.util
import pandas as pd, numpy as np
BASE = r"D:\股票数据\市场数据"
L = os.path.join(BASE, "_学习")
sys.path.insert(0, BASE)
os.environ.pop("PYTHONPATH", None)
spec = importlib.util.spec_from_file_location("zjzl", os.path.join(BASE, "涨停质量训练.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

P = m._factor_table()
print("样本 n=", len(P), " 日数", P['日'].nunique(), flush=True)
P = m._enrich(P, forward=True)
P = P[P['E1'].notna()].copy()
print("有前向样本 n=", len(P), flush=True)

def st(g):
    return dict(n=int(len(g)),
                执1胜率=round(float((g['E1']>0).mean()*100),1),
                执1均涨=round(float(g['E1'].mean()*100),2),
                执2胜率=round(float((g['E2']>0).mean()*100),1) if g['E2'].notna().any() else None,
                执2均涨=round(float(g['E2'].mean()*100),2) if g['E2'].notna().any() else None)

P['温度'] = pd.to_numeric(P['温度'], errors='coerce')
def band(t):
    if pd.isna(t): return None
    if t<25: return "A_冰点<25"
    if t<40: return "B_25-40"
    if t<65: return "C_40-65"
    return "D_≥65"
P['温档']=P['温度'].map(band)
def hb(x):
    if x is None or pd.isna(x): return None
    if x<3: return "<3%"
    if x<10: return "3-10%"
    if x<20: return "10-20%"
    return "≥20%"
P['换手桶']=P['换手'].map(hb)
def fb(x):
    t=str(x)[:5]
    if t<="09:25": return "一字≤9:25"
    if t<="09:31": return "秒板≤9:31"
    if t<="10:00": return "早盘≤10:00"
    if t<="14:00": return "盘中10-14"
    return "尾盘>14"
P['首封桶']=P['首封'].map(fb)

out={}
print("\n=== 温度子档 × 换手桶 ===")
cross={}
for bk in ["A_冰点<25","B_25-40","C_40-65","D_≥65"]:
    sub=P[P['温档']==bk]
    row={}
    for h in ["<3%","3-10%","10-20%","≥20%"]:
        g=sub[sub['换手桶']==h]
        row[h]=st(g) if len(g) else {"n":0}
        print(bk,h,row[h])
    cross[bk]=row
    # 单调性: spearman 桶序 vs 执1均涨
    xs=[i for i,h in enumerate(["<3%","3-10%","10-20%","≥20%"]) if row[h].get("n",0)>=100]
    ys=[row[["<3%","3-10%","10-20%","≥20%"][i]]["执1均涨"] for i in xs]
    def _rho(a,b):
        if len(a)<3: return None
        ra=pd.Series(a).rank(); rb=pd.Series(b).rank()
        return round(float(ra.corr(rb)),3)
    rho=_rho(xs,ys)
    cross[bk]["_n_buckets≥100"]=len(xs); cross[bk]["_rho_桶序vs执1均涨"]=rho
    print("  -> 桶数(n>=100)=%d rho=%s"%(len(xs),rho))
out["温度子档x换手桶"]=cross

print("\n=== 冰点档 换手<3% × 首封结构（适用边界）===")
sub=P[(P['温档']=="A_冰点<25")&(P['换手桶']=="<3%")]
b1={}
for k in ["一字≤9:25","秒板≤9:31","早盘≤10:00","盘中10-14","尾盘>14"]:
    g=sub[sub['首封桶']==k]
    b1[k]=st(g) if len(g) else {"n":0}
    print(" <3%×",k,b1[k])
un=b1.get("一字≤9:25",{}).get("n",0)+b1.get("秒板≤9:31",{}).get("n",0)
print(f" <3% 内 不可成交结构(一字+秒板) n={un} 占比{(un/len(sub)*100 if len(sub) else 0):.1f}%")
out["冰点_换手<3%_x_首封"]=b1
out["冰点_换手<3%_总量"]=st(sub); out["冰点_换手<3%_不可成交n"]=un

print("\n=== 冰点档 换手<3% 再按是否可成交（可执行口径）===")
sub2=sub[~sub['首封桶'].isin(["一字≤9:25","秒板≤9:31"])]
out["冰点_换手<3%_可成交子集"]=st(sub2); print(" 可成交子集",out["冰点_换手<3%_可成交子集"])
sub3=sub[sub['首封桶'].isin(["一字≤9:25","秒板≤9:31"])]
out["冰点_换手<3%_不可成交子集"]=st(sub3); print(" 不可成交子集",out["冰点_换手<3%_不可成交子集"])

print("\n=== 冰点档 换手<3% × 开板 ===")
for k,lab in [(0,"未开板"),(1,"开1次")]:
    g=sub[sub['开板']==k]; out["冰点_<3%_"+lab]=st(g) if len(g) else {"n":0}; print(" ",lab,out["冰点_<3%_"+lab])
g=sub[sub['开板']>=2]; out["冰点_<3%_开2次+"]=st(g) if len(g) else {"n":0}; print("  开2次+",out["冰点_<3%_开2次+"])

print("\n=== 近30交易日子集（稳健性）===")
days=sorted(P['日'].unique())[-30:]
recent=P[P['日'].isin(days)]
for bk in ["A_冰点<25"]:
    s=recent[recent['温档']==bk]
    rr={}
    for h in ["<3%","3-10%","10-20%","≥20%"]:
        g=s[s['换手桶']==h]; rr[h]=st(g) if len(g) else {"n":0}; print(" recent",bk,h,rr[h])
    out["近30日_冰点x换手"]=rr
out["近30日_全档"]=st(recent)

json.dump({"口径":"执1=T+1开→T+1收;样本=_factor_table+_enrich同源(零网络,本地bars_cache);温度=_市场温度表.json T日值;换手=zt_pool换手率T日值",
           "结果":out}, open(os.path.join(L,"_limitup_MA01_20261016.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nwritten _limitup_MA01_20261016.json")
