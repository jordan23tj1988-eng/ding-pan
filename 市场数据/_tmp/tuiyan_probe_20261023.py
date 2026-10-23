# -*- coding: utf-8 -*-
import json, statistics as st
T=json.load(open('_学习/_市场温度表.json',encoding='utf-8'))
days=sorted(T)
for k,v in T.items():
    v['封板率']=round(v['涨停数']/(v['涨停数']+v['炸板数']),4) if (v['涨停数']+v['炸板数']) else None
FIELDS=['涨停数','跌停数','炸板率','封板率','温度','最高板','二板加','成交额亿','封板总额亿']
def pct(field,val):
    xs=sorted(T[d][field] for d in days if T[d].get(field) is not None)
    n=len(xs); below=sum(1 for x in xs if x<val)
    return round(below/n*100,2), n
def nxt(d):
    i=days.index(d); return days[i+1] if i+1<len(days) else None
def summarize(name, sel):
    rows=[(d,nxt(d)) for d in days[:-1] if sel(d)]
    print(f"\n### {name}  n={len(rows)}")
    if not rows: return
    print("  样本日:", ", ".join(d for d,_ in rows))
    for f in FIELDS:
        vals=[T[e][f] for _,e in rows if T[e].get(f) is not None]
        if not vals: continue
        vals_s=sorted(vals)
        print(f"  {f}: 中位={st.median(vals):.4g} 均={st.mean(vals):.4g} 最小={min(vals):.4g} 最大={max(vals):.4g} 分布={vals_s}")
D='20261023'
print("== 今日读数分位 ==")
for f in FIELDS:
    print(f, T[D][f], "分位%", pct(f,T[D][f]))

# V型修复：前日温度<25 且 当日温度>=45
summarize("V型修复日(前日<25,当日>=45)", lambda d: T[d]['温度']<25 and T[nxt(d)]['温度']>=45)
# 同桶再限制当日温度<=60（今日53.2）
summarize("V型修复日且当日温度45~60", lambda d: T[d]['温度']<25 and 45<=T[nxt(d)]['温度']<=60)
summarize("温度中性45~65", lambda d: 45<=T[d]['温度']<=65)
summarize("涨停>=80", lambda d: T[d]['涨停数']>=80)
summarize("封板率>=0.85", lambda d: T[d]['封板率'] and T[d]['封板率']>=0.85)
summarize("封板率>=0.85且涨停>=70", lambda d: T[d]['封板率'] and T[d]['封板率']>=0.85 and T[d]['涨停数']>=70)
summarize("二板加>=12", lambda d: T[d]['二板加']>=12)
summarize("最高板==6", lambda d: T[d]['最高板']==6)
summarize("成交额>=19000", lambda d: T[d]['成交额亿']>=19000)
