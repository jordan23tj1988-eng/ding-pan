# -*- coding: utf-8 -*-
import json, statistics as st
T=json.load(open('_学习/_市场温度表.json',encoding='utf-8'))
days=sorted(T)
for v in T.values():
    v['封板率']=round(v['涨停数']/(v['涨停数']+v['炸板数']),4) if (v['涨停数']+v['炸板数']) else None
FIELDS=['涨停数','跌停数','炸板率','封板率','温度','最高板','二板加','成交额亿','封板总额亿']
def g(d,f):
    return T.get(d,{}).get(f) if d else None
def idx(d): return days.index(d)
def prev(d): 
    i=idx(d); return days[i-1] if i>0 else None
def nxt(d):
    i=idx(d); return days[i+1] if i+1<len(days) else None
def summarize(name, sel):
    rows=[]
    for d in days[:-1]:
        if sel(d):
            rows.append((d,nxt(d)))
    print(f"\n### {name}  n={len(rows)}")
    if not rows: return
    print("  样本日(当日→次日):", ", ".join(f"{a}→{b}" for a,b in rows))
    for f in FIELDS:
        vals=[g(e,f) for _,e in rows if g(e,f) is not None]
        if not vals: 
            print(f"  {f}: 缺"); continue
        vs=sorted(vals)
        print(f"  {f}: 中位={st.median(vals):.4g} 均={st.mean(vals):.4g} min={min(vals):.4g} max={max(vals):.4g} | {vs}")
    return rows

summarize("A. V型修复日(前日温度<25 且 当日>=45)", lambda d: g(prev(d),'温度') is not None and g(prev(d),'温度')<25 and g(d,'温度') is not None and g(d,'温度')>=45)
summarize("A2. 同上且当日温度45~60", lambda d: g(prev(d),'温度') is not None and g(prev(d),'温度')<25 and g(d,'温度') is not None and 45<=g(d,'温度')<=60)
summarize("A3. 前日<25 且 当日温度>=45 且 涨停>=60", lambda d: g(prev(d),'温度') is not None and g(prev(d),'温度')<25 and g(d,'温度') is not None and g(d,'温度')>=45 and g(d,'涨停数')>=60)
summarize("B. 温度中性45~65", lambda d: g(d,'温度') is not None and 45<=g(d,'温度')<=65)
summarize("C. 涨停>=80", lambda d: g(d,'涨停数') is not None and g(d,'涨停数')>=80)
summarize("D. 封板率>=0.85", lambda d: g(d,'封板率') is not None and g(d,'封板率')>=0.85)
summarize("E. 二板加>=12", lambda d: g(d,'二板加') is not None and g(d,'二板加')>=12)
summarize("F. 最高板==6", lambda d: g(d,'最高板')==6)
summarize("G. 成交额>=19000", lambda d: g(d,'成交额亿') is not None and g(d,'成交额亿')>=19000)
summarize("H. 炸板率<=0.15 且 涨停>=70", lambda d: g(d,'炸板率') is not None and g(d,'炸板率')<=0.15 and g(d,'涨停数')>=70)
print("\n== 近12日 ==")
for d in days[-12:]:
    v=T[d]
    print(d, {k:v.get(k) for k in ['涨停数','跌停数','炸板率','封板率','温度','最高板','二板加','成交额亿','封板总额亿','梯队']})
