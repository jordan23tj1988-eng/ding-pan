# -*- coding: utf-8 -*-
"""温度体检_20260718.py(临时,用完弃) 供0719温度钝化终判:
A) 冰点×跌停分位分层回测: 冰点日按跌停数因果滚动分位拆层,出次日全场涨停执行均收
B) 7分量250日相关矩阵(spearman) + 正负失衡量化
"""
import json, os
import numpy as np

L = "_学习"
T = json.load(open(os.path.join(L,"_市场温度表.json"),encoding="utf-8"))
P = json.load(open(os.path.join(L,"_全场涨停执行均收_回填.json"),encoding="utf-8"))
days = sorted(T)

# ---------- A 冰点分层 ----------
# 因果滚动分位: 跌停数在截至当日(含)历史窗口的分位
def roll_pct(seq):
    out=[]
    for i,v in enumerate(seq):
        if v is None: out.append(None); continue
        hist=[x for x in seq[:i+1] if x is not None][-250:]
        out.append(100.0*sum(1 for x in hist if x<=v)/len(hist))
    return out

dts=[T[d].get("跌停数") for d in days]
dtp=roll_pct(dts)
dtp_map=dict(zip(days,dtp))

rows=[]
for d in days:
    t=T[d].get("温度")
    if t is None or t>=25: continue
    y=P.get(d,{}).get("执行均收")   # 池d的T+1执行均收
    if y is None: continue
    rows.append((d,t,T[d].get("跌停数"),dtp_map[d],y))

def stat(sub):
    ys=[r[4] for r in sub]
    if not ys: return "n=0"
    return "n=%d 均收%+.2f%% 胜率%.0f%%" % (len(ys), float(np.mean(ys)), 100*sum(1 for y in ys if y>0)/len(ys))

hi=[r for r in rows if r[3]>=90]
mid=[r for r in rows if 50<=r[3]<90]
lo=[r for r in rows if r[3]<50]
print("== A 冰点(温度<25)分层×跌停数滚动分位 ==")
print("全部冰点日:", stat(rows))
print("崩盘冰点(跌停分位>=90):", stat(hi), "  日:", [r[0] for r in hi])
print("中间(50-90):", stat(mid))
print("安静冰点(<50):", stat(lo), "  日:", [r[0] for r in lo][:10])

# ---------- B 7分量相关矩阵 ----------
COMP=["涨停数","成交额亿","封板总额亿","最高板","二板加","跌停数","炸板率"]
M=[]
for c in COMP:
    M.append([T[d].get(c) for d in days])
def spearman(a,b):
    pairs=[(x,y) for x,y in zip(a,b) if x is not None and y is not None]
    if len(pairs)<30: return None
    xa=np.array([p[0] for p in pairs],float); ya=np.array([p[1] for p in pairs],float)
    rx=np.argsort(np.argsort(xa)); ry=np.argsort(np.argsort(ya))
    return float(np.corrcoef(rx,ry)[0,1])
print("\n== B 7分量spearman相关(n=%d日) =="%len(days))
print(" "*8+" ".join("%6s"%c[:3] for c in COMP))
for i,c in enumerate(COMP):
    line=[]
    for j in range(len(COMP)):
        r=spearman(M[i],M[j])
        line.append("%6.2f"%r if r is not None else "   na ")
    print("%-8s"%c[:4]+" ".join(line))
# 正向簇平均相关
pos_idx=[0,1,2,3,4]
rs=[spearman(M[i],M[j]) for i in pos_idx for j in pos_idx if i<j]
print("正向5分量两两平均相关: %.2f"%np.mean([r for r in rs if r is not None]))
# 有效独立度粗估: 等权下亏钱簇有效权重
print("(等权名义权重: 正5/7=71%% 负2/7=29%%; 正向共线越高,负向有效话语权越接近 2/(2+k), k=正向独立因子数)")

# ---------- C 置顶规则真正影响的人群: 跌停分位>=99 且 温度>=25 ----------
print("\n== C 跌停极值(分位>=99)日按温度档分层(次日全场涨停执行均收) ==")
ext=[d for d in days if dtp_map[d] is not None and dtp_map[d]>=99]
for lo_,hi_,tag in [(0,25,"冰点<25"),(25,45,"偏冷25-45"),(45,101,"中性及以上>=45")]:
    sub=[(d,P.get(d,{}).get("执行均收")) for d in ext if T[d].get("温度") is not None and lo_<=T[d]["温度"]<hi_]
    sub=[(d,y) for d,y in sub if y is not None]
    ys=[y for _,y in sub]
    if ys:
        print("%s: n=%d 均收%+.2f%% 胜率%.0f%%  日:%s"%(tag,len(ys),float(np.mean(ys)),100*sum(1 for y in ys if y>0)/len(ys),[d for d,_ in sub]))
    else:
        print("%s: n=0"%tag)
print("跌停极值日总数:",len(ext))
