# -*- coding: utf-8 -*-
import csv,os,json,statistics as st
T=json.load(open('_学习/_市场温度表.json',encoding='utf-8'))
days=sorted(T)
def g(d,f): return T.get(d,{}).get(f)
def prev(d):
    i=days.index(d); return days[i-1] if i>0 else None
def nxt(d):
    i=days.index(d); return days[i+1] if i+1<len(days) else None
# 形态：最高板==6 且 梯队无4无5
def shape(d):
    t=T[d]
    lad=t.get('梯队') or {}
    return t.get('最高板')==6 and not lad.get('4') and not lad.get('5')
rows=[(d,nxt(d)) for d in days[:-1] if shape(d)]
print("形态『6板最高且4/5板空档』n=",len(rows))
print(" 样本:",[a for a,_ in rows])
for f in ['涨停数','温度','最高板','二板加','封板率','炸板率','跌停数','封板总额亿']:
    vals=[g(e,f) for _,e in rows if g(e,f) is not None]
    if vals: print(f"  次日{f}: 中位={st.median(vals):.4g} min={min(vals):.4g} max={max(vals):.4g} | {sorted(vals)}")
print("  今日形态: 最高6, 梯队",T['20261023']['梯队'])
# 一进二率条件
S=json.load(open('_学习/_情绪先行指标.json',encoding='utf-8'))
td=sorted(d for d in S if S[d].get('晋级',{}).get('一进二率') is not None)
for lo,hi in [(0.35,1.0),(0.30,1.0),(0.30,0.40)]:
    nx=[S[td[i+1]]['晋级']['一进二率'] for i in range(len(td)-1) if lo<=S[td[i]]['晋级']['一进二率']<=hi]
    if nx: print(f"今日一进二∈[{lo},{hi}) 次日一进二: 均={st.mean(nx):.3f} 中位={st.median(nx):.3f} n={len(nx)} <=0.30者={sum(1 for v in nx if v<=0.30)}/{len(nx)} <=0.25者={sum(1 for v in nx if v<=0.25)}/{len(nx)}")
# 二进三 rate today 0.20 -> next
nx3=[S[td[i+1]]['晋级'].get('二进三率') for i in range(len(td)-1) if S[td[i]]['晋级'].get('一进二率',0)>=0.30]
print("一进二>=0.30 次日二进三>=0.20:",sum(1 for v in nx3 if v and v>=0.20),"/",len([v for v in nx3 if v is not None]))
