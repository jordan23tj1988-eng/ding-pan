# -*- coding: utf-8 -*-
import json, statistics as st
T=json.load(open('_学习/_市场温度表.json',encoding='utf-8'))
days=sorted(T)
for v in T.values():
    v['封板率']=round(v['涨停数']/(v['涨停数']+v['炸板数']),4) if (v['涨停数']+v['炸板数']) else None
def g(d,f): return T.get(d,{}).get(f)
def prev(d):
    i=days.index(d); return days[i-1] if i>0 else None
def nxt(d):
    i=days.index(d); return days[i+1] if i+1<len(days) else None
V=[(d,nxt(d)) for d in days[:-1] if g(prev(d),'温度') is not None and g(prev(d),'温度')<25 and g(d,'温度') is not None and g(d,'温度')>=45]
print("V桶 n=",len(V),[a for a,_ in V])
def rate(f,op,th):
    vals=[g(e,f) for _,e in V if g(e,f) is not None]
    ok=sum(1 for v in vals if (v>=th if op=='ge' else v<=th))
    return f"{ok}/{len(vals)}={ok/len(vals)*100:.1f}%"
for f,op,th in [('温度','ge',40),('温度','ge',45),('涨停数','ge',50),('涨停数','ge',70),('成交额亿','ge',20000),('封板率','le',0.85),('封板率','ge',0.80),('二板加','ge',12),('二板加','ge',14),('跌停数','le',10),('最高板','ge',4),('最高板','ge',5),('炸板率','le',0.30)]:
    print(f"  {f} {op} {th}: {rate(f,op,th)}")
for f in ['涨停数','成交额亿','封板率','二板加','最高板','温度','跌停数']:
    vals=sorted(g(e,f) for _,e in V if g(e,f) is not None)
    print(' ',f,'p25=',vals[len(vals)//4],'中位=',st.median(vals))
print('今日分位:')
def pct(f,val,pool=None):
    xs=sorted(g(d,f) for d in days if g(d,f) is not None)
    return round(sum(1 for x in xs if x<val)/len(xs)*100,2)
for f in ['涨停数','封板率','二板加','成交额亿','温度','封板总额亿']:
    print(' ',f,T['20261023'][f],pct(f,T['20261023'][f]),'%')
